// SPDX-License-Identifier: AGPL-3.0-only

import {
    readFileSync,
    writeFileSync,
    existsSync,
    mkdirSync,
    readdirSync,
    copyFileSync,
    rmSync,
    mkdtempSync,
} from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";

const root = fileURLToPath(new URL("../", import.meta.url));
for (const required of [
    "package.json",
    "pnpm-workspace.yaml",
    "apps/web/package.json",
    "apps/desktop/package.json",
]) {
    if (!existsSync(join(root, required))) {
        throw new Error(
            `Invalid repository root: ${root}\n` +
            `Missing: ${required}\n` +
            "Place this script at <repository>/lemon/build.mjs, " +
            "inside the complete Element-derived checkout."
        );
    }
}
const desktop = join(root, "apps/desktop");
const project = JSON.parse(
    readFileSync(join(root, "lemon/project.json"), "utf8"),
);

const stage = process.argv[2];
const arch = process.argv[3] || process.arch;
const platform = {
    linux: "linux",
    darwin: "macos",
    win32: "windows",
}[process.platform];

function assert(condition, message) {
    if (!condition) throw new Error(message);
}

assert(
    /^[A-Za-z0-9][A-Za-z0-9-]*\/[A-Za-z0-9_.-]+$/.test(
        project.repository,
    ),
    "Set a real owner/repository in lemon/project.json.",
);
assert(
    /^\d+\.\d+\.\d+$/.test(project.version),
    "This release pipeline expects a numeric x.y.z version.",
);

if (process.env.GITHUB_REPOSITORY) {
    assert(
        process.env.GITHUB_REPOSITORY.toLowerCase() ===
            project.repository.toLowerCase(),
        "Repository metadata does not match GITHUB_REPOSITORY.",
    );
}

if (process.env.GITHUB_REF_TYPE === "tag") {
    assert(
        process.env.GITHUB_REF_NAME === `v${project.version}`,
        "Git tag must match lemon/project.json.",
    );
}

const env = {
    ...process.env,
    NX_DAEMON: "false",
    NX_NO_CLOUD: "true",
    VERSION: project.version,
};

// electron-builder treats an empty CSC_LINK differently from an absent one.
for (const key of [
    "CSC_LINK",
    "CSC_KEY_PASSWORD",
    "APPLE_ID",
    "APPLE_APP_SPECIFIC_PASSWORD",
    "APPLE_TEAM_ID",
]) {
    if (!env[key]) delete env[key];
}

if (!env.CSC_LINK) {
    env.CSC_IDENTITY_AUTO_DISCOVERY = "false";
}

function run(command, args, cwd = root) {
    const result = spawnSync(command, args, {
        cwd,
        env,
        stdio: "inherit",
        shell: process.platform === "win32",
    });

    if (result.error) throw result.error;
    assert(
        result.status === 0,
        `${command} failed with status ${result.status}`,
    );
}

function writeJson(path, value) {
    writeFileSync(path, JSON.stringify(value, null, 2) + "\n");
}

const generated = join(root, "lemon/generated");
mkdirSync(generated, { recursive: true });

const owner = project.repository.split("/")[0].toLowerCase();
const variantPath = join(generated, "variant.json");

writeJson(variantPath, {
    name: "lemon",
    productName: "Lemon",
    description: "A refreshing, open-source Matrix chat client",
    appId: `io.github.${owner}.lemon`,
    protocols: ["lemon"],
});

env.VARIANT_PATH = variantPath;

run(
    process.platform === "win32" ? "python" : "python3",
    ["lemon/assets.py"],
);

if (stage === "web") {
    run("pnpm", ["--filter", "element-web", "build"]);

    const webapp = join(root, "apps/web/webapp");
    assert(existsSync(join(webapp, "index.html")), "Missing web build.");

    const config = JSON.parse(
        readFileSync(join(root, "lemon/config.json"), "utf8"),
    );

    const repository = `https://github.com/${project.repository}`;
    config.help_url = `${repository}/issues`;
    config.update_base_url = "";
    config.branding.logo_link_url = repository;
    config.branding.auth_footer_links = [
        { text: "Lemon source", url: repository },
        { text: "Report an issue", url: `${repository}/issues` },
    ];

    writeJson(join(webapp, "config.json"), config);

    for (const name of ["lemon-logo.svg", "lemon-breeze.svg"]) {
        copyFileSync(join(generated, name), join(webapp, name));
    }

    const indexPath = join(webapp, "index.html");
    const html = readFileSync(indexPath, "utf8");
    writeFileSync(
        indexPath,
        html.replace(/<title>[\s\S]*?<\/title>/i, "<title>Lemon</title>"),
    );

    run(
        "pnpm",
        ["exec", "asar", "pack", "../web/webapp", "webapp.asar"],
        desktop,
    );
} else if (stage === "desktop") {
    assert(platform, "Unsupported operating system.");
    assert(["x64", "arm64"].includes(arch), "Unsupported architecture.");
    assert(
        process.arch === arch,
        `Native runner required: Node is ${process.arch}, target is ${arch}.`,
    );
    assert(
        existsSync(join(desktop, "webapp.asar")),
        "Build/download webapp.asar first.",
    );

    run("pnpm", ["exec", "nx", "run", "element-desktop:build:ts"]);
    run("pnpm", ["exec", "nx", "run", "element-desktop:build:res"]);

    run(
        "pnpm",
        [
            "exec",
            "electron-builder",
            "--config",
            "lemon-builder.ts",
            "--publish",
            "never",
            `--${arch}`,
        ],
        desktop,
    );

    const dist = join(desktop, "dist");
    let resources;
    let executable;

    if (process.platform === "darwin") {
        const candidates =
            arch === "arm64" ? ["mac-arm64", "mac"] : ["mac", "mac-x64"];

        const folder = candidates
            .map((name) => join(dist, name, "Lemon.app", "Contents"))
            .find((path) => existsSync(join(path, "MacOS", "Lemon")));

        assert(folder, "Packaged macOS app not found.");
        resources = join(folder, "Resources");
        executable = join(folder, "MacOS", "Lemon");
    } else {
        const prefix = process.platform === "win32" ? "win" : "linux";
        const folder = join(
            dist,
            arch === "arm64"
                ? `${prefix}-arm64-unpacked`
                : `${prefix}-unpacked`,
        );

        resources = join(folder, "resources");
        executable = join(
            folder,
            process.platform === "win32" ? "Lemon.exe" : "lemon",
        );
    }

    assert(existsSync(executable), "Packaged executable not found.");

    const require = createRequire(join(desktop, "package.json"));
    const asar = await import(
        pathToFileURL(require.resolve("@electron/asar")).href
    );

    const packageJson = JSON.parse(
        asar.extractFile(join(resources, "app.asar"), "package.json")
            .toString(),
    );
    const config = JSON.parse(
        asar.extractFile(join(resources, "webapp.asar"), "config.json")
            .toString(),
    );

    assert(packageJson.name === "lemon", "Wrong packaged application name.");
    assert(packageJson.productName === "Lemon", "Wrong product name.");
    assert(packageJson.version === project.version, "Wrong version.");
    assert(packageJson.electron_protocol === "lemon", "Wrong URI protocol.");
    assert(config.brand === "Lemon", "Wrong embedded branding.");
    assert(!config.update_base_url, "Unexpected auto-update endpoint.");
    assert(
        config.default_theme === "custom-Lemon Summer Breeze",
        "Wrong default theme.",
    );

    const binary = readFileSync(executable);
    let machine;
    let expected;

    if (process.platform === "linux") {
        machine = binary.readUInt16LE(18);
        expected = arch === "x64" ? 62 : 183;
    } else if (process.platform === "win32") {
        const peOffset = binary.readUInt32LE(0x3c);
        machine = binary.readUInt16LE(peOffset + 4);
        expected = arch === "x64" ? 0x8664 : 0xaa64;
    } else {
        machine = binary.readUInt32LE(4);
        expected = arch === "x64" ? 0x01000007 : 0x0100000c;
    }

    assert(machine === expected, "Executable architecture mismatch.");

    const profile = mkdtempSync(join(tmpdir(), "lemon-smoke-"));

    try {
        const args = ["--help", "--profile-dir", profile, "--no-update"];
        const command =
            process.platform === "linux" ? "xvfb-run" : executable;
        const commandArgs =
            process.platform === "linux"
                ? ["-a", executable, ...args]
                : args;

        const result = spawnSync(command, commandArgs, {
            env,
            stdio: "inherit",
            timeout: 60000,
        });

        if (result.error) throw result.error;
        assert(result.status === 0, "Packaged native smoke test failed.");
    } finally {
        rmSync(profile, { recursive: true, force: true });
    }

    const out = join(root, "lemon-out");
    rmSync(out, { recursive: true, force: true });
    mkdirSync(out);

    const suffixes = {
        linux: [".deb", ".rpm", ".AppImage", ".tar.gz"],
        macos: [".dmg", ".zip"],
        windows: [".exe", ".zip"],
    }[platform];

    // electron-builder uses distribution-specific architecture names
    // in some Linux artifact filenames.
    const linuxArtifactArch = {
        x64: {
            ".deb": "amd64",
            ".rpm": "x86_64",
            ".AppImage": "x86_64",
            ".tar.gz": "x64",
        },
        arm64: {
            ".deb": "arm64",
            ".rpm": "aarch64",
            ".AppImage": "arm64",
            ".tar.gz": "arm64",
        },
    };

    for (const suffix of suffixes) {
        const nativeArch =
            platform === "linux"
                ? linuxArtifactArch[arch][suffix]
                : arch;

        // Keep published filenames consistent with release.py and
        // the generated Arch, Gentoo, and Nix packaging recipes.
        const publishedName =
            `Lemon-${project.version}-${platform}-${arch}${suffix}`;

        const nativeName =
            `Lemon-${project.version}-${platform}-${nativeArch}${suffix}`;

        const candidates = [...new Set([nativeName, publishedName])];
        const sourceName = candidates.find((name) =>
            existsSync(join(dist, name)),
        );

        assert(
            sourceName,
            `Expected release artifact missing. Tried: ${candidates.join(", ")}`,
        );

        copyFileSync(
            join(dist, sourceName),
            join(out, publishedName),
        );
    }
} else {
    throw new Error("Usage: node lemon/build.mjs web|desktop [x64|arm64]");
}

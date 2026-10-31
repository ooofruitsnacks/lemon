// SPDX-License-Identifier: AGPL-3.0-only

import fs from "node:fs";
import { fileURLToPath } from "node:url";

import upstream from "./electron-builder.ts";

const project = JSON.parse(
    fs.readFileSync(
        fileURLToPath(new URL("../../lemon/project.json", import.meta.url)),
        "utf8",
    ),
);

const repository = `https://github.com/${project.repository}`;
const platform = {
    darwin: "macos",
    win32: "windows",
    linux: "linux",
}[process.platform];

if (!platform) {
    throw new Error(`Unsupported platform: ${process.platform}`);
}

const signedMac =
    process.platform === "darwin" && Boolean(process.env.CSC_LINK);

if (
    signedMac &&
    ![
        process.env.APPLE_ID,
        process.env.APPLE_APP_SPECIFIC_PASSWORD,
        process.env.APPLE_TEAM_ID,
    ].every(Boolean)
) {
    throw new Error("Signed macOS releases require notarization credentials.");
}

export default {
    ...upstream,

    productName: "Lemon",
    artifactName:
        `Lemon-${project.version}-${platform}-\${arch}.\${ext}`,

    publish: null,

    extraMetadata: {
        ...upstream.extraMetadata,
        version: project.version,
        author: "Lemon contributors",
        homepage: repository,
        repository: {
            type: "git",
            url: `${repository}.git`,
        },
        license: "AGPL-3.0-only",
    },

    extraResources: [
        "build/icon.png",
        "build/icon.ico",
        "build/icon.icns",
        "webapp.asar",
        {
            from: "../..",
            to: "licenses",
            filter: [
                "LICENSE*",
                "COPYING*",
                "NOTICE*",
                "UPSTREAM-README.md",
            ],
        },
    ],

    linux: {
        ...upstream.linux,
        executableName: "lemon",
        icon: "build/icon.png",
        target: ["deb", "rpm", "AppImage", "tar.gz"],
    },

    deb: {
        ...upstream.deb,
        maintainer: "Lemon contributors",
        recommends: [],
        depends: [
            "libc6 (>= 2.35)",
            "libgtk-3-0 | libgtk-3-0t64",
            "libnotify4",
            "libnss3",
            "libxss1",
            "libxtst6",
            "libatspi2.0-0 | libatspi2.0-0t64",
            "libuuid1",
            "libsecret-1-0",
            "libasound2 | libasound2t64",
            "libgbm1",
            "libdrm2",
            "libxkbcommon0",
            "xdg-utils",
            "ca-certificates",
        ],
    },

    rpm: {
        vendor: "Lemon contributors",
        depends: [
            "gtk3",
            "nss",
            "alsa-lib",
            "libXScrnSaver",
            "libXtst",
            "libnotify",
            "libsecret",
            "mesa-libgbm",
            "libdrm",
            "libxkbcommon",
            "xdg-utils",
        ],
    },

    mac: {
        ...upstream.mac,
        target: ["dmg", "zip"],
        icon: "build/icon.icns",
        identity: signedMac ? undefined : "-",
        notarize: signedMac,
        gatekeeperAssess: signedMac,
        extendInfo: {
            NSCameraUsageDescription:
                "Lemon uses your camera when you choose to join a video call.",
            NSMicrophoneUsageDescription:
                "Lemon uses your microphone for calls and voice messages.",
        },
    },

    dmg: {
        ...upstream.dmg,
        badgeIcon: "build/icon.icns",
        backgroundColor: "#FFF8D7",
    },

    win: {
        ...upstream.win,
        target: ["nsis", "zip"],
        icon: "build/icon.ico",
    },

    nsis: {
        oneClick: false,
        perMachine: false,
        allowToChangeInstallationDirectory: true,
        createDesktopShortcut: true,
        createStartMenuShortcut: true,
    },
};

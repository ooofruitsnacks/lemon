# Welcome to Lemon 🍋 

Lemon is a free open-source Element derived Matrix chat client. Focused on privacy and open communication because everyone deserves a community without corporate oversight. 

<img width="6226" height="3891" alt="lemonbckgrnd_fotoRC" src="https://github.com/user-attachments/assets/22ca5ce2-815f-4b25-92e5-2da0ed441be2" />

## Platforms Supported 

- IOS: IOS 17.6 or later
- macOS: x64 and ARM64
- Windows: x64 and ARM64
- Linux distros (AARCH64) that support glibc 2.35+ with plans for raspberry pi soon

## Development

Use the Node version in apps/desktop/.node-version and the package-manager
version recorded in the root package.json.

    pnpm install --frozen-lockfile
    node lemon/build.mjs web
    node lemon/build.mjs desktop

Build artifacts are collected in ```lemon-out/```

## Customization

The default configuration and bundled themes are in ```lemon/config.json```

The application also supports a user configuration file:

    lemon --config /absolute/path/to/config.json

Use a separate profile for another account:

    lemon --profile Work

> [!WARNING]
> Do not share a live profile directory between running application instances.

## Releases

Update ```lemon/project.json``` commit the change and push a matching vX.Y.Z tag after all checks have passed.

## Attribution and licensing

Lemon is derived from Element Web/Desktop.

Upstream source, history, copyright notices, license texts, and
UPSTREAM-README.md are retained. Lemon-specific additions are licensed
under AGPL-3.0-only.

Lemon is not an official Element or Matrix.org release.

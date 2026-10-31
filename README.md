# 🍋 Lemon

Lemon is an open-source, Element-derived Matrix desktop client with a
Lemon Summer Breeze default theme.

## Platforms

- macOS: x64 and ARM64
- Windows: x64 and ARM64
- Linux with glibc 2.35+: x64 and ARM64

Release outputs include DMG, ZIP, NSIS, DEB, RPM, AppImage, tar archives,
Arch packages, a Nix package expression, and a Gentoo binary overlay.

## Development

Use the Node version in apps/desktop/.node-version and the package-manager
version recorded in the root package.json.

    pnpm install --frozen-lockfile
    node lemon/build.mjs web
    node lemon/build.mjs desktop

Build artifacts are collected in lemon-out/.

## Customization

The default configuration and bundled themes are in lemon/config.json.

The application also supports a user configuration file:

    lemon --config /absolute/path/to/config.json

Use a separate profile for another account:

    lemon --profile Work

Do not share a live profile directory between running application instances.

## Releases

Update lemon/project.json, commit the change, and push a matching vX.Y.Z tag.

GitHub Actions creates a draft release. Build success and the included
smoke checks do not constitute complete Matrix feature validation.

Automatic updating is disabled until a Lemon-specific signed update
service is implemented.

## Attribution and licensing

Lemon is derived from Element Web/Desktop.

Upstream source, history, copyright notices, license texts, and
UPSTREAM-README.md are retained. Lemon-specific additions are licensed
under AGPL-3.0-only.

Lemon is not an official Element or Matrix.org release.

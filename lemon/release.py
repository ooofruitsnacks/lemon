# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import sys
import tarfile
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "release").resolve()
PROJECT = json.loads((ROOT / "lemon/project.json").read_text())
VERSION = PROJECT["version"]
REPO = PROJECT["repository"]
BASE = f"https://github.com/{REPO}/releases/download/v{VERSION}"
SVG = runpy.run_path(str(ROOT / "lemon/assets.py"))["SVG"]

OUT.mkdir(parents=True, exist_ok=True)


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def artifact(arch, extension):
    path = OUT / f"Lemon-{VERSION}-linux-{arch}.{extension}"
    if not path.is_file():
        raise SystemExit(f"Required artifact is missing: {path}")
    return path


values = {
    "VERSION": VERSION,
    "REPO": REPO,
    "BASE": BASE,
    "SVG": SVG,
    "TAR_X64": digest(artifact("x64", "tar.gz")),
    "TAR_ARM64": digest(artifact("arm64", "tar.gz")),
    "APPIMAGE_X64": digest(artifact("x64", "AppImage")),
    "APPIMAGE_ARM64": digest(artifact("arm64", "AppImage")),
}


def expand(template):
    result = textwrap.dedent(template).lstrip()
    for key, value in values.items():
        result = result.replace(f"@{key}@", value)
    return result


(OUT / "PKGBUILD").write_text(expand(r'''
pkgname=lemon-bin
pkgver=@VERSION@
pkgrel=1
pkgdesc="Lemon: a themed, Element-derived Matrix client"
arch=('x86_64' 'aarch64')
url="https://github.com/@REPO@"
license=('AGPL-3.0-only')
depends=(
  'glibc>=2.35' 'gtk3' 'nss' 'alsa-lib' 'libxss' 'libxtst'
  'libnotify' 'libsecret' 'libdrm' 'mesa' 'libxkbcommon' 'xdg-utils'
)
provides=('lemon')
conflicts=('lemon')
options=('!strip' '!debug')

source_x86_64=("@BASE@/Lemon-${pkgver}-linux-x64.tar.gz")
sha256sums_x86_64=('@TAR_X64@')
source_aarch64=("@BASE@/Lemon-${pkgver}-linux-arm64.tar.gz")
sha256sums_aarch64=('@TAR_ARM64@')

package() {
  local executable root
  executable="$(find "$srcdir" -type f -name lemon -print -quit)"
  test -n "$executable" || return 1
  root="${executable%/*}"

  install -d "$pkgdir/opt/lemon" "$pkgdir/usr/bin"
  cp -a "$root/." "$pkgdir/opt/lemon/"
  ln -s /opt/lemon/lemon "$pkgdir/usr/bin/lemon"

  if test -f "$pkgdir/opt/lemon/chrome-sandbox"; then
    chmod 4755 "$pkgdir/opt/lemon/chrome-sandbox"
  fi

  install -Dm644 "$root/resources/build/icon.png" \
    "$pkgdir/usr/share/icons/hicolor/512x512/apps/lemon.png"

  install -d "$pkgdir/usr/share/applications"
  printf '%s\n' \
    '[Desktop Entry]' \
    'Type=Application' \
    'Name=Lemon' \
    'Comment=Matrix chat with a summer breeze' \
    'Exec=lemon %U' \
    'Icon=lemon' \
    'Terminal=false' \
    'Categories=Network;InstantMessaging;' \
    'MimeType=x-scheme-handler/lemon;' \
    'StartupWMClass=lemon' \
    > "$pkgdir/usr/share/applications/lemon.desktop"
}
'''), encoding="utf-8")

(OUT / "lemon.nix").write_text(expand(r'''
{ pkgs ? import <nixpkgs> {} }:

let
  version = "@VERSION@";
  variants = {
    x86_64-linux = {
      arch = "x64";
      sha256 = "@APPIMAGE_X64@";
    };
    aarch64-linux = {
      arch = "arm64";
      sha256 = "@APPIMAGE_ARM64@";
    };
  };

  variant = variants.${pkgs.stdenv.hostPlatform.system}
    or (throw "Lemon supports x86_64-linux and aarch64-linux");

  src = pkgs.fetchurl {
    url = "@BASE@/Lemon-${version}-linux-${variant.arch}.AppImage";
    inherit (variant) sha256;
  };

  desktop = pkgs.makeDesktopItem {
    name = "lemon";
    desktopName = "Lemon";
    exec = "lemon %U";
    icon = "lemon";
    categories = [ "Network" "InstantMessaging" ];
    mimeTypes = [ "x-scheme-handler/lemon" ];
  };

  icon = builtins.toFile "lemon.svg" ''
@SVG@
  '';

in pkgs.appimageTools.wrapType2 {
  pname = "lemon";
  inherit version src;

  extraPkgs = p: [ p.libsecret p.nss ];

  extraInstallCommands = ''
    mkdir -p "$out/share/applications"
    cp ${desktop}/share/applications/* "$out/share/applications/"
    install -Dm644 ${icon} \
      "$out/share/icons/hicolor/scalable/apps/lemon.svg"
  '';

  meta = {
    description = "Lemon, an Element-derived Matrix desktop client";
    homepage = "https://github.com/@REPO@";
    license = pkgs.lib.licenses.agpl3Only;
    platforms = [ "x86_64-linux" "aarch64-linux" ];
    mainProgram = "lemon";
  };
}
'''), encoding="utf-8")

ebuild = expand(r'''
EAPI=8

inherit desktop xdg

DESCRIPTION="Lemon: an Element-derived Matrix desktop client"
HOMEPAGE="https://github.com/@REPO@"
SRC_URI="
  amd64? ( @BASE@/Lemon-@VERSION@-linux-x64.tar.gz )
  arm64? ( @BASE@/Lemon-@VERSION@-linux-arm64.tar.gz )
"

S="${WORKDIR}"
LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~arm64"
RESTRICT="strip"
QA_PREBUILT="*"

RDEPEND="
  >=sys-libs/glibc-2.35
  dev-libs/nss
  dev-libs/nspr
  dev-libs/expat
  app-accessibility/at-spi2-core
  app-crypt/libsecret
  media-libs/alsa-lib
  media-libs/mesa
  x11-libs/gtk+:3
  x11-libs/libX11
  x11-libs/libXcomposite
  x11-libs/libXdamage
  x11-libs/libXfixes
  x11-libs/libXrandr
  x11-libs/libXScrnSaver
  x11-libs/libXtst
  x11-libs/libxcb
  x11-libs/libxkbcommon
  x11-misc/xdg-utils
"

src_install() {
  local executable root
  executable="$(find "${WORKDIR}" -type f -name lemon -print -quit)"
  [[ -n "${executable}" ]] || die "Lemon executable not found"
  root="${executable%/*}"

  insinto /opt/lemon
  doins -r "${root}/."

  fperms 0755 /opt/lemon/lemon

  if [[ -f "${root}/chrome_crashpad_handler" ]]; then
    fperms 0755 /opt/lemon/chrome_crashpad_handler
  fi
  if [[ -f "${root}/chrome-sandbox" ]]; then
    fperms 4755 /opt/lemon/chrome-sandbox
  fi

  dosym ../../opt/lemon/lemon /usr/bin/lemon
  newicon -s 512 "${root}/resources/build/icon.png" lemon.png

  make_desktop_entry \
    "lemon %U" "Lemon" "lemon" "Network;InstantMessaging;"
}
''')

with tempfile.TemporaryDirectory() as temporary:
    overlay = Path(temporary) / "lemon-overlay"
    package = overlay / "net-im/lemon-bin"
    package.mkdir(parents=True)
    (overlay / "metadata").mkdir()
    (overlay / "profiles").mkdir()

    (overlay / "metadata/layout.conf").write_text(
        "masters = gentoo\nrepo-name = lemon\n"
        "thin-manifests = true\n",
        encoding="utf-8",
    )
    (overlay / "profiles/repo_name").write_text("lemon\n")
    (package / f"lemon-bin-{VERSION}.ebuild").write_text(
        ebuild, encoding="utf-8"
    )

    manifest = []
    for arch in ("x64", "arm64"):
        path = artifact(arch, "tar.gz")
        manifest.append(
            f"DIST {path.name} {path.stat().st_size} "
            f"BLAKE2B {digest(path, 'blake2b')} "
            f"SHA512 {digest(path, 'sha512')}"
        )

    (package / "Manifest").write_text("\n".join(manifest) + "\n")

    with tarfile.open(
        OUT / f"lemon-gentoo-overlay-{VERSION}.tar.gz", "w:gz"
    ) as archive:
        archive.add(overlay, arcname="lemon-overlay")

subprocess.run([
    "git", "archive",
    "--format=tar.gz",
    f"--prefix=lemon-{VERSION}/",
    "-o", str(OUT / f"lemon-source-{VERSION}.tar.gz"),
    "HEAD",
], cwd=ROOT, check=True)

print("Generated Arch, NixOS, Gentoo, and source-release artifacts.")

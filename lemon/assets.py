# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]

SVG = (ROOT / "lemon/branding/lemon-logo.svg").read_text(
    encoding="utf-8"
)

BREEZE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000">
<defs>
<linearGradient id="b" x2="1" y2="1">
<stop stop-color="#fff6be"/>
<stop offset="1" stop-color="#dff1e5"/>
</linearGradient>
</defs>
<rect width="1600" height="1000" fill="url(#b)"/>
<circle cx="1280" cy="170" r="180" fill="#fffce6" opacity=".75"/>
<path d="M0 740 Q400 560 850 780 T1600 700 V1000 H0Z"
 fill="#dcebbd" opacity=".65"/>
<path d="M0 860 Q500 690 1100 850 T1600 820 V1000 H0Z"
 fill="#cfe7d8" opacity=".65"/>
</svg>
"""


def chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def png(size):
    return (ROOT / f"lemon/branding/icons/{size}.png").read_bytes()


def main():
    generated = ROOT / "lemon/generated"
    build = ROOT / "apps/desktop/build"
    generated.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)

    (generated / "lemon-logo.svg").write_text(SVG, encoding="utf-8")
    (generated / "lemon-breeze.svg").write_text(BREEZE, encoding="utf-8")

    sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    images = {size: png(size) for size in sizes}
    (build / "icon.png").write_bytes(images[512])

    ico_sizes = sizes[:6]
    offset = 6 + 16 * len(ico_sizes)
    entries, payload = bytearray(), bytearray()

    for size in ico_sizes:
        image = images[size]
        dimension = size if size < 256 else 0
        entries.extend(struct.pack(
            "<BBBBHHII",
            dimension, dimension, 0, 0, 1, 32, len(image), offset
        ))
        payload.extend(image)
        offset += len(image)

    (build / "icon.ico").write_bytes(
        struct.pack("<HHH", 0, 1, len(ico_sizes)) + entries + payload
    )

    icns = bytearray()
    for kind, size in [
        (b"ic07", 128), (b"ic08", 256),
        (b"ic09", 512), (b"ic10", 1024)
    ]:
        image = images[size]
        icns.extend(kind + struct.pack(">I", len(image) + 8) + image)

    (build / "icon.icns").write_bytes(
        b"icns" + struct.pack(">I", len(icns) + 8) + icns
    )


if __name__ == "__main__":
    main()

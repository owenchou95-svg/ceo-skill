#!/usr/bin/env python3
"""Render the README showcase GIF without third-party dependencies."""

from __future__ import annotations

import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "assets" / "showcase.gif"


def write_gif(path: Path) -> None:
    width, height = 640, 360
    palette = [
        (18, 18, 18),
        (80, 250, 123),
        (248, 248, 242),
        (139, 233, 253),
        (241, 250, 140),
        (255, 85, 85),
        (98, 114, 164),
        (40, 42, 54),
    ]
    palette += [(0, 0, 0)] * (256 - len(palette))
    pixels = bytearray([0] * (width * height))

    def rect(x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(width, x1), min(height, y1)
        for y in range(y0, y1):
            row = y * width
            pixels[row + x0 : row + x1] = bytes([color]) * (x1 - x0)

    rect(24, 24, width - 24, height - 24, 7)
    rect(24, 24, width - 24, 56, 6)
    rect(44, 36, 56, 48, 5)
    rect(64, 36, 76, 48, 4)
    rect(84, 36, 96, 48, 1)

    lines = [
        (52, 84, 450, 1),
        (52, 124, 250, 3),
        (52, 152, 520, 2),
        (52, 196, 300, 4),
        (84, 224, 420, 2),
        (84, 248, 190, 2),
        (84, 272, 260, 1),
        (52, 312, 500, 3),
    ]
    for x, y, length, color in lines:
        rect(x, y, x + length, y + 10, color)
        for gap in range(x + 58, x + length, 96):
            rect(gap, y, min(gap + 8, x + length), y + 10, 7)

    min_code_size = 8
    clear = 1 << min_code_size
    end = clear + 1
    code_size = min_code_size + 1
    codes = [clear] + list(pixels) + [end]
    bitstream = bytearray()
    bitbuf = 0
    bitcount = 0
    for code in codes:
        bitbuf |= code << bitcount
        bitcount += code_size
        while bitcount >= 8:
            bitstream.append(bitbuf & 0xFF)
            bitbuf >>= 8
            bitcount -= 8
    if bitcount:
        bitstream.append(bitbuf & 0xFF)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        file.write(b"GIF89a")
        file.write(struct.pack("<HH", width, height))
        file.write(bytes([0xF7, 0x00, 0x00]))
        for red, green, blue in palette:
            file.write(bytes([red, green, blue]))
        file.write(b"!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00")
        file.write(b",")
        file.write(struct.pack("<HHHH", 0, 0, width, height))
        file.write(b"\x00")
        file.write(bytes([min_code_size]))
        for index in range(0, len(bitstream), 255):
            chunk = bitstream[index : index + 255]
            file.write(bytes([len(chunk)]))
            file.write(chunk)
        file.write(b"\x00;")


def main() -> int:
    write_gif(DEFAULT_OUTPUT)
    print(f"Rendered {DEFAULT_OUTPUT.relative_to(ROOT)} ({DEFAULT_OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

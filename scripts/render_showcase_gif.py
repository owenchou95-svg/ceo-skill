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

    # Three route cards: Task, Goal gap, Risk boundary.
    rect(52, 78, 318, 88, 2)
    rect(52, 94, 430, 104, 3)
    cards = [
        (52, 132, 188, 290, 1),
        (252, 132, 388, 290, 4),
        (452, 132, 588, 290, 5),
    ]
    for x0, y0, x1, y1, accent in cards:
        rect(x0, y0, x1, y1, 0)
        rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, 7)
        rect(x0 + 3, y0 + 3, x1 - 3, y0 + 18, accent)
        rect(x0 + 18, y0 + 38, x1 - 18, y0 + 48, 2)
        rect(x0 + 18, y0 + 68, x1 - 32, y0 + 78, 3)
        rect(x0 + 18, y0 + 96, x1 - 46, y0 + 106, accent)
        rect(x0 + 18, y0 + 124, x1 - 24, y0 + 134, 2)
        for gap in range(x0 + 76, x1 - 24, 42):
            rect(gap, y0 + 124, min(gap + 6, x1 - 24), y0 + 134, 7)

    rect(52, 314, 588, 324, 3)
    rect(52, 334, 460, 344, 2)

    min_code_size = 8
    clear = 1 << min_code_size
    end = clear + 1
    code_size = min_code_size + 1
    codes = []
    emitted_since_clear = 0
    for pixel in pixels:
        if emitted_since_clear == 0 or emitted_since_clear >= 200:
            codes.append(clear)
            emitted_since_clear = 0
        codes.append(pixel)
        emitted_since_clear += 1
    codes.append(end)
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

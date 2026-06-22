from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "app_icon.ico"
SIZES = (16, 24, 32, 48, 64, 128, 256)


Color = tuple[int, int, int, int]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images = [png_bytes(size) for size in SIZES]
    OUT.write_bytes(ico_bytes(images))
    print(f"Generated {OUT}")


def ico_bytes(images: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + len(images) * 16
    entries = []
    payload = []
    for size, data in images:
        entries.append(
            struct.pack(
                "<BBBBHHII",
                0 if size >= 256 else size,
                0 if size >= 256 else size,
                0,
                0,
                1,
                32,
                len(data),
                offset,
            )
        )
        payload.append(data)
        offset += len(data)
    return header + b"".join(entries) + b"".join(payload)


def png_bytes(size: int) -> tuple[int, bytes]:
    pixels = render_icon(size)
    raw = b"".join(b"\x00" + bytes(row) for row in pixels)
    return size, png_chunked(
        b"\x89PNG\r\n\x1a\n",
        [
            (b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)),
            (b"IDAT", zlib.compress(raw, level=9)),
            (b"IEND", b""),
        ],
    )


def png_chunked(signature: bytes, chunks: list[tuple[bytes, bytes]]) -> bytes:
    out = bytearray(signature)
    for kind, data in chunks:
        out.extend(struct.pack(">I", len(data)))
        out.extend(kind)
        out.extend(data)
        out.extend(struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))
    return bytes(out)


def render_icon(size: int) -> list[bytearray]:
    scale = 4
    canvas = size * scale
    hi = [[(0, 0, 0, 0) for _ in range(canvas)] for _ in range(canvas)]

    for y in range(canvas):
        for x in range(canvas):
            px = (x + 0.5) / scale
            py = (y + 0.5) / scale
            color = (0, 0, 0, 0)
            if rounded_rect(px, py, size * 0.07, size * 0.07, size * 0.86, size * 0.86, size * 0.18):
                color = (30, 35, 41, 255)
            if rounded_rect_stroke(
                px,
                py,
                size * 0.07,
                size * 0.07,
                size * 0.86,
                size * 0.86,
                size * 0.18,
                max(1.0, size * 0.035),
            ):
                color = (43, 49, 57, 255)
            if music_note(px, py, size):
                color = (11, 14, 17, 255)
            if waveform(px, py, size):
                color = (252, 213, 53, 255)
            hi[y][x] = color

    rows: list[bytearray] = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            block = [
                hi[y * scale + dy][x * scale + dx]
                for dy in range(scale)
                for dx in range(scale)
            ]
            row.extend(average(block))
        rows.append(row)
    return rows


def rounded_rect(x: float, y: float, left: float, top: float, width: float, height: float, radius: float) -> bool:
    right = left + width
    bottom = top + height
    if x < left or x > right or y < top or y > bottom:
        return False
    cx = min(max(x, left + radius), right - radius)
    cy = min(max(y, top + radius), bottom - radius)
    return math.hypot(x - cx, y - cy) <= radius


def rounded_rect_stroke(
    x: float,
    y: float,
    left: float,
    top: float,
    width: float,
    height: float,
    radius: float,
    stroke: float,
) -> bool:
    outer = rounded_rect(x, y, left, top, width, height, radius)
    inner = rounded_rect(
        x,
        y,
        left + stroke,
        top + stroke,
        width - stroke * 2,
        height - stroke * 2,
        max(0.0, radius - stroke),
    )
    return outer and not inner


def music_note(x: float, y: float, size: int) -> bool:
    stem_x = size * 0.48
    stem_y = size * 0.24
    stem_w = size * 0.08
    stem_h = size * 0.38
    head_cx = size * 0.38
    head_cy = size * 0.66
    head_rx = size * 0.16
    head_ry = size * 0.10
    flag = (
        size * 0.48 <= x <= size * 0.73
        and size * 0.20 <= y <= size * 0.33
        and y >= -0.35 * (x - size * 0.48) + size * 0.32
    )
    stem = stem_x <= x <= stem_x + stem_w and stem_y <= y <= stem_y + stem_h
    head = ((x - head_cx) / head_rx) ** 2 + ((y - head_cy) / head_ry) ** 2 <= 1.0
    return stem or head or flag


def waveform(x: float, y: float, size: int) -> bool:
    points = [
        (0.46, 0.61),
        (0.56, 0.61),
        (0.61, 0.48),
        (0.68, 0.76),
        (0.76, 0.54),
        (0.82, 0.61),
        (0.92, 0.61),
    ]
    scaled = [(px * size, py * size) for px, py in points]
    width = max(2.0, size * 0.065)
    return any(distance_to_segment(x, y, a, b) <= width / 2 for a, b in zip(scaled, scaled[1:]))


def distance_to_segment(x: float, y: float, a: tuple[float, float], b: tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(x - ax, y - ay)
    t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / length_sq))
    px = ax + t * dx
    py = ay + t * dy
    return math.hypot(x - px, y - py)


def average(colors: list[Color]) -> Color:
    return tuple(round(sum(color[i] for color in colors) / len(colors)) for i in range(4))  # type: ignore[return-value]


if __name__ == "__main__":
    main()

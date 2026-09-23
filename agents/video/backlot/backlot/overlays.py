"""Text overlays rendered with Pillow (titles, burned captions). Works without ffmpeg's drawtext/libass."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONTS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


@dataclass
class Cue:
    start: float
    end: float
    text: str


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONTS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        cur = ""
        for word in words:
            trial = f"{cur} {word}".strip()
            if draw.textlength(trial, font=fnt) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines or [""]


def render_text_png(text: str, width: int, height: int, dest: Path, *, style: str = "lower-third", scale: float = 1.0) -> tuple[Path, int, int]:
    """Render text into a transparent PNG sized to the frame. Returns (path, x, y) for overlay."""
    size = int((height * (0.045 if style == "caption" else 0.05 if style == "lower-third" else 0.08)) * scale)
    fnt = font(max(size, 12))
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = int(width * 0.06)
    lines = _wrap(draw, text, fnt, width - 2 * margin)
    line_h = int(size * 1.25)
    block_h = line_h * len(lines)
    pad = int(size * 0.45)
    widths = [draw.textlength(l, font=fnt) for l in lines]
    block_w = int(max(widths)) if widths else 0
    if style == "center":
        x0 = (width - block_w) // 2
        y0 = (height - block_h) // 2
        box = (x0 - pad, y0 - pad, x0 + block_w + pad, y0 + block_h + pad)
        draw.rounded_rectangle(box, radius=pad // 2, fill=(0, 0, 0, 140))
        for i, line in enumerate(lines):
            lx = (width - widths[i]) / 2
            draw.text((lx, y0 + i * line_h), line, font=fnt, fill=(255, 255, 255, 255))
    elif style == "caption":
        y0 = height - block_h - int(height * 0.08)
        for i, line in enumerate(lines):
            lx = (width - widths[i]) / 2
            ly = y0 + i * line_h
            draw.rounded_rectangle((lx - pad, ly - pad // 3, lx + widths[i] + pad, ly + line_h), radius=6, fill=(0, 0, 0, 160))
            draw.text((lx, ly), line, font=fnt, fill=(255, 255, 255, 255))
    else:
        x0 = margin
        y0 = height - block_h - int(height * 0.12)
        draw.rectangle((x0 - pad, y0 - pad, x0 + block_w + pad, y0 + block_h + pad), fill=(0, 0, 0, 150))
        draw.rectangle((x0 - pad, y0 - pad, x0 - pad + max(4, size // 8), y0 + block_h + pad), fill=(76, 155, 232, 255))
        for i, line in enumerate(lines):
            draw.text((x0, y0 + i * line_h), line, font=fnt, fill=(255, 255, 255, 255))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "PNG")
    return dest, 0, 0


_TS = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)")


def _ts(value: str) -> float:
    m = _TS.match(value.strip())
    if not m:
        raise ValueError(f"bad timestamp {value!r}")
    h, mi, s, ms = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000


def parse_srt(text: str) -> list[Cue]:
    cues: list[Cue] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        idx = 1 if "-->" in lines[1] else 0
        if "-->" not in lines[idx]:
            continue
        start, end = [p.strip() for p in lines[idx].split("-->")[:2]]
        body = "\n".join(lines[idx + 1 :])
        cues.append(Cue(_ts(start), _ts(end.split()[0]), body))
    return cues


def fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues: list[Cue], dest: Path) -> Path:
    lines = []
    for i, cue in enumerate(cues, 1):
        lines += [str(i), f"{fmt_ts(cue.start)} --> {fmt_ts(cue.end)}", cue.text, ""]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest

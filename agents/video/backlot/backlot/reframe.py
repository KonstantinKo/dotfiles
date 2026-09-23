"""Reframe a take or render to another aspect ratio with a crop focus."""

from __future__ import annotations

from pathlib import Path

from backlot import ffmpeg
from backlot.errors import BacklotError
from backlot.project import Project
from backlot.takes import resolve_media
from backlot.thumbs import media_kind

_CANON = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350), "4:3": (1440, 1080), "3:4": (1080, 1440)}


def parse_aspect(text: str) -> tuple[int, int]:
    try:
        a, b = text.replace("x", ":").split(":")
        return int(a), int(b)
    except ValueError as exc:
        raise BacklotError(f"bad aspect {text!r}; use e.g. 9:16") from exc


def crop_box(w: int, h: int, aspect: tuple[int, int], focus: str) -> tuple[int, int, int, int]:
    target = aspect[0] / aspect[1]
    if w / h > target:
        cw, ch = int(round(h * target)) & ~1, h
        x = {"left": 0, "right": w - cw}.get(focus, (w - cw) // 2)
        return cw, ch, x, 0
    cw, ch = w, int(round(w / target)) & ~1
    y = {"top": 0, "bottom": h - ch}.get(focus, (h - ch) // 2)
    return cw, ch, 0, y


def reframe(project: Project, ref: str, to: str, focus: str = "center", output: Path | None = None) -> Path:
    src = resolve_media(project, ref)
    kind = media_kind(src)
    if kind not in ("image", "video"):
        raise BacklotError(f"{ref} is not an image or video")
    aspect = parse_aspect(to)
    w, h = ffmpeg.dimensions(src)
    cw, ch, x, y = crop_box(w, h, aspect, focus if focus != "auto" else "center")
    tw, th = _CANON.get(f"{aspect[0]}:{aspect[1]}", (cw, ch))
    tag = f"{aspect[0]}x{aspect[1]}"
    output = output or project.renders_dir / f"{src.parent.name if src.parent.name and src.stem == 'out' else src.stem}-{tag}{src.suffix}"
    if not output.is_absolute():
        output = project.root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    ffm = ffmpeg.which("ffmpeg")
    if not ffm:
        raise BacklotError("ffmpeg not found")
    vf = f"crop={cw}:{ch}:{x}:{y},scale={tw}:{th},setsar=1"
    cmd = [ffm, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vf", vf]
    if kind == "video":
        cmd += ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart"]
    else:
        cmd += ["-frames:v", "1"]
    cmd.append(str(output))
    ffmpeg.run(cmd)
    return output

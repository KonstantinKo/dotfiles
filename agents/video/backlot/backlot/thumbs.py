"""Thumbnails for the vault, always JPEG (`_thumbs/<id>.jpg`): image, first video frame or audio waveform."""

from __future__ import annotations

import subprocess
from pathlib import Path

from backlot.errors import BacklotError

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"}
AUDIO_EXT = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".opus"}
SIZE = 256


def media_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    return "other"


def make_thumb(src: Path, thumbs_dir: Path, take_id: str) -> Path | None:
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    kind = media_kind(src)
    if kind == "image":
        return _image_thumb(src, thumbs_dir / f"{take_id}.jpg")
    if kind == "video":
        return _video_thumb(src, thumbs_dir / f"{take_id}.jpg")
    if kind == "audio":
        return _audio_thumb(src, thumbs_dir / f"{take_id}.jpg")
    return None


def _image_thumb(src: Path, dest: Path) -> Path:
    from PIL import Image

    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((SIZE, SIZE))
        im.save(dest, "JPEG", quality=82)
    return dest


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise BacklotError(f"ffmpeg failed: {proc.stderr.strip().splitlines()[-1] if proc.stderr else proc.returncode}")


def _video_thumb(src: Path, dest: Path) -> Path:
    _run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-frames:v", "1",
        "-vf", f"scale={SIZE}:-2", "-q:v", "4", str(dest),
    ])
    return dest


def _audio_thumb(src: Path, dest: Path) -> Path:
    _run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
        "-filter_complex", f"color=c=#1e2530:s={SIZE}x64[bg];[0:a]showwavespic=s={SIZE}x64:colors=#4c9be8[w];[bg][w]overlay=format=auto,format=yuvj420p",
        "-frames:v", "1", "-q:v", "4", str(dest),
    ])
    return dest

"""Thin ffmpeg/ffprobe helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from backlot.errors import BacklotError


def which(name: str) -> str | None:
    return shutil.which(name) or (f"/opt/homebrew/bin/{name}" if Path(f"/opt/homebrew/bin/{name}").exists() else None)


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-6:])
        raise BacklotError(f"{Path(cmd[0]).name} failed:\n{tail}")


def probe(path: Path) -> dict:
    ffprobe = which("ffprobe")
    if not ffprobe:
        raise BacklotError("ffprobe not found")
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise BacklotError(f"ffprobe failed on {path}: {proc.stderr.strip()[-200:]}")
    return json.loads(proc.stdout or "{}")


def duration(path: Path) -> float:
    info = probe(path)
    fmt = info.get("format") or {}
    try:
        return float(fmt.get("duration"))
    except (TypeError, ValueError):
        for s in info.get("streams") or []:
            if s.get("duration"):
                return float(s["duration"])
    return 0.0


def dimensions(path: Path) -> tuple[int, int]:
    for s in probe(path).get("streams") or []:
        if s.get("codec_type") == "video" and s.get("width"):
            return int(s["width"]), int(s["height"])
    raise BacklotError(f"no video stream in {path}")


def has_filter(name: str) -> bool:
    ffmpeg = which("ffmpeg")
    if not ffmpeg:
        return False
    proc = subprocess.run([ffmpeg, "-hide_banner", "-filters"], capture_output=True, text=True, check=False)
    return any(line.split()[1:2] == [name] for line in proc.stdout.splitlines() if line.strip())

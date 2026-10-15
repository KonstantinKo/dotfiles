"""`backlot doctor`: environment and configuration checks."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from backlot import ffmpeg
from backlot.config import Studio, load_studio, studio_path
from backlot.errors import BacklotError
from backlot.models import load_models


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    warn: bool = False


def run_checks() -> list[Check]:
    checks: list[Check] = []
    for tool in ("uv", "ffmpeg", "ffprobe"):
        found = shutil.which(tool) or (ffmpeg.which(tool) if tool != "uv" else None)
        checks.append(Check(tool, bool(found), found or "not found"))
    for tool in ("kokoro", "edge-tts"):
        from backlot.providers.local import find_cli

        found = find_cli(tool)
        checks.append(Check(tool, bool(found), found or "not found (local tts unavailable)", warn=True))
    path = studio_path()
    try:
        studio = load_studio(path)
        checks.append(Check("studio.yaml", True, str(path)))
    except BacklotError as exc:
        checks.append(Check("studio.yaml", False, str(exc)))
        return checks
    checks.append(Check("vault", studio.vault.is_dir(), str(studio.vault)))
    checks.append(Check("projects_root", studio.projects_root.is_dir(), str(studio.projects_root), warn=True))
    from backlot.scaffold import CLAUDE_SETTINGS, validate_hook_settings

    try:
        validate_hook_settings(CLAUDE_SETTINGS)
        checks.append(Check("spend hook source", True, str(CLAUDE_SETTINGS)))
    except BacklotError as exc:
        checks.append(Check("spend hook source", False, str(exc)))
    for parent in (Path.cwd(), *Path.cwd().parents):
        if (parent / "project.yaml").is_file():
            settings = parent / ".claude" / "settings.json"
            try:
                validate_hook_settings(settings)
                checks.append(Check("project spend hook", True, str(settings)))
            except BacklotError as exc:
                checks.append(Check("project spend hook", False, str(exc)))
            break
    checks += _provider_checks(studio)
    models, problems = load_models(studio.vault)
    checks.append(Check("model notes", not problems, f"{len(models)} ok" + (f", {len(problems)} broken: " + "; ".join(f"{p.name}: {m}" for p, m in problems) if problems else "")))
    return checks


def _provider_checks(studio: Studio) -> list[Check]:
    from backlot.providers.comfyui_local import ComfyUILocalProvider
    from backlot.providers.fal import has_key

    out: list[Check] = []
    fal_cfg = studio.provider_config("fal")
    out.append(Check("fal key", has_key(fal_cfg), "present (env or Keychain)" if has_key(fal_cfg) else "missing: env FAL_KEY or Keychain fal-api/FAL_KEY"))
    comfy = ComfyUILocalProvider(studio.provider_config("comfyui-local"))
    out.append(Check("comfyui-local", comfy.reachable(), comfy.url if comfy.reachable() else f"unreachable at {comfy.url}", warn=True))
    return out

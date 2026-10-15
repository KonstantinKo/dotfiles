"""studio.yaml: vault path, projects root, currency and provider settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from backlot.errors import BacklotError
from backlot.frontmatter import load_yaml

DEFAULT_STUDIO = Path("~/projects/video/backlot/studio.yaml")


@dataclass
class Studio:
    path: Path
    vault: Path
    projects_root: Path
    currency: str = "EUR"
    providers: dict[str, dict[str, Any]] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)

    def provider_config(self, name: str) -> dict[str, Any]:
        return dict(self.providers.get(name) or {})


def studio_path() -> Path:
    default = Path(os.environ.get("DOTFILES_PROJECTS_ROOT", "~/projects")) / "video/backlot/studio.yaml"
    return Path(os.environ.get("BACKLOT_STUDIO") or default).expanduser()


def _machine_path(value: str) -> Path:
    root = os.environ.get("DOTFILES_PROJECTS_ROOT")
    if root and value.startswith("~/projects/"):
        return Path(root).expanduser() / value[len("~/projects/"):]
    return Path(value).expanduser()


def load_studio(path: Path | None = None) -> Studio:
    path = (path or studio_path()).expanduser()
    if not path.exists():
        raise BacklotError(f"studio config not found: {path} (set BACKLOT_STUDIO or create it)")
    try:
        raw = load_yaml(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise BacklotError(f"studio config is not valid YAML: {exc}") from exc
    for key in ("vault", "projects_root"):
        if not raw.get(key):
            raise BacklotError(f"studio config missing '{key}': {path}")
    return Studio(
        path=path,
        vault=_machine_path(str(raw["vault"])),
        projects_root=_machine_path(str(raw["projects_root"])),
        currency=str(raw.get("currency", "EUR")),
        providers=dict(raw.get("providers") or {}),
        defaults=dict(raw.get("defaults") or {}),
    )

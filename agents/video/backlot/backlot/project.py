"""Project dir (project.yaml) resolution and paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from backlot.config import Studio
from backlot.errors import BacklotError
from backlot.frontmatter import load_yaml


THRESHOLDS = {"confirm_over_eur": 0.0, "max_call_eur": 1.0, "escalate_pct": 80.0}


@dataclass
class Project:
    root: Path
    data: dict[str, Any]

    @property
    def slug(self) -> str:
        return str(self.data.get("slug") or self.root.name)

    @property
    def vault_project(self) -> Path:
        vp = self.data.get("vault_project")
        if not vp:
            raise BacklotError(f"project.yaml has no vault_project: {self.yaml_path}")
        return Path(str(vp)).expanduser()

    @property
    def yaml_path(self) -> Path:
        return self.root / "project.yaml"

    @property
    def takes_dir(self) -> Path:
        return self.root / "takes"

    @property
    def renders_dir(self) -> Path:
        return self.root / "renders"

    @property
    def manifest(self) -> Path:
        return self.takes_dir / "manifest.jsonl"

    @property
    def budget_eur(self) -> float:
        return float(self.data.get("budget_eur") or 0.0)

    @property
    def ask_before_generate(self) -> bool:
        return bool(self.data.get("ask_before_generate", True))

    def threshold(self, key: str, studio: Studio | None = None) -> float:
        """project.yaml value, else studio.yaml `defaults:`, else the built-in default."""
        value = self.data.get(key)
        if value is None and studio is not None:
            value = studio.defaults.get(key)
        if value is None:
            value = THRESHOLDS[key]
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise BacklotError(f"{key} must be a number, got {value!r}") from exc

    @property
    def vault_prefix(self) -> str:
        """Vault-root-relative folder of the project (`Projects/<slug>`), for unambiguous wikilinks."""
        vp = self.vault_project
        return f"{vp.parent.name}/{vp.name}"

    @property
    def fps(self) -> int:
        return int(self.data.get("fps") or 24)

    @property
    def resolution(self) -> str:
        return str(self.data.get("resolution") or "1920x1080")

    @property
    def home_note(self) -> Path:
        return self.vault_project / f"{self.slug}.md"

    def default_model(self, kind: str) -> str | None:
        models = self.data.get("models") or {}
        value = models.get(kind)
        return str(value) if value else None

    def save(self) -> None:
        self.yaml_path.write_text(yaml.safe_dump(self.data, sort_keys=False), encoding="utf-8")


def load_project_dir(root: Path) -> Project:
    path = root / "project.yaml"
    if not path.exists():
        raise BacklotError(f"no project.yaml in {root}")
    data = load_yaml(path.read_text(encoding="utf-8")) or {}
    return Project(root=root.resolve(), data=data)


def resolve_project(studio: Studio, slug: str | None = None, cwd: Path | None = None) -> Project:
    if slug:
        root = studio.projects_root / slug
        if not (root / "project.yaml").exists():
            raise BacklotError(f"project {slug!r} not found under {studio.projects_root}")
        return load_project_dir(root)
    here = (cwd or Path(os.getcwd())).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "project.yaml").exists():
            return load_project_dir(candidate)
    raise BacklotError("not inside a project (no project.yaml found upwards); use --project <slug>")

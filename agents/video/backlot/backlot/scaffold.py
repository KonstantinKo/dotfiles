"""`backlot init`: scaffold the vault project and the project dir from templates."""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from backlot.config import Studio
from backlot.errors import BacklotError

BUILTIN = Path(__file__).resolve().parent.parent / "templates"
_PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
_TEXT_EXT = {".md", ".base", ".yaml", ".yml", ".txt", ".json", ""}


def _fill(text: str, values: dict[str, Any]) -> str:
    return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), text)


def _copy_tree(src: Path, dest: Path, values: dict[str, Any], rename: dict[str, str]) -> list[Path]:
    written: list[Path] = []
    for path in sorted(src.rglob("*")):
        if path.is_dir() or path.name == "README.md" or path.name == "Model.md":
            continue
        rel = path.relative_to(src)
        source = path
        name = rename.get(rel.name, rel.name)
        target = dest / rel.parent / _fill(name, values)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        if path.suffix in _TEXT_EXT:
            target.write_text(_fill(source.read_text(encoding="utf-8"), values), encoding="utf-8")
        else:
            target.write_bytes(source.read_bytes())
        written.append(target)
    return written


def init_project(studio: Studio, slug: str, *, fmt: str, fps: int, res: str, budget: float, title: str | None = None) -> dict[str, Any]:
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        raise BacklotError(f"slug {slug!r} must be lowercase letters, digits and dashes")
    vault_project = studio.vault / "Projects" / slug
    project_dir = studio.projects_root / slug
    if budget <= 0:
        raise BacklotError(f"--budget must be greater than 0 EUR (got {budget:g}); a project without budget cannot generate")
    if (project_dir / "project.yaml").exists():
        raise BacklotError(f"project {slug!r} already exists at {project_dir}")
    values = {
        "slug": slug,
        "title": title or slug.replace("-", " ").title(),
        "format": fmt,
        "fps": fps,
        "resolution": res,
        "budget_eur": budget,
        "date": date.today().isoformat(),
        "vault_project": str(vault_project),
        "project_dir": str(project_dir),
    }
    vault_templates = studio.vault / "_templates"
    if not (vault_templates / "project.md").is_file():
        raise BacklotError(f"vault templates missing: {vault_templates / 'project.md'} (the vault's _templates/ folder is the source for init)")
    written = _copy_tree(vault_templates, vault_project, values, {"project.md": f"{slug}.md"})
    for sub in ("Context/Cast", "Context/Locations", "Context/Props", "Shots", "Takes", "_thumbs"):
        (vault_project / sub).mkdir(parents=True, exist_ok=True)
    (vault_project / "_thumbs" / ".gitkeep").touch()
    dir_src = vault_templates / "projectdir" if (vault_templates / "projectdir").is_dir() else BUILTIN / "projectdir"
    written += _copy_tree(dir_src, project_dir, values, {"gitignore": ".gitignore"})
    for sub in ("inputs", "takes", "renders", "edit"):
        (project_dir / sub).mkdir(parents=True, exist_ok=True)
    git = _git_init(project_dir)
    return {"slug": slug, "vault_project": str(vault_project), "project_dir": str(project_dir), "files": len(written), "git": git}


def _git_init(project_dir: Path) -> str:
    if (project_dir / ".git").exists():
        return "existing"
    try:
        subprocess.run(["git", "init", "-q", str(project_dir)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(project_dir), "add", "-A"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(project_dir), "-c", "user.name=backlot", "-c", "user.email=backlot@localhost", "commit", "-q", "-m", "init project"],
            check=False, capture_output=True,
        )
        return "initialized"
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"failed: {exc}"

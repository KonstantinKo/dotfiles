"""Production stages in order, and the gate each one has to pass before `backlot stage --advance`."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from backlot import frontmatter, vault
from backlot import takes as takes_mod
from backlot.errors import BacklotError
from backlot.project import Project

STAGES = ("idea", "brief", "develop", "preproduction", "boards", "shots", "voice", "score", "assemble", "review", "deliver", "delivered")


def next_stage(stage: str) -> str | None:
    i = STAGES.index(stage)
    return STAGES[i + 1] if i + 1 < len(STAGES) else None


def _template_body(project: Project, name: str) -> str:
    path = project.vault_project.parent.parent / "_templates" / name
    if not path.is_file():
        return ""
    try:
        return frontmatter.read(path)[1]
    except ValueError:
        return ""


_PLACEHOLDER = re.compile(r"\{\{\s*\w+\s*\}\}")


def _non_template(project: Project, name: str) -> bool:
    """A note counts as written when it has at least one non-empty line the template does not have
    (template lines with `{{placeholders}}` match whatever init filled in)."""
    path = project.vault_project / name
    if not path.is_file():
        return False
    try:
        body = frontmatter.read(path)[1]
    except ValueError:
        return False
    patterns = [
        re.compile("^" + ".*".join(re.escape(part) for part in _PLACEHOLDER.split(l.strip())) + "$")
        for l in _template_body(project, name).splitlines() if l.strip()
    ]
    return any(l.strip() and not any(p.match(l.strip()) for p in patterns) for l in body.splitlines())


def _gate_idea(project: Project) -> list[str]:
    return [] if (project.vault_project / "Brief.md").is_file() else ["Brief.md"]


def _gate_brief(project: Project) -> list[str]:
    return [] if _non_template(project, "Brief.md") else ["Brief.md is still the template"]


def _gate_develop(project: Project) -> list[str]:
    path = project.vault_project / "Script.md"
    if not path.is_file():
        return ["Script.md"]
    body = frontmatter.read(path)[1]
    lines = body.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip().lower() == "## beats"), None)
    if start is None:
        return ["Script.md has no `## Beats` section"]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    section = [l.strip() for l in lines[start + 1:end] if l.strip()]
    table = [l for l in section if l.startswith("|")]
    separator = next((i for i, l in enumerate(table) if re.match(r"^\|[\s\-:|]+\|$", l)), None)
    rows = table[separator + 1:] if separator is not None else []
    rows += [l for l in section if re.match(r"^(?:[-*]|\d+\.)\s", l)]
    return [] if rows else ["Script.md `## Beats` has no rows"]


def _gate_preproduction(project: Project) -> list[str]:
    notes = [p for p in vault.context_notes(project) if p.parent.name in ("Cast", "Locations")]
    if not notes:
        return ["no Cast or Locations notes"]
    missing = []
    for path in notes:
        try:
            data, _ = frontmatter.read(path)
        except ValueError:
            data = {}
        if data.get("locked") is not True:
            missing.append(f"{path.parent.name}/{path.stem} not locked")
    return missing


def _shots_or_missing(project: Project) -> tuple[list[dict[str, Any]], list[str]]:
    shots = vault.load_shots(project)
    return shots, ([] if shots else ["no shot notes"])


def _gate_boards(project: Project) -> list[str]:
    shots, missing = _shots_or_missing(project)
    for s in shots:
        take = s.get("board_take")
        if not take:
            missing.append(f"{s['shot']} has no board_take")
            continue
        try:
            status = takes_mod.load_take(project, str(take)).status
        except BacklotError:
            status = "missing"
        if status != "approved":
            missing.append(f"{s['shot']} board_take {take} is {status}")
    return missing


def _gate_shots(project: Project) -> list[str]:
    shots, missing = _shots_or_missing(project)
    return missing + [f"{s['shot']} has no video_take" for s in shots if not s.get("video_take")]


def _gate_voice(project: Project) -> list[str]:
    shots, missing = _shots_or_missing(project)
    return missing + [f"{s['shot']} has no vo_take" for s in shots if not s.get("vo_take") and s.get("vo", True) is not False]


def _timeline(project: Project) -> dict[str, Any]:
    path = project.root / "edit" / "timeline.yaml"
    if not path.is_file():
        return {}
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _gate_score(project: Project) -> list[str]:
    tracks = {str(a.get("track") or "") for a in (_timeline(project).get("audio") or [])}
    home = vault.home_data(project)
    if home.get("score") is False or tracks & {"music", "sfx"}:
        return []
    return ["timeline.yaml has no music or sfx track (or set `score: false` on the project note)"]


def _renders(project: Project) -> list[Path]:
    if not project.renders_dir.is_dir():
        return []
    return sorted(p for p in project.renders_dir.iterdir() if p.is_file() and p.suffix.lower() in (".mp4", ".mov", ".webm"))


def _gate_assemble(project: Project) -> list[str]:
    if not (project.root / "edit" / "timeline.yaml").is_file():
        return ["edit/timeline.yaml"]
    if not _timeline(project).get("video"):
        return ["edit/timeline.yaml has no video clips"]
    return [] if any(p.stem.startswith("timeline") for p in _renders(project)) else ["no render of timeline.yaml in renders/"]


def _gate_review(project: Project) -> list[str]:
    return [] if (project.vault_project / "Review.md").is_file() else ["Review.md"]


def _gate_deliver(project: Project) -> list[str]:
    return [] if _renders(project) else ["no renders in renders/"]


def _gate_delivered(project: Project) -> list[str]:
    return []


GATES: dict[str, Callable[[Project], list[str]]] = {
    "idea": _gate_idea, "brief": _gate_brief, "develop": _gate_develop, "preproduction": _gate_preproduction,
    "boards": _gate_boards, "shots": _gate_shots, "voice": _gate_voice, "score": _gate_score,
    "assemble": _gate_assemble, "review": _gate_review, "deliver": _gate_deliver, "delivered": _gate_delivered,
}


def check(project: Project) -> dict[str, Any]:
    from backlot.workflow import declaration, evaluate

    stage = str(vault.home_data(project).get("status") or "idea")
    if stage not in STAGES:
        raise BacklotError(f"project status {stage!r} is not a stage; expected one of {', '.join(STAGES)}")
    declared = declaration(project)
    if declared is not None and declared.get("preset") != "legacy":
        readiness = evaluate(project)
        return {"stage": stage, "passed": readiness["passed"],
                "missing": readiness["blockers"], "next": "delivered" if stage != "delivered" else None,
                "readiness": readiness["readiness"], "scenes": readiness["scenes"],
                "deliverables": readiness["deliverables"]}
    missing = GATES[stage](project)
    return {"stage": stage, "passed": not missing, "missing": missing, "next": next_stage(stage)}


def advance(project: Project) -> dict[str, Any]:
    info = check(project)
    if not info["passed"]:
        return {**info, "advanced": False}
    if info["next"] is None:
        return {**info, "advanced": False}
    vault.update_home(project, status=info["next"])
    return {**info, "advanced": True}

"""Compact current project handoff, derived from typed decisions and work state."""

from __future__ import annotations

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import yaml

from backlot import vault
from backlot.decisions import list_decisions
from backlot.errors import BacklotError
from backlot.project import Project
from backlot.takes import spent_eur


def work_path(project: Project) -> Path:
    return project.vault_project / "Records" / "work.yaml"


def load_work(project: Project) -> dict[str, Any]:
    path = work_path(project)
    if not path.exists():
        return {"schema_version": 1, "revision": 0, "owner_by_scene": {},
                "review_surface": "unspecified", "open_work": [], "selected_references": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("schema_version") != 1:
        raise BacklotError("unsupported work record schema")
    return data


@contextmanager
def _locked(project: Project) -> Iterator[None]:
    path = work_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _save(project: Project, data: dict[str, Any]) -> None:
    path = work_path(project)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(tmp, path)


def claim(project: Project, scene: str, worker: str, base_revision: int) -> dict[str, Any]:
    if not scene.strip() or not worker.strip():
        raise BacklotError("scene and worker are required")
    with _locked(project):
        data = load_work(project)
        if data["revision"] != base_revision:
            raise BacklotError(f"handoff changed: expected revision {base_revision}, current {data['revision']}")
        owners = data.setdefault("owner_by_scene", {})
        owner = owners.get(scene)
        if owner and owner != worker:
            raise BacklotError(f"{scene} is owned by {owner}; propose a handoff first")
        owners[scene] = worker
        data["revision"] += 1
        _save(project, data)
        return data


def _latest(decisions: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    effective: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in decisions:
        if row.get("subject_type") != kind or row.get("action") not in ("approve", "reject"):
            continue
        key = (kind, str(row.get("subject_id")), str(row.get("version")), str(row.get("scope")))
        effective.pop(key, None)
        effective[key] = row
    return next((row for row in reversed(list(effective.values())) if row.get("action") == "approve"), None)


def render(project: Project) -> str:
    work = load_work(project)
    decisions = list_decisions(project)
    home = vault.home_data(project)
    candidates = [_latest(decisions, kind) for kind in ("picture", "scored", "share")]
    current = next((row for row in reversed(candidates) if row), None)
    path = project.vault_project / "Handoff.md"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "## Work intent\n"
    intent = old.split(marker, 1)[1].strip() if marker in old else ""
    lines = ["---", "type: handoff", "schema_version: 1", f"work_revision: {work['revision']}", "---",
             "# Current handoff", "", f"Project: {project.slug} · legacy stage: {home.get('status', 'unknown')}", "",
             "## Deliverables and approval scope", ""]
    for kind, row in zip(("picture", "scored", "share"), candidates):
        if row:
            lines.append(f"- {kind}: `{row['subject_id']}` @ `{row['version']}` · {row['scope']} · `{row['id']}`")
        else:
            lines.append(f"- {kind}: no typed approval recorded")
    lines += ["", f"Current approved variant: `{current['subject_id']}` ({current['subject_type']})" if current else
              "Current approved variant: unregistered; inspect Delivery.md and existing final manifests before proposing work.",
              "", "## Work and review", "", f"Work revision: {work['revision']}",
              f"Review surface: {work.get('review_surface') or 'unspecified'}", ""]
    for scene, worker in sorted((work.get("owner_by_scene") or {}).items()):
        lines.append(f"- {scene}: {worker}")
    for item in work.get("open_work") or []:
        lines.append(f"- Open: {item}")
    if not (work.get("owner_by_scene") or work.get("open_work")):
        lines.append("- No current work claim recorded")
    lines += ["", "## Scene and shot map", ""]
    shots = vault.load_shots(project)
    for shot in shots:
        name = shot.get("name") or shot.get("scene") or shot.get("beat") or shot.get("description") or "unnamed"
        lines.append(f"- {name} · `{shot['shot']}` · {shot.get('status') or 'planned'}")
    if not shots:
        lines.append("- No shot records")
    lines += ["", "## References and accepted limits", ""]
    for ref in work.get("selected_references") or []:
        lines.append(f"- Reference: {ref}")
    limits = [row for row in decisions if row.get("action") == "accept-limit"]
    for row in limits:
        lines.append(f"- Accepted: {row['subject_type']} `{row['subject_id']}` @ `{row['version']}` · {row['reason']}")
    if not limits and not work.get("selected_references"):
        lines.append("- None recorded in typed state; inspect legacy Review.md")
    lines += ["", "## Spend", "", f"Backlot EUR ledger: {spent_eur(project):.4f} / {project.budget_eur:.2f} EUR.",
              "Native-unit external charges and balances need separate reconciliation.",
              "", marker.rstrip(), "", intent or "Add a short current instruction here; this section survives refresh.", ""]
    result = "\n".join(lines)
    path.write_text(result, encoding="utf-8")
    return result

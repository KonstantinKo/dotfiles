"""approve / reject / stale: update take + shot + context notes and the Decisions ledger."""

from __future__ import annotations

from datetime import date
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import os
import uuid

import yaml

from backlot import frontmatter
from backlot import takes as takes_mod
from backlot import vault
from backlot.config import Studio
from backlot.errors import BacklotError
from backlot.models import load_models
from backlot.project import Project
from backlot.takes import Take
from backlot.authority import file_hash


def record_decision(project: Project, action: str, subject_type: str, subject_id: str, *,
                    version: str, scope: str, reason: str, source_ref: str,
                    source_message: str, source_kind: str = "user",
                    source_at: str | None = None,
                    coverage: list[list[int]] | None = None) -> dict[str, Any]:
    """Record an explicit, version-bound decision without changing another object's status."""
    if action not in ("approve", "reject", "accept-limit"):
        raise BacklotError("invalid decision action")
    if subject_type not in ("take", "reference", "shot", "range", "picture", "scored", "share"):
        raise BacklotError("invalid decision subject type")
    if not all(x and x.strip() for x in (subject_id, version, scope, reason, source_ref, source_message)):
        raise BacklotError("decision needs a subject version, scope, reason and explicit source message/reference")
    if source_kind not in ("user", "agent", "legacy"):
        raise BacklotError("source_kind must be user, agent or legacy")
    if source_at:
        try:
            stamp = datetime.fromisoformat(source_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise BacklotError("source_at needs an ISO timestamp with timezone") from exc
        if stamp.tzinfo is None:
            raise BacklotError("source_at needs an ISO timestamp with timezone")
    if coverage is not None and (not coverage or any(
            not isinstance(r, list) or len(r) != 2 or
            not all(isinstance(n, int) and n >= 0 for n in r) or r[1] < r[0]
            for r in coverage)):
        raise BacklotError("coverage needs nonempty inclusive [start, end] frame ranges")
    record = {
        "schema_version": 1, "id": f"dec-{uuid.uuid4().hex}", "action": action,
        "subject_type": subject_type, "subject_id": subject_id,
        "version": version, "scope": scope, "reason": reason,
        "source_ref": source_ref, "source_message": source_message,
        "source_kind": source_kind, "source_at": source_at,
        "coverage": coverage,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    folder = project.vault_project / "Records" / "decisions"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{record['id']}.yaml"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(tmp, path)
    vault.prepend_decision(project, action, f"{subject_type}:{subject_id}@{version[:12]}",
                           reason, extra=f"[{scope}; {record['id']}]")
    from backlot.handoff import render

    render(project)
    return record


def list_decisions(project: Project) -> list[dict[str, Any]]:
    folder = project.vault_project / "Records" / "decisions"
    return sorted((yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                   for path in folder.glob("dec-*.yaml")) if folder.is_dir() else (),
                  key=lambda row: row.get("recorded_at", ""))


def approve(project: Project, take_id: str, reason: str, lock: str | None = None,
            studio: Studio | None = None, *, source_ref: str | None = None,
            source_message: str | None = None, scope: str = "provisional production use") -> dict[str, Any]:
    if not source_ref or not source_message:
        raise BacklotError("approval needs the user's explicit --source-ref and --source-message")
    take = takes_mod.load_take(project, take_id)
    if take.status in takes_mod.UNFINISHED:
        raise BacklotError(f"take {take_id} is {take.status}; recover or discard it before approving")
    version = file_hash(project.root / take.file) if take.file else take.take
    record_decision(project, "approve", "take", take_id, version=version,
                    scope=scope, reason=reason, source_ref=source_ref,
                    source_message=source_message)
    take = takes_mod.set_status(project, take_id, "approved", reason)
    vault.set_take_note_status(project, take_id, "approved", reason)
    vault.record_approval_on_shot(project, take)
    locked = None
    if lock:
        locked = vault.lock_context(project, lock, take_id)
        vault.prepend_decision(project, "lock", lock.split("/")[-1], reason, extra=f"-> {take_id}")
    promoted = promote_model(studio, take) if studio else None
    vault.write_status(project, studio)
    return {"take": take_id, "status": "approved", "shot": take.shot, "locked": str(locked) if locked else None, "model_promoted": str(promoted) if promoted else None}


def promote_model(studio: Studio, take: Take) -> Path | None:
    """First approval of an `untested` model makes it `active` and records what was observed."""
    models, _ = load_models(studio.vault)
    model = next((m for m in models if m.id == take.model), None)
    if model is None or model.path is None or model.status != "untested":
        return None
    frontmatter.update(model.path, status="active")
    data, body = frontmatter.read(model.path)
    line = f"- {date.today().isoformat()} · {take.take} · {take.seconds:.1f} s · {take.cost_eur:.3f} EUR"
    lines = body.rstrip("\n").split("\n")
    anchor = next((i for i, l in enumerate(lines) if l.strip().lower() == "## observed"), None)
    if anchor is None:
        lines += ["", "## Observed", "", line]
    else:
        end = next((i for i in range(anchor + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        while end > anchor + 1 and not lines[end - 1].strip():
            end -= 1
        lines.insert(end, line)
    frontmatter.write(model.path, data, "\n".join(lines) + "\n")
    return model.path


def reject(project: Project, take_id: str, reason: str, *, source_ref: str | None = None,
           source_message: str | None = None, scope: str = "raw take",
           source_kind: str = "agent") -> dict[str, Any]:
    if bool(source_ref) != bool(source_message):
        raise BacklotError("rejection source needs both --source-ref and --source-message")
    take = takes_mod.set_status(project, take_id, "rejected", reason)
    vault.set_take_note_status(project, take_id, "rejected", reason)
    if source_ref and source_message:
        version = file_hash(project.root / take.file) if take.file else take.take
        record_decision(project, "reject", "take", take_id, version=version,
                        scope=scope, reason=reason, source_ref=source_ref,
                        source_message=source_message, source_kind=source_kind)
    else:
        vault.prepend_decision(project, "reject", take_id, reason,
                               extra=f"({take.shot}) [legacy scope unverified]" if take.shot else "[legacy scope unverified]")
    vault.write_status(project)
    return {"take": take_id, "status": "rejected", "shot": take.shot}


def stale(project: Project, note: str, reason: str, dry_run: bool = False) -> dict[str, Any]:
    """Mark everything that depends on a Context note, through dependent Context notes too."""
    target = vault.context_note(project, note)
    dependents = vault.context_dependents(project, target)
    targets = [target, *dependents]

    def depends(names: list[str]) -> bool:
        return any(vault.note_matches(str(n), t, project) for n in names for t in targets)

    stale_takes = [t.take for t in takes_mod.list_takes(project) if t.status != "stale" and depends(t.depends_on)]
    stale_shots: list[str] = []
    for shot in vault.load_shots(project):
        if shot.get("status") == "stale":
            continue
        refs = {shot.get("board_take"), shot.get("video_take"), shot.get("vo_take")}
        if depends(shot.get("depends_on") or []) or refs & set(stale_takes):
            stale_shots.append(str(shot["shot"]))
    context = [str(p.relative_to(project.vault_project / "Context").with_suffix("")) for p in dependents]
    info = {"note": target.stem, "takes": stale_takes, "shots": stale_shots, "context": context, "dry_run": dry_run}
    if not stale_takes and not stale_shots and not dependents:
        raise BacklotError(f"nothing depends on {target.stem!r}", code=0, data=info)
    if dry_run:
        return info
    for tid in stale_takes:
        takes_mod.set_status(project, tid, "stale", reason)
        vault.set_take_note_status(project, tid, "stale", reason)
    for sid in stale_shots:
        vault.update_shot(project, sid, status="stale")
    for path in dependents:
        frontmatter.update(path, stale=True, stale_reason=reason)
    vault.prepend_decision(project, "stale", target.stem, reason, extra=f"-> {len(stale_takes)} takes, {len(stale_shots)} shots, {len(dependents)} context notes")
    vault.write_status(project)
    return info

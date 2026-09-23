"""approve / reject / stale: update take + shot + context notes and the Decisions ledger."""

from __future__ import annotations

from typing import Any

from backlot import takes as takes_mod
from backlot import vault
from backlot.errors import BacklotError
from backlot.project import Project


def approve(project: Project, take_id: str, reason: str, lock: str | None = None) -> dict[str, Any]:
    take = takes_mod.set_status(project, take_id, "approved", reason)
    vault.set_take_note_status(project, take_id, "approved", reason)
    vault.record_approval_on_shot(project, take)
    locked = None
    if lock:
        locked = vault.lock_context(project, lock, take_id)
        vault.prepend_decision(project, "lock", lock.split("/")[-1], reason, extra=f"-> {take_id}")
    vault.prepend_decision(project, "approve", take_id, reason, extra=f"({take.shot})" if take.shot else "")
    vault.write_status(project)
    return {"take": take_id, "status": "approved", "shot": take.shot, "locked": str(locked) if locked else None}


def reject(project: Project, take_id: str, reason: str) -> dict[str, Any]:
    take = takes_mod.set_status(project, take_id, "rejected", reason)
    vault.set_take_note_status(project, take_id, "rejected", reason)
    vault.prepend_decision(project, "reject", take_id, reason, extra=f"({take.shot})" if take.shot else "")
    vault.write_status(project)
    return {"take": take_id, "status": "rejected", "shot": take.shot}


def stale(project: Project, note: str, reason: str) -> dict[str, Any]:
    target = vault.context_note(project, note)
    stale_takes: list[str] = []
    for take in takes_mod.list_takes(project):
        if take.status == "stale":
            continue
        if any(vault.note_matches(dep, target, project) for dep in take.depends_on):
            takes_mod.set_status(project, take.take, "stale", reason)
            vault.set_take_note_status(project, take.take, "stale", reason)
            stale_takes.append(take.take)
    stale_shots: list[str] = []
    for shot in vault.load_shots(project):
        if shot.get("status") == "stale":
            continue
        deps = shot.get("depends_on") or []
        refs = {shot.get("board_take"), shot.get("video_take"), shot.get("vo_take")}
        if any(vault.note_matches(str(d), target, project) for d in deps) or refs & set(stale_takes):
            vault.update_shot(project, str(shot["shot"]), status="stale")
            stale_shots.append(str(shot["shot"]))
    if not stale_takes and not stale_shots:
        raise BacklotError(f"nothing depends on {target.stem!r}", code=0, data={"note": target.stem, "takes": [], "shots": []})
    vault.prepend_decision(project, "stale", target.stem, reason, extra=f"-> {len(stale_takes)} takes, {len(stale_shots)} shots")
    vault.write_status(project)
    return {"note": target.stem, "takes": stale_takes, "shots": stale_shots}

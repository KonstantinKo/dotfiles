"""Exact source-version edges and targeted, read-only review flags."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backlot.authority import file_hash
from backlot.project import Project
from backlot.takes import Take, list_takes


def check(project: Project) -> dict[str, Any]:
    """Report changed/missing output versions and their source descendants.

    Recorded hashes and decisions stay frozen; review flags are a projection.
    """
    records = list_takes(project)
    by_id = {take.take: take for take in records}
    by_path = {str((project.root / take.file).resolve()): take for take in records if take.file}
    newest: dict[str, Take] = {}
    for take in records:
        key = take.extra.get("source_key")
        if key and (key not in newest or (take.extra.get("registered_at", ""), take.take)
                    > (newest[key].extra.get("registered_at", ""), newest[key].take)):
            newest[key] = take
    direct: dict[str, list[str]] = {}
    parents: dict[str, set[str]] = {}
    for take in records:
        if take.file:
            output = Path(take.file)
            if not output.is_absolute():
                output = project.root / output
            if not take.sha256:
                direct.setdefault(take.take, []).append("output version unavailable: no recorded SHA-256")
            elif not output.is_file():
                direct.setdefault(take.take, []).append(f"recorded output missing: {output}")
            elif file_hash(output) != take.sha256:
                direct.setdefault(take.take, []).append(f"recorded output bytes changed: {output}")
        for ref in take.source_refs:
            ref_id = str(ref.get("id") or "")
            path = Path(str(ref.get("path") or ""))
            if not path.is_absolute():
                path = project.root / path
            source = by_id.get(ref_id) or by_path.get(str(path.resolve()))
            if source:
                parents.setdefault(source.take, set()).add(take.take)
                key = source.extra.get("source_key")
                if key and newest.get(key) is not source and newest[key].sha256 != ref.get("sha256"):
                    direct.setdefault(take.take, []).append(f"{source.take} has newer version {newest[key].take}")
            if not path.is_file():
                direct.setdefault(take.take, []).append(f"source missing: {ref_id or path}")
            elif file_hash(path) != ref.get("sha256"):
                direct.setdefault(take.take, []).append(f"source bytes changed: {ref_id or path}")
    affected = set(direct)
    queue = list(affected)
    while queue:
        current = queue.pop(0)
        for child in parents.get(current, ()):
            if child not in affected:
                affected.add(child)
                queue.append(child)
    return {"direct": direct, "needs_review": sorted(affected),
            "recorded_output_versions_available": not any(
                reason.startswith("output version unavailable") or reason.startswith("recorded output missing")
                for reasons in direct.values() for reason in reasons),
            "recorded_output_bytes_unchanged": not any(
                reason.startswith(("recorded output bytes changed", "recorded output missing",
                                   "output version unavailable"))
                for reasons in direct.values() for reason in reasons),
            "records_checked": len(records)}

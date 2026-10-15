"""Register existing media by reference and verified bytes, without provider calls or copying."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backlot import authority, expenses, ffmpeg, takes, vault
from backlot.errors import BacklotError
from backlot.ids import TAKE_PREFIXES, validate_take_id
from backlot.project import Project
from backlot.takes import Take

ORIGINS = {"provider", "supplied", "local_derivative", "assembly"}


def _path(project: Project, value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else project.root / path).resolve()


def _hash_media(path: Path, expected: str | None = None) -> str:
    if not path.is_file():
        raise BacklotError(f"media missing: {path}")
    actual = authority.file_hash(path)
    if expected and actual != expected:
        raise BacklotError(f"media hash differs from declared version: {path}")
    return actual


def _probe(path: Path) -> dict[str, Any]:
    command = ffmpeg.which("ffprobe")
    if not command:
        raise BacklotError("ffprobe is required to register media")
    result = subprocess.run([command, "-v", "error", "-show_entries",
                             "format=duration,size,format_name:stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
                             "-of", "json", str(path)], capture_output=True, text=True, check=False)
    if result.returncode:
        raise BacklotError(f"cannot probe media {path}: {result.stderr.strip()[:300]}")
    return json.loads(result.stdout or "{}")


def _sources(project: Project, values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for value in values:
        if not isinstance(value, dict) or not (value.get("id") or value.get("path")):
            raise BacklotError("each source_ref needs a take id or path")
        record = dict(value)
        ref = str(record.get("id") or record.get("path"))
        if record.get("id") and takes.meta_path(project, ref).exists():
            source = takes.take_file(project, ref)
        else:
            source = _path(project, str(record.get("path") or ref))
        record["id"] = ref
        record["path"] = str(source)
        record["sha256"] = _hash_media(source, record.get("sha256"))
        output.append(record)
    return output


def prepare(project: Project, spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise BacklotError("register spec must be a JSON object")
    origin = str(spec.get("origin") or "")
    kind = str(spec.get("kind") or "")
    if origin not in ORIGINS or kind not in TAKE_PREFIXES:
        raise BacklotError(f"register needs origin in {sorted(ORIGINS)} and kind in {TAKE_PREFIXES}")
    if not spec.get("media"):
        raise BacklotError("register needs media path")
    path = _path(project, str(spec["media"]))
    digest = _hash_media(path, spec.get("sha256"))
    source_refs = _sources(project, spec.get("source_refs") or [])
    if origin in {"local_derivative", "assembly"} and not source_refs:
        raise BacklotError(f"{origin} needs exact source_refs")
    coverage = spec.get("coverage") or []
    if not isinstance(coverage, list) or any(not isinstance(x, dict) for x in coverage):
        raise BacklotError("coverage must be a list of shot/story range objects")
    for item in coverage:
        if not (item.get("shot") or item.get("story")):
            raise BacklotError("each coverage entry needs shot or story")
        for key in ("source_frames", "output_frames"):
            if key in item:
                rng = item[key]
                if not isinstance(rng, list) or len(rng) != 2 or not all(isinstance(v, int) and v >= 0 for v in rng) or rng[1] < rng[0]:
                    raise BacklotError(f"coverage {key} needs [start, end_inclusive]")
    provider = str(spec.get("provider") or ("local" if origin in {"local_derivative", "assembly"} else origin))
    operation_id = str(spec.get("operation_id") or "")
    identity = f"{provider}\0{operation_id}\0{digest}" if operation_id else f"{origin}\0{path}\0{digest}"
    probe = _probe(path)
    _hash_media(path, digest)
    return {**spec, "media": str(path), "sha256": digest, "probe": probe,
            "source_refs": source_refs, "coverage": coverage, "origin": origin,
            "kind": kind, "provider": provider, "operation_id": operation_id,
            "import_key": hashlib.sha256(identity.encode()).hexdigest()}


def register(project: Project, spec: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    prepared = prepare(project, spec)
    if dry_run:
        return {"prepared": prepared, "provider_calls": 0, "media_copied": False}
    with takes.locked(project):
        _hash_media(Path(prepared["media"]), prepared["sha256"])
        def same_import(t: Take) -> bool:
            if t.import_key == prepared["import_key"]:
                return True
            if not (prepared["operation_id"] and t.provider == prepared["provider"]
                    and t.request_id == prepared["operation_id"] and t.file):
                return False
            path = project.root / t.file
            return path.is_file() and _hash_media(path) == prepared["sha256"]

        existing = takes.list_takes(project)
        duplicate = next((t for t in existing if same_import(t)), None)
        old = None
        if prepared.get("id"):
            take_id = validate_take_id(str(prepared["id"]))
            if not take_id.startswith(prepared["kind"] + "-"):
                raise BacklotError("id prefix does not match kind")
            if takes.meta_path(project, take_id).exists():
                old = takes.load_take(project, take_id)
            if duplicate and duplicate.take != take_id:
                raise BacklotError(f"identical provider job and media already registered as {duplicate.take}")
        else:
            old = duplicate
            take_id = old.take if old else takes.allocate_id(project, prepared["kind"])
        if old:
            if old.schema_version > takes.SCHEMA_VERSION:
                raise BacklotError(f"{old.take} has future schema version {old.schema_version}")
            old_path = takes.take_file(project, old.take) if old.file else None
            if old_path and old_path.resolve() != Path(prepared["media"]).resolve():
                raise BacklotError(f"{old.take} already names different media")
            if old.sha256 and old.sha256 != prepared["sha256"]:
                raise BacklotError(f"{old.take} already names a different media version")
            if old.request_id and prepared["operation_id"] and old.request_id != prepared["operation_id"]:
                raise BacklotError(f"{old.take} already has another operation id")
            if old.provider and old.provider != prepared["provider"]:
                raise BacklotError(f"{old.take} already has another provider")
            if old.import_key and old.import_key != prepared["import_key"]:
                raise BacklotError(f"{old.take} already has another import identity")
            take = old
        else:
            if prepared.get("status") == "approved":
                raise BacklotError("new imported media needs a separate sourced take approval")
            take = Take(take=take_id, kind=prepared["kind"], model=str(prepared.get("model") or "external"),
                        provider=prepared["provider"], status=str(prepared.get("status") or "new"))
        if take.status not in takes.STATUSES:
            raise BacklotError(f"invalid status {take.status}")
        if prepared.get("expense"):
            expense_spec = {**prepared["expense"], "provider": prepared["provider"],
                            "operation_id": prepared["operation_id"] or None}
            candidate = expenses.normalize(expense_spec)
            linked = expenses.find_unlocked(project, candidate, linked_id=take.expense_id or None)
            if linked:
                candidate["id"] = linked["id"]
            ledger = candidate.get("project_ledger") or {}
            target_cost = take.cost_eur
            if ledger.get("unit") == "EUR":
                amount = float(ledger["amount"])
                related = [t for t in existing if t.take == take.take or
                           (prepared["operation_id"] and t.provider == prepared["provider"]
                            and t.request_id == prepared["operation_id"]) or t.expense_id == candidate["id"]]
                booked = round(sum(t.cost_eur for t in related), 4)
                if abs(booked - amount) > 0.00005:
                    if take.cost_eur == 0 and booked < amount:
                        target_cost = round(amount - booked, 4)
                    else:
                        raise BacklotError(f"operation EUR ledger {amount} conflicts with existing take costs {booked}")
            expense = expenses.upsert_unlocked(project, expense_spec, linked_id=take.expense_id or None)
            take.expense_id = expense["id"]
            take.cost_eur = target_cost
        take.file = str(Path(prepared["media"]).relative_to(project.root)) if Path(prepared["media"]).is_relative_to(project.root) else prepared["media"]
        take.sha256 = prepared["sha256"]
        take.probe = prepared["probe"]
        take.source_refs = prepared["source_refs"] if "source_refs" in spec else take.source_refs
        take.coverage = prepared["coverage"] if "coverage" in spec else take.coverage
        take.original_request = dict(prepared["original_request"]) if "original_request" in spec else take.original_request
        take.effective_request = dict(prepared["effective_request"]) if "effective_request" in spec else take.effective_request
        take.review_scope = str(prepared.get("review_scope") or take.review_scope)
        take.import_key = prepared["import_key"]
        take.schema_version = takes.SCHEMA_VERSION
        take.request_id = prepared["operation_id"] or take.request_id
        take.origin = prepared["origin"]
        take.model = str(prepared.get("model") or take.model)
        take.provider = prepared["provider"]
        take.shot = prepared.get("shot") or take.shot
        take.prompt = str(prepared.get("prompt") or take.prompt)
        take.params = {**take.params, **(prepared.get("params") or {})}
        take.created = take.created or str(prepared.get("created") or "")
        known = {"id", "kind", "origin", "media", "sha256", "probe", "source_refs", "coverage", "provider", "operation_id", "import_key", "expense", "model", "status", "original_request", "effective_request", "review_scope", "shot", "prompt", "params", "created"}
        take.extra.update({k: v for k, v in prepared.items() if k not in known})
        take.extra.setdefault("registered_at", datetime.now(timezone.utc).isoformat())
        takes.take_dir(project, take.take).mkdir(parents=True, exist_ok=True)
        takes.write_meta(project, take)
        takes.rebuild_manifest(project)
    note = vault.take_note_path(project, take.take)
    if note.exists():
        from backlot import frontmatter
        frontmatter.update(note, schema_version=take.schema_version, origin=take.origin, sha256=take.sha256,
                           source_refs=take.source_refs, coverage=take.coverage, expense_id=take.expense_id)
    else:
        vault.write_take_note(project, take, None)
    vault.write_costs(project)
    return {"take": take.take, "sha256": take.sha256, "origin": take.origin,
            "expense_id": take.expense_id or None, "provider_calls": 0, "media_copied": False}

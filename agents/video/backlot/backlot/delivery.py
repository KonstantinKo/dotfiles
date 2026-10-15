"""Versioned assembly and deliverable records with read-only media verification."""

from __future__ import annotations

import os
import re
import subprocess
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from backlot import ffmpeg, lineage
from backlot.authority import file_hash
from backlot.decisions import list_decisions
from backlot.errors import BacklotError
from backlot.project import Project
from backlot.takes import load_take

_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ROUTES = {"native", "external", "custom"}
KINDS = {"picture", "scored", "share"}


def _record_path(project: Project, folder: str, record_id: str) -> Path:
    if not _ID.fullmatch(str(record_id)):
        raise BacklotError(f"invalid {folder} id {record_id!r}")
    return project.root / folder / f"{record_id}.yaml"


def _path(project: Project, value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else project.root / path).resolve()


def _range(value: Any, label: str) -> tuple[int, int]:
    if (not isinstance(value, list) or len(value) != 2 or
            any(not isinstance(n, int) or n < 0 for n in value) or value[1] < value[0]):
        raise BacklotError(f"{label} needs inclusive [start, end] frames")
    return value[0], value[1]


def _hash_once(path: Path, memo: dict[Path, str] | None) -> str:
    if memo is None:
        return file_hash(path)
    if path not in memo:
        memo[path] = file_hash(path)
    return memo[path]


def _take_media(project: Project, take_id: str,
                hash_memo: dict[Path, str] | None = None) -> tuple[Path, str]:
    take = load_take(project, take_id)
    if not take.file or not take.sha256:
        raise BacklotError(f"artifact {take_id} lacks media path or recorded SHA-256")
    path = _path(project, take.file)
    if not path.is_file() or _hash_once(path, hash_memo) != take.sha256:
        raise BacklotError(f"artifact {take_id} media missing or differs from recorded SHA-256")
    return path, take.sha256


def _reference(project: Project, value: dict[str, Any], label: str,
               hash_memo: dict[Path, str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BacklotError(f"{label} needs an object")
    take_id = str(value.get("artifact") or "")
    if take_id:
        path, digest = _take_media(project, take_id, hash_memo)
        if value.get("path") and _path(project, str(value["path"])) != path:
            raise BacklotError(f"{label} path differs from artifact {take_id}")
    else:
        if not value.get("path"):
            raise BacklotError(f"{label} needs artifact or path")
        path = _path(project, str(value["path"]))
        if not path.is_file():
            raise BacklotError(f"{label} missing: {path}")
        digest = _hash_once(path, hash_memo)
    if value.get("sha256") and value["sha256"] != digest:
        raise BacklotError(f"{label} SHA-256 differs: {path}")
    return {**value, "path": str(path), "sha256": digest}


def _video_probe(path: Path) -> dict[str, Any]:
    binary = ffmpeg.which("ffprobe")
    if not binary:
        raise BacklotError("ffprobe is required to verify a deliverable")
    proc = subprocess.run([binary, "-v", "error", "-count_frames", "-select_streams", "v:0",
                           "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration,size",
                           "-of", "json", str(path)], capture_output=True, text=True, check=False)
    if proc.returncode:
        raise BacklotError(f"cannot probe {path}: {proc.stderr.strip()[:200]}")
    import json

    result = json.loads(proc.stdout or "{}")
    streams = result.get("streams") or []
    if not streams:
        raise BacklotError(f"deliverable has no video stream: {path}")
    stream = streams[0]
    count = stream.get("nb_read_frames")
    if not count or count == "N/A":
        raise BacklotError(f"cannot count output video frames: {path}")
    return {"frames": int(count), "fps": stream.get("r_frame_rate"),
            "width": stream.get("width"), "height": stream.get("height"),
            "codec": stream.get("codec_name"), "duration": (result.get("format") or {}).get("duration"),
            "size": (result.get("format") or {}).get("size")}


def _write_once(path: Path, data: dict[str, Any]) -> None:
    if path.exists():
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if old != data:
            raise BacklotError(f"{path.name} is versioned; use a new id for changed content")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(tmp, path)


def prepare_assembly(project: Project, spec: dict[str, Any]) -> dict[str, Any]:
    record_id = str(spec.get("id") or "")
    _record_path(project, "edit/assemblies", record_id)
    route = str(spec.get("route") or "")
    if route not in ROUTES:
        raise BacklotError(f"assembly route must be one of {sorted(ROUTES)}")
    hash_memo: dict[Path, str] = {}
    verified: dict[tuple[str, str], dict[str, Any]] = {}

    def probe_once(ref: dict[str, Any]) -> dict[str, Any]:
        key = (ref["path"], ref["sha256"])
        if key not in verified:
            verified[key] = _video_probe(Path(ref["path"]))
        return verified[key]

    output = _reference(project, spec.get("output"), "assembly output", hash_memo)
    if not output.get("artifact"):
        raise BacklotError("assembly output needs a registered artifact id")
    probe = probe_once(output)
    recipe = _reference(project, spec.get("recipe"), "assembly recipe", hash_memo)
    segments = spec.get("segments")
    if not isinstance(segments, list) or not segments:
        raise BacklotError("assembly needs at least one source-to-output segment")
    checked = []
    for i, segment in enumerate(segments, 1):
        if not isinstance(segment, dict) or not segment.get("scene"):
            raise BacklotError(f"segment {i} needs a scene or story name")
        start, end = _range(segment.get("output_frames"), f"segment {i} output_frames")
        source = _reference(project, segment.get("source"), f"segment {i} source", hash_memo)
        source_probe = probe_once(source)
        source_frames = segment.get("source_frames")
        if source_frames is not None:
            _, source_end = _range(source_frames, f"segment {i} source_frames")
            if source_end >= source_probe["frames"]:
                raise BacklotError(f"segment {i} source_frames exceed source video")
        checked.append({**segment, "output_frames": [start, end], "source": source})
    checked.sort(key=lambda row: row["output_frames"][0])
    cursor = 0
    for segment in checked:
        if segment["output_frames"][0] != cursor:
            raise BacklotError(f"assembly coverage gap or overlap at output frame {cursor}")
        cursor = segment["output_frames"][1] + 1
    if cursor != probe["frames"]:
        raise BacklotError(f"assembly covers {cursor} frames; output has {probe['frames']}")
    attachments = [_reference(project, item, "assembly attachment", hash_memo)
                   for item in (spec.get("attachments") or [])]
    if len(attachments) != len(spec.get("attachments") or []):
        raise BacklotError("invalid assembly attachments")
    output_take = load_take(project, str(output["artifact"]))
    source_hashes = {str(ref.get("sha256") or "") for ref in output_take.source_refs}
    used_hashes = {str(item["source"]["sha256"]) for item in checked}
    used_hashes |= {str(item["sha256"]) for item in attachments}
    if not used_hashes <= source_hashes:
        raise BacklotError("assembly sources are missing from output artifact source_refs")
    return {**spec, "schema_version": 1, "id": record_id, "route": route,
            "output": output, "probe": probe, "recipe": recipe,
            "segments": checked, "attachments": attachments,
            "verified_probes": [{"path": path, "sha256": digest, "probe": facts}
                                for (path, digest), facts in verified.items()]}


def register_assembly(project: Project, spec: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    record = prepare_assembly(project, spec)
    if not dry_run:
        _write_once(_record_path(project, "edit/assemblies", record["id"]), record)
    return record


def load_assembly(project: Project, record_id: str) -> dict[str, Any]:
    path = _record_path(project, "edit/assemblies", record_id)
    if not path.is_file():
        raise BacklotError(f"assembly {record_id} missing")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def prepare_deliverable(project: Project, spec: dict[str, Any]) -> dict[str, Any]:
    if "historical_acceptance" in spec:
        raise BacklotError("historical acceptance must be imported separately and referenced by id")
    record_id = str(spec.get("id") or "")
    _record_path(project, "deliverables", record_id)
    kind = str(spec.get("kind") or "")
    if kind not in KINDS:
        raise BacklotError(f"deliverable kind must be one of {sorted(KINDS)}")
    assembly_id = str(spec.get("assembly") or "")
    assembly = load_assembly(project, assembly_id)
    output = _reference(project, spec.get("output"), "deliverable output")
    if not output.get("artifact"):
        raise BacklotError("deliverable output needs a registered artifact id")
    if output["sha256"] != (assembly.get("output") or {}).get("sha256"):
        raise BacklotError("deliverable output differs from assembly output")
    if not spec.get("approval_scope"):
        raise BacklotError("deliverable needs exact approval_scope")
    if spec.get("historical_acceptance_id"):
        acceptance = load_historical_acceptance(project, str(spec["historical_acceptance_id"]))
        if not historical_acceptance_matches(project, acceptance, spec):
            raise BacklotError("historical acceptance does not bind this exact deliverable version")
    return {**spec, "schema_version": 1, "id": record_id, "kind": kind,
            "assembly": assembly_id, "output": output}


def register_deliverable(project: Project, spec: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    record = prepare_deliverable(project, spec)
    if not dry_run:
        _write_once(_record_path(project, "deliverables", record["id"]), record)
    return record


def load_deliverable(project: Project, record_id: str) -> dict[str, Any]:
    path = _record_path(project, "deliverables", record_id)
    if not path.is_file():
        raise BacklotError(f"deliverable {record_id} missing")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_historical_acceptance(project: Project, record_id: str) -> dict[str, Any]:
    path = _record_path(project, "deliverables/historical-acceptances", record_id)
    if not path.is_file():
        raise BacklotError(f"historical acceptance {record_id} missing")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def historical_acceptance_matches(project: Project, acceptance: dict[str, Any],
                                  deliverable: dict[str, Any]) -> bool:
    """Bind a migrated approval to one old artifact, recipe and deliverable identity."""
    try:
        assembly = load_assembly(project, str(deliverable.get("assembly") or ""))
    except BacklotError:
        return False
    output = deliverable.get("output") or {}
    return (acceptance.get("deliverable") == deliverable.get("id") and
            acceptance.get("kind") == deliverable.get("kind") and
            acceptance.get("approval_scope") == deliverable.get("approval_scope") and
            acceptance.get("artifact") == output.get("artifact") and
            acceptance.get("sha256") == output.get("sha256") and
            acceptance.get("assembly") == deliverable.get("assembly") and
            acceptance.get("recipe_sha256") == (assembly.get("recipe") or {}).get("sha256"))


def import_historical_acceptance(project: Project, spec: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Import an existing final approval once; ordinary deliverable registration cannot create it."""
    record_id = str(spec.get("id") or "")
    path = _record_path(project, "deliverables/historical-acceptances", record_id)
    if path.exists():
        raise BacklotError(f"historical acceptance {record_id} is already imported")
    assembly_id = str(spec.get("assembly") or "")
    assembly = load_assembly(project, assembly_id)
    artifact = str(spec.get("artifact") or "")
    take = load_take(project, artifact)
    sha256 = str(spec.get("sha256") or "")
    if take.origin != "assembly" or not sha256 or take.sha256 != sha256:
        raise BacklotError("historical import needs an exact registered assembly artifact")
    _take_media(project, artifact)
    if (assembly.get("output") or {}).get("artifact") != artifact or (assembly.get("output") or {}).get("sha256") != sha256:
        raise BacklotError("historical import assembly does not bind the artifact")
    decision = next((row for row in list_decisions(project) if row.get("id") == spec.get("decision_id")), None)
    if not decision or decision.get("action") != "approve" or decision.get("source_kind") != "user":
        raise BacklotError("historical import needs a typed original user approval")
    if (decision.get("subject_type") != spec.get("kind") or
            decision.get("subject_id") != spec.get("deliverable") or
            decision.get("version") != sha256 or
            decision.get("scope") != spec.get("approval_scope") or
            decision.get("source_ref") != spec.get("source_ref") or
            decision.get("source_at") != spec.get("source_at")):
        raise BacklotError("historical decision subject, source or scope differs")
    try:
        original_at = datetime.fromisoformat(str(decision["source_at"]).replace("Z", "+00:00"))
        registered_at = datetime.fromisoformat(str(take.extra["registered_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError) as exc:
        raise BacklotError("historical import needs original approval time and registration time") from exc
    if original_at.tzinfo is None or registered_at.tzinfo is None or original_at >= registered_at:
        raise BacklotError("historical approval must predate artifact migration registration")
    evidence = _reference(project, spec.get("source_evidence"), "historical approval evidence")
    try:
        archived = json.loads(Path(evidence["path"]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BacklotError("historical approval evidence must be readable JSON") from exc
    if archived.get("output_sha256") != sha256 or archived.get("user_quote") != decision.get("source_message"):
        raise BacklotError("historical approval evidence differs from original user decision or output")
    covers = spec.get("covers")
    if not isinstance(covers, list) or not covers or any(not isinstance(x, str) or not x for x in covers):
        raise BacklotError("historical import needs named accepted requirement coverage")
    record = {**spec, "schema_version": 1, "id": record_id, "artifact": artifact,
              "sha256": sha256, "assembly": assembly_id,
              "recipe_sha256": (assembly.get("recipe") or {}).get("sha256"),
              "source_evidence": evidence, "covers": covers}
    if not dry_run:
        _write_once(path, record)
    return record


def _approved_ranges(project: Project, record: dict[str, Any], frames: int) -> tuple[list[tuple[int, int]], str | None]:
    kind, record_id = record["kind"], record["id"]
    expected = (record.get("output") or {}).get("sha256")
    matches = [row for row in list_decisions(project)
               if row.get("action") in ("approve", "reject")
               and row.get("subject_type") == kind and row.get("subject_id") == record_id
               and row.get("version") == expected and row.get("scope") == record.get("approval_scope")]
    if not matches:
        raise BacklotError("matching user approval missing")
    latest = matches[-1]
    if latest.get("action") != "approve" or latest.get("source_kind") != "user":
        raise BacklotError("matching decision is not a user approval")
    if not latest.get("source_ref") or not latest.get("source_message"):
        raise BacklotError("approval lacks original user message/reference")
    coverage = latest.get("coverage")
    if coverage is None:
        return [(0, frames - 1)], latest["id"]
    return [_range(item, "approval coverage") for item in coverage], latest["id"]


def _covered(ranges: list[tuple[int, int]], start: int, end: int) -> bool:
    cursor = start
    for low, high in sorted(ranges):
        if high < cursor:
            continue
        if low > cursor:
            return False
        cursor = max(cursor, high + 1)
        if cursor > end:
            return True
    return False


def inspect_deliverable(project: Project, record_id: str) -> dict[str, Any]:
    """Inspect existing records and media without changing any projection or approval."""
    blockers: list[str] = []
    scene_ranges: dict[str, list[list[int]]] = {}
    record: dict[str, Any] = {}
    assembly: dict[str, Any] = {}
    try:
        record = load_deliverable(project, record_id)
        assembly = load_assembly(project, str(record.get("assembly") or ""))
        hash_memo: dict[Path, str] = {}
        probes = {(row["path"], row["sha256"]): row["probe"]
                  for row in assembly.get("verified_probes") or []}

        def probe_once(ref: dict[str, Any]) -> dict[str, Any]:
            key = (ref["path"], ref["sha256"])
            if key not in probes:  # Legacy assembly: decode once per unique asset in this inspection.
                probes[key] = _video_probe(Path(ref["path"]))
            return probes[key]

        output = _reference(project, record.get("output"), "deliverable output", hash_memo)
        recorded_hash = (record.get("output") or {}).get("sha256")
        if output["sha256"] != recorded_hash:
            blockers.append("output SHA-256 differs from recorded version")
        if recorded_hash != (assembly.get("output") or {}).get("sha256"):
            blockers.append("assembly/output versions differ")
        probe = probe_once(output)
        if any(probe.get(key) != (assembly.get("probe") or {}).get(key)
               for key in ("frames", "fps", "width", "height")):
            blockers.append("output probe differs from registered assembly")
        frames = probe["frames"]
        recipe = _reference(project, assembly.get("recipe"), "assembly recipe", hash_memo)
        if recipe["sha256"] != (assembly.get("recipe") or {}).get("sha256"):
            blockers.append("assembly recipe changed")
        segments = assembly.get("segments") or []
        if not segments:
            blockers.append("assembly has no source coverage")
        cursor = 0
        for item in sorted(segments, key=lambda row: row["output_frames"][0]):
            start, end = _range(item.get("output_frames"), "assembly output_frames")
            if start != cursor:
                blockers.append(f"source coverage gap or overlap at output frame {cursor}")
            cursor = end + 1
            scene_ranges.setdefault(str(item.get("scene") or ""), []).append([start, end])
            source = _reference(project, item.get("source"), "assembly source", hash_memo)
            if source["sha256"] != (item.get("source") or {}).get("sha256"):
                blockers.append(f"{item.get('scene')}: source version changed")
            if item.get("source_frames") is not None:
                _, source_end = _range(item["source_frames"], "assembly source_frames")
                if source_end >= probe_once(source)["frames"]:
                    blockers.append(f"{item.get('scene')}: source_frames exceed source video")
        if cursor != frames:
            blockers.append(f"assembly covers {cursor} of {frames} output frames")
        for item in assembly.get("attachments") or []:
            found = _reference(project, item, "assembly attachment", hash_memo)
            if found["sha256"] != item.get("sha256"):
                blockers.append("assembly attachment version changed")
        output_take = load_take(project, str((record.get("output") or {}).get("artifact") or ""))
        declared_sources = {str(ref.get("sha256") or "") for ref in output_take.source_refs}
        used_sources = {str((item.get("source") or {}).get("sha256") or "") for item in segments}
        used_sources |= {str(item.get("sha256") or "") for item in assembly.get("attachments") or []}
        if not used_sources <= declared_sources:
            blockers.append("output artifact source_refs omit an assembly source")
        art_ids = {str((assembly.get("output") or {}).get("artifact") or "")}
        art_ids |= {str((item.get("source") or {}).get("artifact") or "") for item in segments}
        art_ids |= {str(item.get("artifact") or "") for item in assembly.get("attachments") or []}
        affected = set(lineage.check(project)["needs_review"])
        if changed := sorted((art_ids - {""}) & affected):
            blockers.append("registered source/output needs review: " + ", ".join(changed))
        approved, approval_id = _approved_ranges(project, record, frames)
        for scene, ranges in scene_ranges.items():
            for start, end in ranges:
                if not _covered(approved, start, end):
                    blockers.append(f"{scene}: user approval does not cover output frames {start}-{end}")
    except (BacklotError, KeyError, TypeError, ValueError) as exc:
        blockers.append(str(exc))
        approval_id = None
    return {"id": record_id, "kind": record.get("kind"), "output": record.get("output"),
            "assembly": record.get("assembly"), "approval_id": approval_id,
            "scene_ranges": scene_ranges, "blockers": blockers, "passed": not blockers}


def index_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# Deliverables", "", "Generated from exact deliverable records by `backlot delivery --refresh`.", "",
             "| Deliverable | Version | Approval | State |", "|---|---|---|---|"]
    for row in results:
        version = (row.get("output") or {}).get("sha256") or "missing"
        lines.append(f"| {row['id']} | `{version}` | {row.get('approval_id') or 'missing'} | {'ready' if row['passed'] else 'blocked'} |")
        for issue in row["blockers"]:
            lines.append(f"- {row['id']}: {issue}")
    return "\n".join(lines) + "\n"

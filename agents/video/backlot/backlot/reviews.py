"""Version-bound human review and no-spend repair records."""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from backlot import authority, decisions, takes
from backlot.errors import BacklotError
from backlot.project import Project

SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RESULTS = {"pass", "fail", "pending", "unsupported"}
_COVERAGE = {"full_playback", "sampled", "technical_only"}


def _dir(project: Project, name: str) -> Path:
    return project.vault_project / "Records" / name


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(temp, path)


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BacklotError(f"record not found: {path.name}")
    row = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(row, dict) or row.get("schema_version") != SCHEMA_VERSION:
        raise BacklotError(f"unsupported review record: {path.name}")
    return row


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BacklotError(f"{label} is required")
    return value.strip()


def _time(value: Any, label: str) -> str:
    raw = _text(value, label)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BacklotError(f"{label} needs an ISO timestamp with timezone") from exc
    if parsed.tzinfo is None:
        raise BacklotError(f"{label} needs an ISO timestamp with timezone")
    return parsed.isoformat()


def _source(data: Any, label: str) -> dict[str, str]:
    if not isinstance(data, dict):
        raise BacklotError(f"{label} source evidence is required")
    return {"kind": _text(data.get("kind"), f"{label} source kind"),
            "ref": _text(data.get("ref"), f"{label} source ref"),
            "observed_at": _time(data.get("observed_at"), f"{label} source timestamp")}


def _sha(value: Any, label: str) -> str:
    digest = _text(value, label).lower()
    if not _SHA256.fullmatch(digest):
        raise BacklotError(f"{label} must be a 64-character SHA-256")
    return digest


def _subject(project: Project, data: Any) -> tuple[dict[str, str], Path, takes.Take | None]:
    if not isinstance(data, dict):
        raise BacklotError("subject needs kind, id and sha256")
    kind, subject_id = _text(data.get("kind"), "subject kind"), _text(data.get("id"), "subject id")
    expected = _sha(data.get("sha256"), "subject sha256")
    take = None
    if kind == "take":
        take = takes.load_take(project, subject_id)
        if not take.file:
            raise BacklotError(f"take {subject_id} has no media file to review")
        path = takes.take_file(project, subject_id)
        if take.sha256 and take.sha256 != expected:
            raise BacklotError(f"subject hash differs from recorded take version: {subject_id}")
    elif kind == "render":
        raw = Path(subject_id).expanduser()
        path = (raw if raw.is_absolute() else project.root / raw
                if raw.parts and raw.parts[0] == "renders" else project.renders_dir / raw).resolve()
        try:
            subject_id = path.relative_to(project.root.resolve()).as_posix()
            path.relative_to(project.renders_dir.resolve())
        except ValueError as exc:
            raise BacklotError("render subject must be inside this project's renders/ directory") from exc
    else:
        raise BacklotError("subject kind must be take or render")
    if not path.is_file():
        raise BacklotError(f"subject media missing: {path}")
    actual = authority.file_hash(path)
    if actual != expected:
        raise BacklotError(f"subject bytes do not match declared SHA-256: {subject_id}")
    return {"kind": kind, "id": subject_id, "sha256": actual}, path, take


def _criteria(data: Any, label: str, *, context: bool = False) -> tuple[list[dict[str, Any]], str, str | None]:
    if not isinstance(data, dict) or not isinstance(data.get("criteria") or [], list):
        raise BacklotError(f"{label} review and criteria list are required")
    rows, cleaned, seen = data.get("criteria") or [], [], set()
    for item in rows:
        if not isinstance(item, dict):
            raise BacklotError(f"{label} criterion must be an object")
        cid = _text(item.get("id"), f"{label} criterion id")
        if cid in seen:
            raise BacklotError(f"duplicate {label} criterion id {cid}")
        seen.add(cid)
        result = str(item.get("result") or "")
        if result not in _RESULTS:
            raise BacklotError(f"{label} criterion {cid} result must be one of {sorted(_RESULTS)}")
        times, refs = item.get("timecodes") or [], item.get("evidence") or []
        if isinstance(refs, str):
            refs = [refs]
        if not isinstance(times, list) or not all(isinstance(v, str) and v.strip() for v in times):
            raise BacklotError(f"{label} criterion {cid} timecodes must be non-empty strings")
        if not isinstance(refs, list) or not all(isinstance(v, str) and v.strip() for v in refs):
            raise BacklotError(f"{label} criterion {cid} evidence must be references")
        if result in ("pass", "fail") and not (times or refs):
            raise BacklotError(f"{label} criterion {cid} needs timecode or evidence")
        why = _text(item.get("reason"), f"{label} criterion {cid} reason") if result == "unsupported" else item.get("reason")
        row = {"id": cid, "name": _text(item.get("name"), f"{label} criterion name"),
               "result": result, "timecodes": [v.strip() for v in times],
               "evidence": [v.strip() for v in refs]}
        if why:
            row["reason"] = str(why)
        cleaned.append(row)
    if not rows:
        status = str(data.get("status") or "unsupported")
        allowed = {"pending", "unsupported", "not_applicable"} if context else {"pending", "unsupported"}
        if status not in allowed:
            raise BacklotError(f"{label} without criteria must be one of {sorted(allowed)}")
        return [], status, _text(data.get("reason"), f"{label} reason")
    results = [row["result"] for row in cleaned]
    status = ("fail" if "fail" in results else "pending" if "pending" in results else
              "unsupported" if "unsupported" in results else "pass")
    if data.get("status") and data["status"] != status:
        raise BacklotError(f"{label} status {data['status']!r} conflicts with its criteria ({status})")
    return cleaned, status, None


def _technical(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("checks"), list) or not data["checks"]:
        raise BacklotError("technical review needs one or more checks")
    checks = []
    for item in data["checks"]:
        if not isinstance(item, dict):
            raise BacklotError("technical check must be an object")
        name, result = _text(item.get("name"), "technical check name"), str(item.get("result") or "")
        if result not in _RESULTS:
            raise BacklotError(f"technical check {name} result must be one of {sorted(_RESULTS)}")
        refs = item.get("evidence") or []
        refs = [refs] if isinstance(refs, str) else refs
        if not isinstance(refs, list) or not all(isinstance(v, str) and v.strip() for v in refs):
            raise BacklotError(f"technical check {name} evidence must be references")
        if result in ("pass", "fail") and not refs:
            raise BacklotError(f"technical check {name} needs evidence")
        checks.append({"name": name, "result": result, "evidence": [v.strip() for v in refs]})
    states = [row["result"] for row in checks]
    status = "fail" if "fail" in states else "pending" if "pending" in states else \
        "unsupported" if "unsupported" in states else "pass"
    return {"status": status, "checks": checks}


def _coverage(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("mode") not in _COVERAGE:
        raise BacklotError(f"coverage mode must be one of {sorted(_COVERAGE)}")
    mode, ranges = data["mode"], data.get("ranges") or []
    if not isinstance(ranges, list):
        raise BacklotError("coverage ranges must be a list")
    cleaned = []
    for row in ranges:
        if not isinstance(row, dict):
            raise BacklotError("coverage range must be an object")
        try:
            start, end = float(row["start_s"]), float(row["end_s"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BacklotError("coverage range needs numeric start_s and end_s") from exc
        if start < 0 or end < start:
            raise BacklotError("coverage range must be non-negative and ordered")
        cleaned.append({"start_s": start, "end_s": end})
    if mode == "sampled" and not cleaned:
        raise BacklotError("sampled review needs the sampled time ranges")
    if mode == "technical_only" and cleaned:
        raise BacklotError("technical-only review cannot claim playback ranges")
    return {"mode": mode, "ranges": cleaned}


def _presentation(data: Any) -> dict[str, Any]:
    if data is None:
        return {"status": "not_presented"}
    if not isinstance(data, dict) or data.get("status") != "presented":
        raise BacklotError("presentation must record `presented` with source evidence")
    return {"status": "presented", **_source(data, "presentation")}


def _listening(data: Any) -> dict[str, Any]:
    if data is None:
        return {"status": "unsupported", "criteria": [], "reason": "listening review not supplied"}
    rows, status, reason = _criteria(data, "listening", context=True)
    return {"status": status, "criteria": rows, **({"reason": reason} if reason else {})}


def _accepted_limits(project: Project, subject: dict[str, str], rows: Any) -> list[dict[str, str]]:
    if rows is None:
        rows = []
    if not isinstance(rows, list):
        raise BacklotError("accepted_limits must be decision references")
    known = {r["id"]: r for r in decisions.list_decisions(project)
             if r.get("action") == "accept-limit" and r.get("subject_id") == subject["id"]
             and r.get("version") == subject["sha256"]}
    mapped = {}
    for item in rows:
        if not isinstance(item, dict):
            raise BacklotError("accepted limit needs criterion_id and decision_id")
        did = _text(item.get("decision_id"), "accepted-limit decision id")
        if did not in known:
            raise BacklotError(f"accepted limit {did} is not sourced for this subject version")
        mapped[did] = _text(item.get("criterion_id"), "accepted-limit criterion id")
    folder = _dir(project, "reviews")
    if folder.is_dir():
        for path in folder.glob("review-*.yaml"):
            old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if old.get("subject") == subject:
                for row in old.get("accepted_limits") or []:
                    if row.get("decision_id") in known:
                        mapped.setdefault(row["decision_id"], row["criterion_id"])
    return [{"criterion_id": cid, "decision_id": did,
             "scope": str(known[did].get("scope") or ""),
             "reason": str(known[did].get("reason") or ""),
             "source_ref": str(known[did].get("source_ref") or ""),
             "recorded_at": str(known[did].get("recorded_at") or "")}
            for did, cid in mapped.items()]


def _record_path(project: Project, category: str, record_id: str, prefix: str) -> Path:
    if not re.fullmatch(rf"{prefix}-[0-9a-f]{{32}}", record_id):
        raise BacklotError(f"invalid {prefix} id {record_id!r}")
    return _dir(project, category) / f"{record_id}.yaml"


def load_review(project: Project, review_id: str) -> dict[str, Any]:
    return _read(_record_path(project, "reviews", review_id, "review"))


def register_review(project: Project, spec: dict[str, Any]) -> dict[str, Any]:
    """Record technical and human findings without mutating approval or take status."""
    if not isinstance(spec, dict):
        raise BacklotError("review spec must be a mapping")
    if "user_decision" in spec:
        raise BacklotError("subjective decisions belong in Decisions records, not review records")
    source = _source(spec.get("source"), "review")
    subject, _, _ = _subject(project, spec.get("subject"))
    coverage, technical = _coverage(spec.get("coverage")), _technical(spec.get("technical"))
    semantic, sem_status, sem_reason = _criteria(spec.get("semantic"), "semantic")
    context, ctx_status, ctx_reason = _criteria(spec.get("context"), "context", context=True)
    listening_spec = spec.get("listening")
    listening = _listening(listening_spec)
    listening_status = listening["status"]
    listening_required = listening_spec is not None and listening_status != "not_applicable"
    if coverage["mode"] == "technical_only" and sem_status == "pass":
        raise BacklotError("technical-only evidence cannot establish a semantic pass")
    if (technical["status"] == "fail" or sem_status == "fail" or ctx_status == "fail" or
            (listening_required and listening_status == "fail")):
        outcome = "fail"
    elif listening_required and listening_status != "pass":
        outcome = "pending"
    elif (technical["status"] == "pass" and sem_status == "pass" and
          ctx_status in ("pass", "not_applicable") and
          (not listening_required or listening_status == "pass") and
          coverage["mode"] != "technical_only"):
        outcome = "pass" if coverage["mode"] == "full_playback" else "pass_limited"
    elif technical["status"] == "pass" and coverage["mode"] == "technical_only":
        outcome = "technical_only"
    else:
        outcome = "pending"
    record_id = f"review-{uuid.uuid4().hex}"
    record = {"schema_version": SCHEMA_VERSION, "id": record_id, "subject": subject, "source": source,
              "coverage": coverage, "technical": technical,
              "semantic": {"status": sem_status, "criteria": semantic, **({"reason": sem_reason} if sem_reason else {})},
              "context": {"status": ctx_status, "criteria": context, **({"reason": ctx_reason} if ctx_reason else {})},
              "listening": listening,
              "presentation": _presentation(spec.get("presentation")),
              "accepted_limits": _accepted_limits(project, subject, spec.get("accepted_limits")),
              "outcome": outcome, "recorded_at": datetime.now(timezone.utc).isoformat()}
    _write(_record_path(project, "reviews", record_id, "review"), record)
    return record


def _criteria_index(review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: {**row, "layer": layer}
            for layer in ("semantic", "context")
            for row in review.get(layer, {}).get("criteria") or []}


def _reopens(rows: Any, accepted: list[dict[str, str]]) -> list[dict[str, str]]:
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise BacklotError("reopen_limits must be a list")
    known = {row["decision_id"]: row for row in accepted}
    reopened = []
    for item in rows:
        if not isinstance(item, dict):
            raise BacklotError("reopen limit needs a sourced user instruction")
        did = _text(item.get("decision_id"), "reopened decision id")
        old = known.get(did)
        if not old:
            raise BacklotError(f"cannot reopen unknown accepted-limit decision {did}")
        src = _source({"kind": item.get("source_kind"), "ref": item.get("source_ref"),
                       "observed_at": item.get("observed_at")}, "limit reopening")
        if src["kind"] != "user_message":
            raise BacklotError("reopening an accepted limit needs a user_message source")
        reopened.append({"decision_id": did, "criterion_id": old["criterion_id"], **src,
                         "source_message": _text(item.get("source_message"), "reopening message")})
    return reopened


def _changes(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        raise BacklotError("repair plan needs explicit changed inputs or operations")
    result = []
    for row in rows:
        if not isinstance(row, dict) or "before" not in row or "after" not in row:
            raise BacklotError("each repair change needs field, before and after values")
        result.append({"field": _text(row.get("field"), "repair change field"), "before": row["before"],
                       "after": row["after"], "reason": _text(row.get("reason"), "repair change reason")})
    return result


def load_repair(project: Project, repair_id: str) -> dict[str, Any]:
    return _read(_record_path(project, "repairs", repair_id, "repair"))


def plan_repair(project: Project, spec: dict[str, Any]) -> dict[str, Any]:
    """Persist a no-spend repair plan from a presented review and unchanged parent bytes."""
    if not isinstance(spec, dict):
        raise BacklotError("repair spec must be a mapping")
    review = load_review(project, _text(spec.get("parent_review_id"), "parent review id"))
    if review["presentation"].get("status") != "presented":
        raise BacklotError("present the first-pass review with source evidence before proposing a repair")
    parent, _, take = _subject(project, review["subject"])
    kind = str(spec.get("repair_kind") or "")
    if kind not in {"provider_job", "local_edit", "external_edit"}:
        raise BacklotError("repair_kind must be provider_job, local_edit or external_edit")
    changes, index = _changes(spec.get("changes")), _criteria_index(review)
    targets = spec.get("target_criteria") or []
    if not isinstance(targets, list) or not targets or not all(isinstance(v, str) and v.strip() for v in targets):
        raise BacklotError("repair plan needs named target_criteria from the presented review")
    targets = [v.strip() for v in targets]
    if any(cid not in index for cid in targets):
        raise BacklotError("repair target is absent from the parent review")
    if any(index[cid]["result"] not in ("fail", "pending", "unsupported") for cid in targets):
        raise BacklotError("repair target must be a failed, pending or unsupported criterion")
    accepted = [r for r in review.get("accepted_limits") or [] if r["criterion_id"] in targets]
    reopened = _reopens(spec.get("reopen_limits"), accepted)
    reopened_ids = {r["decision_id"] for r in reopened}
    closed = [r for r in accepted if r["decision_id"] not in reopened_ids]
    if closed:
        raise BacklotError("repair target is an accepted limitation; explicit sourced user reopening required")
    source = _source(spec.get("source"), "repair plan")
    if take:
        original, effective, refs = take.original_request, take.effective_request, take.source_refs
    else:
        manifest = spec.get("parent_manifest")
        if not isinstance(manifest, dict):
            raise BacklotError("render repair needs its exact parent request/source manifest")
        original, effective, refs = manifest.get("original_request"), manifest.get("effective_request"), manifest.get("source_refs")
        if not isinstance(original, dict) or not isinstance(effective, dict) or not isinstance(refs, list):
            raise BacklotError("parent_manifest needs original_request, effective_request and source_refs")
    if kind == "provider_job" and (not original or not effective):
        raise BacklotError("provider repair needs the parent's exact original and effective request")
    if not isinstance(refs, list):
        raise BacklotError("parent source_refs must be a list")
    repair_id = f"repair-{uuid.uuid4().hex}"
    record = {"schema_version": SCHEMA_VERSION, "id": repair_id, "state": "planned",
              "parent_review_id": review["id"], "parent": parent,
              "request_manifest": {"original_request": original or {}, "effective_request": effective or {},
                                   "source_refs": refs},
              "inherited_controls": dict(effective) if isinstance(effective, dict) else {},
              "changes": changes, "target_criteria": targets,
              "inherited_accepted_limits": review.get("accepted_limits") or [], "reopened_limits": reopened,
              "source": source, "provider_call_submitted": False,
              "created_at": datetime.now(timezone.utc).isoformat()}
    _write(_record_path(project, "repairs", repair_id, "repair"), record)
    return record


def record_repair_result(project: Project, spec: dict[str, Any]) -> dict[str, Any]:
    """Record output evidence and human findings; job completion does not imply semantic success."""
    if not isinstance(spec, dict):
        raise BacklotError("repair result spec must be a mapping")
    plan = load_repair(project, _text(spec.get("repair_id"), "repair id"))
    parent, _, _ = _subject(project, plan["parent"])
    source = _source(spec.get("source"), "repair result")
    job = str(spec.get("job_status") or "")
    if job not in {"completed", "failed", "pending", "not_applicable"}:
        raise BacklotError("job_status must be completed, failed, pending or not_applicable")
    reported = str(spec.get("target_outcome") or "")
    if reported not in {"effective", "ineffective", "pending", "context_fail"}:
        raise BacklotError("invalid target_outcome")
    context = spec.get("context") or {"status": "pending", "reason": "context not reviewed yet", "criteria": []}
    ctx_rows, ctx_status, ctx_reason = _criteria(context, "repair context", context=True)
    out, identical = None, False
    if spec.get("output") is not None:
        out, _, _ = _subject(project, spec["output"])
        identical = out["sha256"] == parent["sha256"]
    elif job == "completed":
        raise BacklotError("completed repair result needs exact output path and hash")
    if reported == "effective" and out is None:
        raise BacklotError("effective repair result needs an exact output path and hash")
    target_spec = spec.get("target_review") or {"status": "pending", "reason": "target not reviewed yet"}
    target_rows, target_status, target_reason = _criteria(target_spec, "repair target")
    if target_rows and any(cid not in {r["id"] for r in target_rows} for cid in plan["target_criteria"]):
        raise BacklotError("repair result omits a targeted criterion")
    if identical:
        if reported == "effective":
            raise BacklotError("byte-identical output cannot be recorded as an effective repair")
        outcome = "ineffective"
    elif ctx_status == "fail" or reported == "context_fail":
        outcome = "context_fail"
    elif job == "failed":
        outcome = "pending" if reported == "pending" else "ineffective"
    elif target_status == "fail" or reported == "ineffective":
        outcome = "ineffective"
    elif job == "pending" or target_status in ("pending", "unsupported") or reported == "pending":
        outcome = "pending"
    elif reported == "effective" and target_status == "pass" and ctx_status in ("pass", "not_applicable"):
        outcome = "effective"
    else:
        outcome = "pending"
    failure, cause = None, None
    if job == "failed":
        raw = spec.get("failure")
        if isinstance(raw, dict) and raw.get("message") and raw.get("evidence_ref"):
            failure = {"message": str(raw["message"]), "evidence_ref": str(raw["evidence_ref"])}
            cause = failure["message"]
        else:
            cause = "failed; cause unavailable"
    result_id = f"repair-result-{uuid.uuid4().hex}"
    record = {"schema_version": SCHEMA_VERSION, "id": result_id, "repair_id": plan["id"],
              "parent": parent, "job_status": job, "output": out, "byte_identical_to_parent": identical,
              "target_outcome_reported": reported, "outcome": outcome,
              "target_review": {"status": target_status, "criteria": target_rows,
                                **({"reason": target_reason} if target_reason else {})},
              "context": {"status": ctx_status, "criteria": ctx_rows,
                          **({"reason": ctx_reason} if ctx_reason else {})},
              "failure": failure, "failure_cause": cause, "source": source,
              "recorded_at": datetime.now(timezone.utc).isoformat(), "approval_changed": False}
    _write(_dir(project, "repair-results") / f"{result_id}.yaml", record)
    return record

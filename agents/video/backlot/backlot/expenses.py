"""One native-unit expense record per provider operation; never infer a receipt from a quote."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from backlot.errors import BacklotError
from backlot.project import Project
from backlot.takes import _write_yaml, locked

SCHEMA_VERSION = 1
CHARGE_STATES = {"charged", "zero", "unknown"}


def expense_dir(project: Project) -> Path:
    return project.vault_project / "Records" / "expenses"


def _id(provider: str, operation_id: str | None, evidence_key: str | None, source_kind: str) -> str:
    # A generated reservation keeps the same identity if its provider later supplies a job id.
    key = (evidence_key or operation_id) if source_kind == "generated" else (operation_id or evidence_key)
    if not provider or not key:
        raise BacklotError("expense needs provider and operation_id or evidence_key")
    return "expense-" + hashlib.sha256(f"{provider}\0{key}".encode()).hexdigest()[:24]


def _money(value: Any, label: str, *, nullable: bool = False) -> dict[str, Any] | None:
    if value is None and nullable:
        return None
    if not isinstance(value, dict) or not value.get("unit") or value.get("amount") is None:
        raise BacklotError(f"{label} needs amount and native unit")
    try:
        amount = float(value["amount"])
    except (TypeError, ValueError) as exc:
        raise BacklotError(f"{label} amount must be numeric") from exc
    if amount < 0 or not math.isfinite(amount):
        raise BacklotError(f"{label} amount must be finite and non-negative")
    return {**value, "amount": amount, "unit": str(value["unit"])}


def normalize(spec: dict[str, Any]) -> dict[str, Any]:
    provider = str(spec.get("provider") or "").strip()
    operation_id = str(spec["operation_id"]).strip() if spec.get("operation_id") else None
    evidence_key = str(spec["evidence_key"]).strip() if spec.get("evidence_key") else None
    state = str(spec.get("charge_status") or "unknown")
    if state not in CHARGE_STATES:
        raise BacklotError("charge_status must be charged, zero or unknown")
    estimate = _money(spec.get("estimate"), "estimate", nullable=True)
    charge = _money(spec.get("charge"), "charge", nullable=True)
    ledger = _money(spec.get("project_ledger"), "project_ledger", nullable=True)
    if state == "unknown" and charge is not None:
        raise BacklotError("unknown actual charge must have no amount")
    if state == "charged" and charge is None:
        raise BacklotError("charged operation needs native charge amount and unit")
    if state == "zero" and (charge is None or charge["amount"] != 0):
        raise BacklotError("known zero charge needs amount 0 and its native unit")
    if estimate and charge and estimate["unit"] != charge["unit"]:
        raise BacklotError("native estimate and charge units disagree")
    allocation = str(spec.get("allocation") or "unallocated")
    if allocation not in {"current_final", "experiment", "unallocated"}:
        raise BacklotError("allocation must be current_final, experiment or unallocated")
    observations = spec.get("balance_observations") or []
    if not isinstance(observations, list):
        raise BacklotError("balance_observations must be a list")
    for item in observations:
        if not isinstance(item, dict) or not all(item.get(k) is not None for k in ("amount", "unit", "source", "observed_at")):
            raise BacklotError("each balance observation needs amount, unit, source and observed_at")
        _money(item, "balance observation")
        try:
            stamp = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00"))
        except ValueError as exc:
            raise BacklotError("balance observation needs ISO timestamp with timezone") from exc
        if stamp.tzinfo is None:
            raise BacklotError("balance observation needs ISO timestamp with timezone")
    return {
        **spec, "schema_version": SCHEMA_VERSION,
        "id": _id(provider, operation_id, evidence_key, str(spec.get("source_kind") or "legacy")), "provider": provider,
        "operation_id": operation_id, "evidence_key": evidence_key,
        "charge_status": state, "estimate": estimate, "charge": charge,
        "project_ledger": ledger, "allocation": allocation,
        "balance_observations": observations,
        "source_kind": spec.get("source_kind") or "legacy",
    }


def find_unlocked(project: Project, record: dict[str, Any], *, linked_id: str | None = None) -> dict[str, Any] | None:
    """Find an existing expense before a registration mutates its take."""
    if linked_id:
        path = expense_dir(project) / f"{linked_id}.yaml"
        if not path.exists():
            raise BacklotError(f"linked expense {linked_id} not found")
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if old.get("provider") != record["provider"]:
            raise BacklotError(f"expense {linked_id} has another provider")
        if old.get("operation_id") and record.get("operation_id") and old["operation_id"] != record["operation_id"]:
            raise BacklotError(f"expense {linked_id} has another operation id")
        return old
    path = expense_dir(project) / f"{record['id']}.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if record.get("source_kind") == "generated" or not record.get("operation_id"):
        return None
    matches = [item for item in list_expenses(project)
               if item.get("provider") == record["provider"] and item.get("operation_id") == record["operation_id"]]
    if len(matches) > 1:
        raise BacklotError(f"provider operation {record['operation_id']} has multiple expense records")
    return matches[0] if matches else None


def upsert_unlocked(project: Project, spec: dict[str, Any], *, linked_id: str | None = None) -> dict[str, Any]:
    """Caller holds takes/.lock when a take and its expense are registered together."""
    record = normalize(spec)
    old = find_unlocked(project, record, linked_id=linked_id)
    if old:
        merged = dict(old)
        if old.get("operation_id") != record.get("operation_id"):
            if old.get("operation_id") and record.get("operation_id"):
                raise BacklotError(f"expense {old['id']} already exists with another operation id")
            if record.get("operation_id"):
                merged["operation_id"] = record["operation_id"]
        prior_state, next_state = old.get("charge_status"), record.get("charge_status")
        if prior_state != next_state:
            if prior_state != "unknown" or next_state == "unknown" or not (
                record.get("source_ref") or (record.get("charge") or {}).get("evidence")):
                raise BacklotError(f"expense {old['id']} charge status conflicts without actual-charge evidence")
            merged["charge_status"] = next_state
            merged["charge"] = record["charge"]
            merged["charge_source_ref"] = record.get("source_ref") or record["charge"].get("evidence")
        elif record.get("charge") is not None and old.get("charge") != record["charge"]:
            raise BacklotError(f"expense {old['id']} already exists with a different charge")
        incoming_estimate = record.get("estimate")
        if incoming_estimate and old.get("estimate") != incoming_estimate:
            prior_estimate = old.get("estimate")
            if prior_estimate and prior_estimate.get("basis") != "project budget quote":
                raise BacklotError(f"expense {old['id']} already exists with a different estimate")
            if prior_estimate:
                merged["budget_quote"] = prior_estimate
            merged["estimate"] = incoming_estimate
        incoming_ledger = record.get("project_ledger")
        prior_ledger = old.get("project_ledger")
        if incoming_ledger and prior_ledger and any(
            prior_ledger.get(key) != incoming_ledger.get(key) for key in ("amount", "unit")):
            raise BacklotError(f"expense {old['id']} already exists with a different EUR project ledger")
        if incoming_ledger and not prior_ledger:
            merged["project_ledger"] = incoming_ledger
        observations = list(old.get("balance_observations") or [])
        for item in record["balance_observations"]:
            if item not in observations:
                observations.append(item)
        merged["balance_observations"] = observations
        if merged != old:
            _write_yaml(expense_dir(project) / f"{old['id']}.yaml", merged)
        return merged
    path = expense_dir(project) / f"{record['id']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_yaml(path, record)
    return record


def register(project: Project, spec: dict[str, Any]) -> dict[str, Any]:
    with locked(project):
        return upsert_unlocked(project, spec)


def link_operation(project: Project, expense_id: str, operation_id: str) -> None:
    """Attach a recovered provider job id to its existing generated reservation."""
    with locked(project):
        path = expense_dir(project) / f"{expense_id}.yaml"
        if not path.exists():
            raise BacklotError(f"expense {expense_id} not found")
        record = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if record.get("source_kind") != "generated":
            raise BacklotError(f"expense {expense_id} is not a generated operation")
        if record.get("operation_id") == operation_id:
            return
        if record.get("operation_id"):
            raise BacklotError(f"expense {expense_id} already links another operation")
        record["operation_id"] = operation_id
        _write_yaml(path, record)


def allocate(project: Project, expense_id: str, allocation: str, *, source_ref: str, reason: str) -> dict[str, Any]:
    """Reclassify use of sunk spend without changing the charge or budget amount."""
    if allocation not in {"current_final", "experiment", "unallocated"} or not source_ref or not reason:
        raise BacklotError("allocation needs a valid use, evidence reference and reason")
    if not expense_id.startswith("expense-") or not all(c in "0123456789abcdef" for c in expense_id[8:]):
        raise BacklotError("invalid expense id")
    with locked(project):
        path = expense_dir(project) / f"{expense_id}.yaml"
        if not path.exists():
            raise BacklotError(f"expense {expense_id} not found")
        record = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if record.get("allocation") == allocation and record.get("allocation_source") == {"source_ref": source_ref, "reason": reason}:
            return record
        record["allocation"] = allocation
        record["allocation_source"] = {"source_ref": source_ref, "reason": reason}
        _write_yaml(path, record)
        return record


def list_expenses(project: Project) -> list[dict[str, Any]]:
    folder = expense_dir(project)
    return [yaml.safe_load(p.read_text(encoding="utf-8")) or {} for p in sorted(folder.glob("expense-*.yaml"))] if folder.is_dir() else []


def summary(project: Project) -> dict[str, Any]:
    """Native charges only. EUR project budget comes from take costs and is separate."""
    totals: dict[str, float] = {}
    allocated: dict[str, float] = {}
    unknown = 0
    for record in list_expenses(project):
        if record.get("charge_status") == "unknown":
            unknown += 1
            continue
        charge = record.get("charge") or {}
        unit = str(charge.get("unit"))
        totals[unit] = round(totals.get(unit, 0) + float(charge.get("amount") or 0), 4)
        if record.get("allocation") == "current_final":
            allocated[unit] = round(allocated.get(unit, 0) + float(charge.get("amount") or 0), 4)
    return {"native_charged": totals, "unknown_actual_charges": unknown,
            "current_final_native_allocation": allocated,
            "coverage": "registered operations only; excludes unregistered jobs and shared-account use"}

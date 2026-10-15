"""Exact, one-use authorization for paid provider operations.

The CLI records the user's message as evidence; a command flag is never evidence of consent.
Balance observations are supplied by the operator because provider balance APIs are not universal.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import shutil
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import yaml

from backlot.errors import EXIT_CONFIRM, BacklotError
from backlot.models import ModelSpec
from backlot.project import Project
from backlot.providers.base import GenRequest, build_arguments
from backlot.providers.base import ProviderPreSubmitError

SCHEMA_VERSION = 1


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quote(model: ModelSpec, req: GenRequest, *, cost_eur: float, shot: str | None = None,
          parent: str | None = None, depends_on: list[str] | None = None,
          override_max_call: bool = False) -> dict[str, Any]:
    """Fingerprint the effective provider arguments, including ordered input contents."""
    if not math.isfinite(cost_eur) or cost_eur < 0:
        raise BacklotError("provider estimate must be a finite non-negative amount")
    media = {
        name: [{"sha256": file_hash(path), "name": path.name} for path in req.media(name)]
        for name in ("image", "audio", "video")
    }
    media["end_image"] = ([{"sha256": file_hash(req.end_image), "name": req.end_image.name}]
                          if req.end_image else [])
    arguments = build_arguments(model, req, lambda path: f"sha256:{file_hash(path)}")
    request = {
        "provider": model.provider, "model": model.id, "route": model.endpoint,
        "kind": model.kind, "arguments": arguments, "media": media,
        "shot": shot, "parent": parent, "depends_on": sorted(depends_on or []),
        "override_max_call": override_max_call,
        "estimate": {"amount": round(cost_eur, 4), "unit": "EUR"},
    }
    return {"schema_version": SCHEMA_VERSION, "request": request,
            "fingerprint": hashlib.sha256(_canonical(request)).hexdigest(),
            "balance": {"status": "unavailable", "detail": "no common provider balance API configured"}}


def spend_dir(project: Project) -> Path:
    return project.vault_project / "Records" / "spend"


@contextmanager
def _locked(project: Project) -> Iterator[None]:
    folder = spend_dir(project)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / ".lock").open("a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _path(project: Project, auth_id: str) -> Path:
    if not auth_id.startswith("auth-") or not all(c in "0123456789abcdef" for c in auth_id[5:]):
        raise BacklotError("invalid authorization ID")
    return spend_dir(project) / f"{auth_id}.yaml"


def _read(project: Project, auth_id: str) -> dict[str, Any]:
    path = _path(project, auth_id)
    if not path.is_file():
        raise BacklotError(f"authorization {auth_id} not found", code=EXIT_CONFIRM)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write(project: Project, record: dict[str, Any]) -> None:
    path = _path(project, record["id"])
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(tmp, path)


def authorize(project: Project, quoted: dict[str, Any], *, source_message: str, source_ref: str,
              balance_amount: float | None, balance_unit: str | None, balance_source: str | None,
              expires_at: str) -> dict[str, Any]:
    if not source_message.strip() or not source_ref.strip():
        raise BacklotError("explicit user message and source reference are required; --yes is not approval")
    request = quoted.get("request") or {}
    if quoted.get("schema_version") != SCHEMA_VERSION or not request or quoted.get("fingerprint") != hashlib.sha256(_canonical(request)).hexdigest():
        raise BacklotError("invalid or altered quote")
    cost = request.get("estimate") or {}
    if float(cost.get("amount", -1)) <= 0:
        raise BacklotError("free operations do not need spend authorization")
    if balance_amount is None or not balance_unit or not balance_source:
        raise BacklotError("current provider balance amount, unit and source are required; unavailable is not zero")
    if not math.isfinite(balance_amount) or balance_amount < 0:
        raise BacklotError("balance must be a finite non-negative amount")
    if balance_unit.upper() == "EUR" and balance_amount < float(cost["amount"]):
        raise BacklotError("observed EUR balance is below the quoted call cost")
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BacklotError("--expires needs an ISO timestamp with timezone") from exc
    if expiry.tzinfo is None or expiry <= _now():
        raise BacklotError("authorization expiry must be in the future and include a timezone")
    record = {
        "schema_version": SCHEMA_VERSION, "id": f"auth-{uuid.uuid4().hex}",
        "project": project.slug, "state": "available", "fingerprint": quoted["fingerprint"],
        "request": request, "source_message": source_message.strip(), "source_ref": source_ref.strip(),
        "authorized_at": _now().isoformat(), "expires_at": expiry.isoformat(),
        "balance": {"amount": balance_amount, "unit": balance_unit, "source": balance_source,
                    "observed_at": _now().isoformat()},
    }
    with _locked(project):
        _write(project, record)
    return record


def reserve(project: Project, auth_id: str, quoted: dict[str, Any]) -> dict[str, Any]:
    with _locked(project):
        record = _read(project, auth_id)
        if record.get("schema_version") != SCHEMA_VERSION or record.get("project") != project.slug:
            raise BacklotError("authorization schema or project mismatch", code=EXIT_CONFIRM)
        if record.get("state") != "available":
            raise BacklotError(f"authorization {auth_id} is {record.get('state')}; it cannot be reused", code=EXIT_CONFIRM)
        try:
            expiry = datetime.fromisoformat(str(record["expires_at"]).replace("Z", "+00:00"))
        except (KeyError, ValueError) as exc:
            raise BacklotError("authorization has no valid expiry", code=EXIT_CONFIRM) from exc
        if expiry <= _now():
            raise BacklotError(f"authorization {auth_id} expired", code=EXIT_CONFIRM)
        if record.get("fingerprint") != quoted.get("fingerprint") or record.get("request") != quoted.get("request"):
            raise BacklotError("authorization does not match current provider, route, inputs, settings or price", code=EXIT_CONFIRM)
        record["state"] = "reserved"
        record["reserved_at"] = _now().isoformat()
        _write(project, record)
        return record


def check_before_submit(project: Project, auth_id: str) -> None:
    """Repeat the expiry check after any uploads, immediately before create."""
    with _locked(project):
        record = _read(project, auth_id)
        if record.get("state") != "reserved":
            raise ProviderPreSubmitError(f"authorization {auth_id} is no longer reserved")
        try:
            expiry = datetime.fromisoformat(str(record["expires_at"]).replace("Z", "+00:00"))
        except (KeyError, ValueError) as exc:
            raise ProviderPreSubmitError("authorization expiry is invalid") from exc
        if expiry <= _now():
            raise ProviderPreSubmitError(f"authorization {auth_id} expired before provider submission")


def stage_request(req: GenRequest, quoted: dict[str, Any], folder: Path) -> GenRequest:
    """Copy approved media into a private temporary folder and verify copied bytes.

    Providers receive only these copies, so edits to source paths after quoting cannot
    alter the submitted request. The folder must live through provider submission.
    """
    expected = (quoted.get("request") or {}).get("media") or {}
    def stage(name: str, paths: list[Path]) -> list[Path]:
        records = expected.get(name) or []
        if len(records) != len(paths):
            raise ProviderPreSubmitError(f"{name} input count changed after approval")
        out = []
        for i, (source, record) in enumerate(zip(paths, records)):
            target = folder / name / str(i) / source.parent.name / source.name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if file_hash(target) != record.get("sha256"):
                raise ProviderPreSubmitError(f"{name} input {i + 1} changed after approval")
            target.chmod(0o400)
            out.append(target)
        return out

    try:
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        images = stage("image", req.media("image"))
        audios = stage("audio", req.media("audio"))
        videos = stage("video", req.media("video"))
        ends = stage("end_image", [req.end_image] if req.end_image else [])
    except OSError as exc:
        # These are local copy/hash/permission failures before a provider sees the request.
        raise ProviderPreSubmitError(f"could not stage approved input: {exc}") from exc
    return GenRequest(prompt=req.prompt, text=req.text, voice=req.voice,
                      images=images, audios=audios, videos=videos,
                      end_image=ends[0] if ends else None, params=dict(req.params),
                      duration_s=req.duration_s, workdir=req.workdir,
                      on_submit=req.on_submit, on_before_submit=req.on_before_submit)


def update_state(project: Project, auth_id: str, state: str, *, take: str | None = None,
                 request_id: str | None = None, error: str | None = None) -> None:
    if state not in ("available", "submitted", "completed", "uncertain"):
        raise BacklotError("invalid authorization state")
    with _locked(project):
        record = _read(project, auth_id)
        if record.get("state") not in ("reserved", "submitted", "uncertain"):
            raise BacklotError(f"authorization {auth_id} is {record.get('state')}; cannot mark {state}")
        record["state"] = state
        record["updated_at"] = _now().isoformat()
        if take:
            record["take"] = take
        if request_id:
            record["request_id"] = request_id
        if error:
            record["error"] = error[:300]
        _write(project, record)

"""Takes in the project dir: id allocation, meta.yaml, manifest.jsonl, file resolution."""

from __future__ import annotations

import fcntl
import json
import shutil
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import yaml

from backlot.errors import BacklotError
from backlot.ids import TAKE_ID_RE as _ID_RE
from backlot.ids import validate_take_id
from backlot.project import Project

STATUSES = ("pending", "failed", "new", "approved", "rejected", "stale")
UNFINISHED = ("pending", "failed")


@dataclass
class Take:
    take: str
    kind: str  # img|vid|vo|mus|sfx|up
    model: str
    provider: str
    shot: str | None = None
    status: str = "new"
    cost_eur: float = 0.0
    parent: str | None = None
    depends_on: list[str] = field(default_factory=list)
    file: str = ""
    prompt: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    created: str = ""
    voice: str | None = None
    request_id: str = ""
    endpoint: str = ""
    seconds: float = 0.0
    reason: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Take":
        fields = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in fields})


def parse_id(take_id: str) -> tuple[str, int, int | None]:
    m = _ID_RE.match(take_id)
    if not m:
        raise BacklotError(f"invalid take id {take_id!r}")
    return m.group("prefix"), int(m.group("seq")), int(m.group("var")) if m.group("var") else None


def take_dir(project: Project, take_id: str) -> Path:
    return project.takes_dir / validate_take_id(take_id)


def meta_path(project: Project, take_id: str) -> Path:
    return take_dir(project, take_id) / "meta.yaml"


@contextmanager
def locked(project: Project) -> Iterator[None]:
    """Exclusive lock on takes/.lock: id allocation, reservation and saving happen under it."""
    project.takes_dir.mkdir(parents=True, exist_ok=True)
    with (project.takes_dir / ".lock").open("a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def existing_ids(project: Project) -> list[str]:
    if not project.takes_dir.is_dir():
        return []
    return sorted(p.name for p in project.takes_dir.iterdir() if p.is_dir() and _ID_RE.match(p.name))


def allocate_id(project: Project, prefix: str, parent: str | None = None) -> str:
    ids = existing_ids(project)
    if parent:
        if parent not in ids:
            raise BacklotError(f"parent take {parent!r} does not exist")
        base_prefix, base_seq, base_var = parse_id(parent)
        if base_var is not None:
            parent = f"{base_prefix}-{base_seq:03d}"
        variants = [parse_id(i)[2] or 1 for i in ids if i.split(".")[0] == parent]
        return f"{parent}.{max(variants) + 1}"
    seqs = [parse_id(i)[1] for i in ids if parse_id(i)[0] == prefix]
    return f"{prefix}-{(max(seqs) + 1) if seqs else 1:03d}"


def load_take(project: Project, take_id: str) -> Take:
    path = meta_path(project, take_id)
    if not path.exists():
        raise BacklotError(f"take {take_id!r} not found in {project.takes_dir}")
    return Take.from_dict(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def list_takes(project: Project) -> list[Take]:
    takes = []
    for tid in existing_ids(project):
        if meta_path(project, tid).exists():
            takes.append(load_take(project, tid))
    return sorted(takes, key=lambda t: (parse_id(t.take)[0], parse_id(t.take)[1], parse_id(t.take)[2] or 0))


def reserve_take(project: Project, take: Take) -> Take:
    """Write takes/<id>/meta.yaml with status pending so the estimate counts as spent before the provider runs."""
    folder = take_dir(project, take.take)
    folder.mkdir(parents=True, exist_ok=True)
    take.status = "pending"
    take.created = take.created or datetime.now(timezone.utc).isoformat(timespec="seconds")
    (folder / "prompt.txt").write_text(take.prompt or take.params.get("text", "") or "", encoding="utf-8")
    write_meta(project, take)
    return take


def discard_take(project: Project, take_id: str) -> None:
    """Drop a reservation that never reached the provider (nothing was billed)."""
    folder = take_dir(project, take_id)
    if folder.is_dir():
        shutil.rmtree(folder)


def save_take(project: Project, take: Take, media: Path, raw: Any = None) -> Take:
    """Move media into takes/<id>/out.<ext>, write meta.yaml + prompt.txt, append manifest."""
    folder = take_dir(project, take.take)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"out{media.suffix.lower()}"
    if media.resolve() != target.resolve():
        shutil.move(str(media), str(target))
    take.file = str(target.relative_to(project.root))
    take.status = "new" if take.status in UNFINISHED else take.status
    take.error = None
    take.created = take.created or datetime.now(timezone.utc).isoformat(timespec="seconds")
    (folder / "prompt.txt").write_text(take.prompt or take.params.get("text", "") or "", encoding="utf-8")
    write_meta(project, take, raw)
    project.manifest.parent.mkdir(parents=True, exist_ok=True)
    with project.manifest.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(take.to_dict(), ensure_ascii=False) + "\n")
    return take


def write_meta(project: Project, take: Take, raw: Any = None) -> None:
    data = take.to_dict()
    if raw is not None:
        data["response"] = _jsonable(raw)
    meta_path(project, take.take).write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def set_status(project: Project, take_id: str, status: str, reason: str | None = None) -> Take:
    if status not in STATUSES:
        raise BacklotError(f"invalid status {status!r}")
    path = meta_path(project, take_id)
    if not path.exists():
        raise BacklotError(f"take {take_id!r} not found")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data["status"] = status
    if reason is not None:
        data["reason"] = reason
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return Take.from_dict(data)


def spent_eur(project: Project) -> float:
    """Everything billed or reserved: pending and failed takes count until recovered or discarded."""
    return round(sum(t.cost_eur for t in list_takes(project)), 4)


def take_file(project: Project, take_id: str) -> Path:
    take = load_take(project, take_id)
    path = project.root / take.file
    if not path.exists():
        raise BacklotError(f"media for {take_id} missing: {path}")
    return path


def resolve_media(project: Project, ref: str) -> Path:
    """A take id, a render name (renders/<name>[.mp4]) or a file path."""
    if _ID_RE.match(ref) and meta_path(project, ref).exists():
        return take_file(project, ref)
    candidates = [Path(ref).expanduser(), project.root / ref, project.renders_dir / ref, project.renders_dir / f"{ref}.mp4"]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    raise BacklotError(f"cannot resolve {ref!r} as take, render or file")


def _jsonable(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return str(value)

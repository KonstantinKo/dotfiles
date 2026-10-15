"""Exact-hash manifests and explicit file bundles for selected deliverables.

Creating or checking a manifest proves only that its declared files currently
match. Bundling copies those files into a fresh folder and rechecks each copy;
neither operation runs a recipe or claims that the final was reproduced.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Mapping

from backlot.authority import file_hash
from backlot.errors import BacklotError


SCHEMA_VERSION = 1
MANIFEST_NAME = "archive-manifest.json"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _safe_member(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise BacklotError(f"{label} must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or PureWindowsPath(value).is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise BacklotError(f"{label} escapes the archive folder: {value!r}")
    normalized = path.as_posix()
    if normalized != value or normalized == ".":
        raise BacklotError(f"{label} must be normalized: {value!r}")
    return normalized


def _resolve_member(root: Path, member: str, label: str) -> Path:
    safe = _safe_member(member, label)
    target = root.joinpath(*PurePosixPath(safe).parts)
    resolved_root = root.resolve()
    resolved = target.resolve(strict=False)
    if not resolved.is_relative_to(resolved_root):
        raise BacklotError(f"{label} escapes the archive folder: {member!r}")
    return target


def _source_ref(source_path: Path, root: Path) -> str:
    resolved = source_path.resolve(strict=True)
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_source(root: Path, source_ref: str, label: str) -> Path:
    candidate = Path(source_ref).expanduser()
    if candidate.is_absolute():
        return candidate
    return _resolve_member(root, source_ref, label)


def _declared_recipe_paths(recipe: Any) -> list[str]:
    if recipe is None:
        return []
    if not isinstance(recipe, dict):
        raise BacklotError("recipe must be a JSON object")
    paths: list[str] = []
    inputs = recipe.get("inputs") or {}
    if isinstance(inputs, dict):
        paths.extend(str(value) for value in inputs.values())
    elif isinstance(inputs, list):
        for item in inputs:
            if isinstance(item, str):
                paths.append(item)
            elif isinstance(item, dict) and item.get("path"):
                paths.append(str(item["path"]))
            else:
                raise BacklotError("recipe inputs list entries must be paths or objects with path")
    else:
        raise BacklotError("recipe inputs must be a path map or list")
    extras = recipe.get("extras") or []
    outputs = recipe.get("outputs") or ([] if recipe.get("output") is None else [recipe["output"]])
    for name, values in (("extras", extras), ("outputs", outputs)):
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            raise BacklotError(f"recipe {name} must be a path list")
        paths.extend(str(value) for value in values)
    return [_safe_member(value, "recipe member") for value in paths]


def _validate_recipe(recipe: Any, members: set[str]) -> None:
    for path in _declared_recipe_paths(recipe):
        if path not in members:
            raise BacklotError(f"recipe references undeclared archive member {path!r}")


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def create_archive(files: Iterable[Mapping[str, Any]], manifest_path: Path, *,
                   recipe: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Write a hash manifest for selected source versions; files are not copied."""
    manifest_path = Path(manifest_path).expanduser().resolve()
    if manifest_path.exists() or manifest_path.is_symlink():
        raise BacklotError(f"archive manifest already exists: {manifest_path}")
    root = manifest_path.parent
    rows = []
    names: set[str] = set()
    for index, item in enumerate(files):
        if not isinstance(item, Mapping):
            raise BacklotError(f"archive file {index + 1} must be an object")
        member = _safe_member(item.get("path"), f"archive file {index + 1} path")
        key = member.casefold()
        if key in names:
            raise BacklotError(f"duplicate archive path {member!r}")
        names.add(key)
        source_text = item.get("source")
        if not isinstance(source_text, (str, Path)) or not str(source_text):
            raise BacklotError(f"archive file {index + 1} needs source")
        source = Path(source_text).expanduser().resolve(strict=True)
        if not source.is_file():
            raise BacklotError(f"archive source is not a file: {source}")
        digest = file_hash(source)
        declared_hash = item.get("sha256")
        if declared_hash is not None and (not isinstance(declared_hash, str) or declared_hash != digest):
            raise BacklotError(f"archive source hash mismatch for {source}")
        role = str(item.get("role") or "").strip()
        if not role:
            raise BacklotError(f"archive file {index + 1} needs a role")
        rows.append({"path": member, "source_path": _source_ref(source, root), "role": role,
                     "size_bytes": source.stat().st_size, "sha256": digest})
    if not rows:
        raise BacklotError("archive needs at least one declared file")
    recipe_data = dict(recipe) if recipe is not None else None
    _validate_recipe(recipe_data, {row["path"] for row in rows})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "files": rows,
        "recipe": recipe_data,
        "bundle": {"status": "manifest_only", "files_copied": False},
        "portability": {
            "status": "pending",
            "all_sources_relative": all(not Path(row["source_path"]).is_absolute() for row in rows),
            "recipe_bindings_declared": recipe_data is None or bool(_declared_recipe_paths(recipe_data)),
            "reproduction_status": "not_run",
            "limits": ["A hash manifest proves file identity at check time; it does not prove backup durability or successful reproduction."],
        },
    }
    _write_manifest(manifest_path, manifest)
    return {"manifest": str(manifest_path), **manifest}


def _load_manifest(manifest_path: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    if not manifest_path.is_file():
        raise BacklotError(f"archive manifest not found: {manifest_path}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BacklotError(f"cannot read archive manifest {manifest_path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION or not isinstance(data.get("files"), list):
        raise BacklotError(f"unsupported or invalid archive manifest: {manifest_path}")
    names = set()
    for index, row in enumerate(data["files"]):
        if not isinstance(row, dict):
            raise BacklotError(f"archive manifest file {index + 1} must be an object")
        member = _safe_member(row.get("path"), f"archive file {index + 1} path")
        if member.casefold() in names:
            raise BacklotError(f"duplicate archive path {member!r}")
        names.add(member.casefold())
        if not isinstance(row.get("sha256"), str) or not _HASH_RE.fullmatch(row["sha256"]):
            raise BacklotError(f"archive file {member!r} has an invalid sha256")
        if not isinstance(row.get("source_path"), str) or not row["source_path"]:
            raise BacklotError(f"archive file {member!r} has no source_path")
        if not str(row.get("role") or "").strip():
            raise BacklotError(f"archive file {member!r} has no role")
    _validate_recipe(data.get("recipe"), {row["path"] for row in data["files"]})
    return manifest_path, data


def check_archive(manifest_path: Path) -> dict[str, Any]:
    """Check each declared source path against its exact SHA-256 and size."""
    path, manifest = _load_manifest(manifest_path)
    checked, missing, mutated = [], [], []
    root = path.parent
    for row in manifest["files"]:
        source = _resolve_source(root, row["source_path"], f"archive source {row['path']}")
        if not source.is_file():
            missing.append(row["path"])
            continue
        actual_hash = file_hash(source)
        actual_size = source.stat().st_size
        if actual_hash != row["sha256"] or actual_size != int(row.get("size_bytes") or -1):
            mutated.append({"path": row["path"], "expected_sha256": row["sha256"], "actual_sha256": actual_hash,
                            "expected_size_bytes": row.get("size_bytes"), "actual_size_bytes": actual_size})
        else:
            checked.append(row["path"])
    ok = not missing and not mutated
    bundle = manifest.get("bundle") or {}
    return {
        "manifest": str(path), "ok": ok, "checked": checked, "missing": missing, "mutated": mutated,
        "bundle_files_verified": bool(ok and bundle.get("status") == "copied_and_hash_checked"),
        "backup_verified": False, "reproduction_verified": False,
        "reproduction_status": (manifest.get("portability") or {}).get("reproduction_status", "not_run"),
    }


def bundle_archive(manifest_path: Path, destination: Path) -> dict[str, Any]:
    """Copy declared files into a new folder, then write a bundle-local manifest."""
    source_manifest, manifest = _load_manifest(manifest_path)
    checked = check_archive(source_manifest)
    if not checked["ok"]:
        parts = []
        if checked["missing"]:
            parts.append("missing " + ", ".join(checked["missing"]))
        if checked["mutated"]:
            parts.append("mutated " + ", ".join(item["path"] for item in checked["mutated"]))
        raise BacklotError("cannot bundle an incomplete archive: " + "; ".join(parts))
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise BacklotError(f"bundle destination must be a new directory: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    try:
        for row in manifest["files"]:
            source = _resolve_source(source_manifest.parent, row["source_path"], f"archive source {row['path']}")
            target = _resolve_member(destination, row["path"], f"bundle destination {row['path']}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if file_hash(target) != row["sha256"]:
                raise BacklotError(f"copied bundle member failed its hash check: {row['path']}")
        bundled_files = [{"source": destination / row["path"], "path": row["path"], "role": row["role"],
                          "sha256": row["sha256"]} for row in manifest["files"]]
        bundled_manifest_path = destination / MANIFEST_NAME
        bundled_manifest = create_archive(bundled_files, bundled_manifest_path, recipe=manifest.get("recipe"))
        bundled_manifest["bundle"] = {"status": "copied_and_hash_checked", "files_copied": True,
                                       "source_manifest": str(source_manifest)}
        bundled_manifest["portability"] = {
            **bundled_manifest["portability"],
            "status": "inputs_bundled_pending_recipe_reproduction",
            "reproduction_status": "not_run",
            "limits": [
                "All declared files were copied and hash checked in this folder.",
                "No recipe was executed; reproduction and backup durability remain unverified.",
            ],
        }
        _write_manifest(bundled_manifest_path, {key: value for key, value in bundled_manifest.items() if key != "manifest"})
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    result = check_archive(bundled_manifest_path)
    if not result["ok"] or not result["bundle_files_verified"]:
        shutil.rmtree(destination, ignore_errors=True)
        raise BacklotError("fresh bundle failed its final archive check")
    return {"destination": str(destination), **result}

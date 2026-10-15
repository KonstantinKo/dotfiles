"""Declared, per-scene production requirements and exact deliverable readiness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backlot import delivery, frontmatter, vault
from backlot.authority import file_hash
from backlot.errors import BacklotError
from backlot.project import Project
from backlot.takes import load_take

# This registry also renders the operator reference in skills/studio/references.
REQUIREMENTS: dict[str, str] = {
    "picture": "Selected output ranges and a version-matched user approval.",
    "board": "An explicitly selected, approved board take for the scene.",
    "identity": "Declared character/identity Context locks and their selected takes.",
    "world": "Declared location/world Context locks and their selected takes.",
    "spatial": "A declared motion or spatial guide with exact bytes.",
    "blender": "A declared editable Blender scene/version and guide export.",
    "voice": "Declared voice media bound to the assembly or named caption source.",
    "captions": "Declared caption file with exact bytes.",
    "score": "Declared score media bound to this output revision.",
    "graphics": "Declared exact graphic source with exact bytes.",
    "review": "Version-bound review evidence for the declared criterion.",
    "remote_share": "A scoped share approval and recorded share location/term.",
}
ARTIFACT_REQUIREMENTS = {"spatial", "blender", "voice", "captions", "score", "graphics"}
LOCK_REQUIREMENTS = {"identity", "world"}


def requirements_markdown() -> str:
    lines = ["# Workflow requirements", "", "Generated from `backlot.workflow.REQUIREMENTS`.", "",
             "The base workflow asks for an agreed brief, named scenes, exact deliverables, output verification, source coverage and scoped user approval. Add only requirements the production needs. `backlot stage --json` reports each missing scene or deliverable requirement.",
             "", "| Requirement | Evidence |", "|---|---|"]
    lines += [f"| `{name}` | {description} |" for name, description in REQUIREMENTS.items()]
    lines += ["", "An imported historical acceptance record can cover named requirements only for its original approved artifact and assembly recipe. New bytes require normal declared evidence.", ""]
    return "\n".join(lines)


def declaration(project: Project) -> dict[str, Any] | None:
    raw = project.data.get("workflow")
    if raw is None:
        return None
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise BacklotError("project.yaml workflow needs schema_version: 1")
    if raw.get("preset") == "legacy":
        return {"schema_version": 1, "preset": "legacy"}
    if raw.get("preset", "base") != "base":
        raise BacklotError("workflow preset must be base or legacy")
    scenes = raw.get("scenes")
    outputs = raw.get("deliverables")
    if not isinstance(scenes, dict) or not scenes:
        raise BacklotError("workflow needs at least one named scene")
    if not isinstance(outputs, list) or not outputs or not any(x.get("required", True) for x in outputs if isinstance(x, dict)):
        raise BacklotError("workflow needs at least one required named deliverable")
    seen: set[str] = set()
    for output in outputs:
        if not isinstance(output, dict) or not output.get("id") or not output.get("kind"):
            raise BacklotError("each workflow deliverable needs id and kind")
        if output["id"] in seen:
            raise BacklotError(f"duplicate workflow deliverable {output['id']}")
        seen.add(output["id"])
    for scene_id, scene in scenes.items():
        if not isinstance(scene, dict) or not scene.get("deliverable") or scene["deliverable"] not in seen:
            raise BacklotError(f"scene {scene_id} needs a declared deliverable")
        requires = scene.get("requires")
        if not isinstance(requires, list) or not requires:
            raise BacklotError(f"scene {scene_id} needs at least one declared requirement")
        unknown = set(requires) - REQUIREMENTS.keys()
        if unknown:
            raise BacklotError(f"scene {scene_id} has unknown requirements: {', '.join(sorted(unknown))}")
    return raw


def _brief(project: Project) -> str | None:
    path = project.vault_project / "Brief.md"
    if not path.is_file():
        return "agreed Brief.md missing"
    data, _ = frontmatter.read(path)
    if data.get("agreed") is not True:
        return "Brief.md has no agreed brief"
    return None


def _versioned_ref(project: Project, value: Any) -> str | None:
    if not isinstance(value, dict):
        return "exact artifact reference missing"
    take_id = value.get("artifact")
    path_value = value.get("path")
    if take_id:
        try:
            take = load_take(project, str(take_id))
            path_value = take.file
            if not take.sha256 or take.sha256 != value.get("sha256"):
                return f"artifact {take_id} version missing or mismatched"
        except BacklotError as exc:
            return str(exc)
    if not path_value or not value.get("sha256"):
        return "artifact path and SHA-256 required"
    path = Path(str(path_value)).expanduser()
    path = path if path.is_absolute() else project.root / path
    if not path.is_file():
        return f"artifact missing: {path}"
    if file_hash(path) != value["sha256"]:
        return f"artifact bytes changed: {path}"
    return None


def _branch(scene_id: str, requirement: str, scene: dict[str, Any],
            result: dict[str, Any], record: dict[str, Any], project: Project) -> list[str]:
    evidence = (scene.get("evidence") or {}).get(requirement)
    if requirement == "picture":
        return [] if result.get("scene_ranges", {}).get(scene_id) and result["passed"] else ["selected picture range or verified deliverable missing"]
    if requirement in LOCK_REQUIREMENTS:
        names = (evidence or {}).get("locks") if isinstance(evidence, dict) else None
        if not names:
            return [f"{requirement} lock evidence missing"]
        missing = []
        for name in names:
            try:
                path = vault.context_note(project, str(name))
                data, _ = frontmatter.read(path)
                if data.get("locked") is not True or not data.get("locked_take"):
                    missing.append(f"{name} not locked to a take")
                else:
                    take = load_take(project, str(data["locked_take"]))
                    if take.status != "approved" or not take.file or not take.sha256:
                        missing.append(f"{name} selected take lacks approved exact media")
                    elif error := _versioned_ref(project, {"artifact": take.take, "sha256": take.sha256}):
                        missing.append(f"{name}: {error}")
            except (BacklotError, ValueError) as exc:
                missing.append(str(exc))
        return missing
    if requirement == "board":
        take_id = (evidence or {}).get("take") if isinstance(evidence, dict) else None
        if not take_id:
            return ["selected board take missing"]
        try:
            take = load_take(project, str(take_id))
            if take.status != "approved" or not take.file or not take.sha256:
                return [f"board {take_id} lacks approved exact media"]
            error = _versioned_ref(project, {"artifact": take_id, "sha256": take.sha256})
            return [error] if error else []
        except BacklotError as exc:
            return [str(exc)]
    if requirement in ARTIFACT_REQUIREMENTS:
        refs = (evidence or {}).get("artifacts") if isinstance(evidence, dict) else None
        if not isinstance(refs, list) or not refs:
            return [f"{requirement} exact artifact evidence missing"]
        errors = [error for ref in refs if (error := _versioned_ref(project, ref))]
        if requirement in {"voice", "score"} and not errors:
            try:
                assembly = delivery.load_assembly(project, str(record.get("assembly") or ""))
                included = {x.get("sha256") for x in assembly.get("attachments") or []}
                if not all(ref.get("sha256") in included for ref in refs):
                    errors.append(f"{requirement} source is not bound to assembly")
            except BacklotError as exc:
                errors.append(str(exc))
        return errors
    if requirement == "review":
        criterion = (evidence or {}).get("criterion") if isinstance(evidence, dict) else None
        if not criterion:
            return ["review criterion missing"]
        import yaml

        folder = project.vault_project / "Records" / "reviews"
        rows = [yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                for path in folder.glob("review-*.yaml")] if folder.is_dir() else []
        output = record.get("output") or {}
        allowed_outcomes = {"pass", "pass_limited"} if (evidence or {}).get("allow_limited") else {"pass"}
        if any(r.get("subject", {}).get("sha256") == output.get("sha256") and
               r.get("outcome") in allowed_outcomes and
               any(c.get("id") == criterion and c.get("result") == "pass"
                   for c in (r.get("semantic") or {}).get("criteria") or [])
               for r in rows):
            return []
        return [f"review criterion {criterion} lacks a passing review for this version"]
    if requirement == "remote_share":
        share = record.get("share") or {}
        return [] if record.get("kind") == "share" and share.get("url") and (
            share.get("expires_at") or share.get("expiry_term_days")) else ["share URL or expiry term missing"]
    return [f"unsupported requirement {requirement}"]


def _historical_covers(project: Project, record: dict[str, Any], result: dict[str, Any],
                       requirement: str, scene: dict[str, Any]) -> bool:
    if (scene.get("evidence") or {}).get(requirement):
        return False
    acceptance_id = record.get("historical_acceptance_id")
    if not acceptance_id or not result.get("approval_id") or not result.get("passed"):
        return False
    try:
        evidence = delivery.load_historical_acceptance(project, str(acceptance_id))
        if not delivery.historical_acceptance_matches(project, evidence, record):
            return False
        approval_file = evidence.get("source_evidence") or {}
        if _versioned_ref(project, approval_file):
            return False
    except BacklotError:
        return False
    if requirement not in evidence.get("covers", []):
        return False
    return evidence.get("decision_id") == result["approval_id"]


def evaluate(project: Project) -> dict[str, Any]:
    spec = declaration(project)
    if spec is None or spec.get("preset") == "legacy":
        raise BacklotError("no declared workflow; legacy stage evaluator applies")
    global_blockers = []
    if brief_error := _brief(project):
        global_blockers.append(brief_error)
    output_results: dict[str, dict[str, Any]] = {}
    referenced = {str(scene["deliverable"]) for scene in spec["scenes"].values()}
    for item in spec["deliverables"]:
        if item.get("required", True) or item["id"] in referenced:
            output_results[item["id"]] = delivery.inspect_deliverable(project, str(item["id"]))
            if output_results[item["id"]].get("kind") != item["kind"]:
                output_results[item["id"]]["blockers"].append("deliverable kind differs from workflow declaration")
                output_results[item["id"]]["passed"] = False
    scene_results: dict[str, dict[str, Any]] = {}
    for scene_id, scene in spec["scenes"].items():
        output_id = str(scene["deliverable"])
        result = output_results[output_id]
        try:
            record = delivery.load_deliverable(project, output_id)
        except BacklotError:
            record = {}
        blockers: list[str] = []
        if not result.get("passed") or not result.get("scene_ranges", {}).get(scene_id):
            blockers.append("picture: selected picture range or verified deliverable missing")
        for requirement in scene["requires"]:
            errors = _branch(scene_id, requirement, scene, result, record, project)
            if errors and not _historical_covers(project, record, result, requirement, scene):
                blockers += [f"{requirement}: {error}" for error in errors]
        scene_results[scene_id] = {"name": scene.get("name") or scene_id, "deliverable": output_id,
                                   "requirements": scene["requires"], "blockers": blockers,
                                   "passed": not blockers}
    blockers = [*global_blockers]
    blockers += [f"{name}: {issue}" for name, result in output_results.items() for issue in result["blockers"]]
    blockers += [f"{name}: {issue}" for name, result in scene_results.items() for issue in result["blockers"]]
    return {"preset": "base", "passed": not blockers, "readiness": "delivered" if not blockers else "blocked",
            "blockers": blockers, "scenes": scene_results, "deliverables": output_results}

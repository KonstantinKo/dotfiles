from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from PIL import Image

from backlot import delivery, frontmatter, register
from backlot.authority import file_hash
from backlot.decisions import record_decision
from backlot.errors import BacklotError
from backlot.project import load_project_dir
from backlot.workflow import requirements_markdown
from tests.conftest import FFMPEG, run_json


def _video(path: Path, color: str) -> Path:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"color=c={color}:s=32x32:r=24", "-frames:v", "24", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


def _workflow(project, requires, evidence=None, *, kind="picture", deliverable="picture-master"):
    path = project["root"] / "project.yaml"
    data = yaml.safe_load(path.read_text())
    data["workflow"] = {"schema_version": 1, "preset": "base",
                        "scenes": {"whole": {"name": "Whole cut", "deliverable": deliverable,
                                              "requires": requires, "evidence": evidence or {}}},
                        "deliverables": [{"id": deliverable, "kind": kind, "required": True}]}
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    frontmatter.update(project["vault_project"] / "Brief.md", agreed=True)


def _register_cut(project, *, extra_sources=(), kind="picture", deliverable="picture-master",
                  approve=True, coverage=None, history=None, share=None):
    proj, root = load_project_dir(project["root"]), project["root"]
    source = _video(root / "inputs" / "source.mp4", "red")
    output = _video(root / "renders" / "complete.mp4", "blue")
    src = register.register(proj, {"kind": "vid", "origin": "supplied", "media": str(source)})
    refs = [{"id": src["take"], "sha256": src["sha256"], "role": "picture"}]
    attachments = []
    for item in extra_sources:
        refs.append({"id": item["take"], "sha256": item["sha256"], "role": item.get("role", "audio")})
        attachments.append({"artifact": item["take"], "sha256": item["sha256"], "role": item.get("role", "audio")})
    final = register.register(proj, {"kind": "vid", "origin": "assembly", "media": str(output),
                                     "source_refs": refs, "coverage": [{"story": "whole", "output_frames": [0, 23]}]})
    recipe = root / "edit" / "recipe.json"
    recipe.write_text('{"edit":"whole"}\n')
    delivery.register_assembly(proj, {"id": "cut-v1", "route": "custom",
                                      "output": {"artifact": final["take"], "sha256": final["sha256"]},
                                      "recipe": {"path": str(recipe), "sha256": file_hash(recipe)},
                                      "segments": [{"scene": "whole", "output_frames": [0, 23],
                                                    "source": {"artifact": src["take"], "sha256": src["sha256"]},
                                                    "source_frames": [0, 23]}], "attachments": attachments})
    decision = None
    if approve:
        decision = record_decision(proj, "approve", kind, deliverable, version=final["sha256"],
                                   scope="final picture" if kind == "picture" else "share copy",
                                   reason="accepted exact cut", source_ref="thread:m1", source_message="This cut is final.",
                                   coverage=coverage, source_at="2020-01-01T00:00:00Z" if history else None)
    historical_acceptance_id = None
    if history:
        approval = root / "edit" / "archived-final-approval.json"
        approval.write_text(json.dumps({"output_sha256": final["sha256"],
                                        "user_quote": "This cut is final."}))
        historical_acceptance_id = "original-final"
        delivery.import_historical_acceptance(proj, {
            "id": historical_acceptance_id, "deliverable": deliverable, "kind": kind,
            "approval_scope": "final picture" if kind == "picture" else "share copy",
            "artifact": final["take"], "sha256": final["sha256"], "assembly": "cut-v1",
            "decision_id": decision["id"], "source_ref": "thread:m1",
            "source_at": "2020-01-01T00:00:00Z",
            "source_evidence": {"path": str(approval), "sha256": file_hash(approval)},
            "covers": history, "accepted_limitations": ["static acting accepted"]})
    delivery.register_deliverable(proj, {"id": deliverable, "kind": kind, "assembly": "cut-v1",
                                         "output": {"artifact": final["take"], "sha256": final["sha256"]},
                                         "approval_scope": "final picture" if kind == "picture" else "share copy",
                                         **({"historical_acceptance_id": historical_acceptance_id} if history else {}),
                                         **({"share": share} if share else {})})
    return proj, final, output


def test_abstract_montage_passes_without_unrequested_branches_and_inspection_is_read_only(project):
    _workflow(project, ["picture"])
    _, final, _ = _register_cut(project)
    vp = project["vault_project"]
    (vp / "Delivery.md").write_text("# Current narrative\n\nKeep this text.\n")
    paths = [vp / name for name in ("Status.md", "Costs.md", "Handoff.md", "Delivery.md", "demo.md")]
    before = [p.read_bytes() for p in paths]
    code, stage = run_json("stage")
    assert code == 0 and stage["passed"] and stage["readiness"] == "delivered"
    assert set(stage["scenes"]["whole"]["requirements"]) == {"picture"}
    assert run_json("status")[0] == 0 and run_json("cost")[0] == 0 and run_json("delivery")[0] == 0
    assert [p.read_bytes() for p in paths] == before
    assert not (vp / "Deliverables.md").exists()
    assert run_json("delivery", "--refresh")[0] == 0
    assert final["sha256"] in (vp / "Deliverables.md").read_text()
    assert (vp / "Delivery.md").read_bytes() == before[3]
    assert run_json("stage", "--advance")[0] == 0
    assert frontmatter.read(vp / "demo.md")[0]["status"] == "delivered"


def test_imported_footage_explainer_voice_and_captions_need_no_cast_or_board(project):
    root, proj = project["root"], load_project_dir(project["root"])
    audio = root / "inputs" / "narration.wav"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=330:duration=1", str(audio)], check=True)
    voice = register.register(proj, {"kind": "vo", "origin": "supplied", "media": str(audio)})
    voice["role"] = "voice"
    captions = root / "inputs" / "captions.srt"
    captions.write_text("1\n00:00:00,000 --> 00:00:00,900\nHello.\n")
    _workflow(project, ["picture", "voice", "captions"], {"voice": {"artifacts": [{"artifact": voice["take"], "sha256": voice["sha256"]}]},
                                                            "captions": {"artifacts": [{"path": str(captions), "sha256": file_hash(captions)}]}})
    _register_cut(project, extra_sources=[voice])
    code, stage = run_json("stage")
    assert code == 0 and stage["passed"]
    assert "board" not in stage["scenes"]["whole"]["requirements"]


def test_fictional_character_declared_identity_lock_blocks_only_its_scene(project):
    _workflow(project, ["picture", "identity"], {"identity": {"locks": ["Cast/Mia"]}})
    proj, _, _ = _register_cut(project)
    code, stage = run_json("stage")
    assert code == 1 and "Cast/Mia not locked" in str(stage["missing"])
    assert stage["deliverables"]["picture-master"]["passed"]
    image = project["root"] / "inputs" / "mia.png"
    Image.new("RGB", (16, 16), "green").save(image)
    take = register.register(proj, {"kind": "img", "origin": "supplied", "media": str(image)})
    from backlot.decisions import approve

    approve(proj, take["take"], "fictional design accepted", source_ref="thread:m2", source_message="Use this design.")
    frontmatter.update(project["vault_project"] / "Context" / "Cast" / "Mia.md", locked=True, locked_take=take["take"])
    assert run_json("stage")[0] == 0
    Image.new("RGB", (16, 16), "yellow").save(image)
    code, stage = run_json("stage")
    assert code == 1 and any("artifact bytes changed" in issue for issue in stage["missing"])


def test_each_scene_needs_verified_picture_even_with_only_board_requirement(project):
    root, proj = project["root"], load_project_dir(project["root"])
    image = root / "inputs" / "board.png"
    Image.new("RGB", (16, 16), "green").save(image)
    board = register.register(proj, {"kind": "img", "origin": "supplied", "media": str(image)})
    from backlot.decisions import approve

    approve(proj, board["take"], "board accepted", source_ref="thread:board",
            source_message="Use this board.")
    _workflow(project, ["board"], {"board": {"take": board["take"]}})
    code, stage = run_json("stage")
    assert code == 1 and any("selected picture range" in issue for issue in stage["missing"])


def test_optional_deliverable_referenced_by_scene_blocks_when_missing(project):
    _workflow(project, ["board"])
    _register_cut(project)
    path = project["root"] / "project.yaml"
    data = yaml.safe_load(path.read_text())
    data["workflow"]["scenes"]["second"] = {"deliverable": "optional-copy", "requires": ["board"]}
    data["workflow"]["deliverables"].append({"id": "optional-copy", "kind": "share", "required": False})
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    code, stage = run_json("stage")
    assert code == 1 and "optional-copy" in stage["deliverables"]
    assert any("optional-copy" in issue for issue in stage["missing"])


def test_archived_exact_final_acceptance_covers_selected_branches_only_for_same_bytes(project):
    _workflow(project, ["picture", "identity", "world", "spatial", "graphics"])
    _, _, output = _register_cut(project, history=["identity", "world", "spatial", "graphics"])
    assert run_json("stage")[0] == 0
    _video(output, "green")
    code, stage = run_json("stage")
    assert code == 1 and any("SHA-256" in issue or "bytes changed" in issue for issue in stage["missing"])


def test_new_revision_cannot_copy_or_freshly_self_attest_historical_acceptance(project):
    _workflow(project, ["picture", "identity"])
    proj, old, _ = _register_cut(project, history=["identity"])
    assert run_json("stage")[0] == 0
    root = project["root"]
    revised_media = _video(root / "renders" / "revised.mp4", "green")
    old_assembly = delivery.load_assembly(proj, "cut-v1")
    source = old_assembly["segments"][0]["source"]
    revised = register.register(proj, {"kind": "vid", "origin": "assembly", "media": str(revised_media),
                                       "source_refs": [{"id": source["artifact"], "sha256": source["sha256"],
                                                        "role": "picture"}],
                                       "coverage": [{"story": "whole", "output_frames": [0, 23]}]})
    recipe = root / "edit" / "revision.json"
    recipe.write_text('{"edit":"revision"}\n')
    delivery.register_assembly(proj, {"id": "cut-v2", "route": "custom",
                                      "output": {"artifact": revised["take"], "sha256": revised["sha256"]},
                                      "recipe": {"path": str(recipe), "sha256": file_hash(recipe)},
                                      "segments": [{"scene": "whole", "output_frames": [0, 23],
                                                    "source": source, "source_frames": [0, 23]}]})
    now = datetime.now(timezone.utc).isoformat()
    decision = record_decision(proj, "approve", "picture", "revision", version=revised["sha256"],
                               scope="final picture", reason="new revision approved", source_ref="thread:new",
                               source_message="This revision is final.", source_at=now)
    spec = {"id": "revision", "kind": "picture", "assembly": "cut-v2",
            "output": {"artifact": revised["take"], "sha256": revised["sha256"]},
            "approval_scope": "final picture", "historical_acceptance_id": "original-final"}
    with pytest.raises(BacklotError, match="does not bind"):
        delivery.register_deliverable(proj, spec)
    with pytest.raises(BacklotError, match="imported separately"):
        delivery.register_deliverable(proj, {**spec, "historical_acceptance_id": None,
                                            "historical_acceptance": {"output_sha256": revised["sha256"]}})
    approval = root / "edit" / "new-approval.json"
    approval.write_text(json.dumps({"output_sha256": revised["sha256"],
                                    "user_quote": "This revision is final."}))
    with pytest.raises(BacklotError, match="predate artifact migration"):
        delivery.import_historical_acceptance(proj, {
            "id": "revision-history", "deliverable": "revision", "kind": "picture",
            "approval_scope": "final picture", "artifact": revised["take"],
            "sha256": revised["sha256"], "assembly": "cut-v2", "decision_id": decision["id"],
            "source_ref": "thread:new", "source_at": now,
            "source_evidence": {"path": str(approval), "sha256": file_hash(approval)},
            "covers": ["identity"]})
    delivery.register_deliverable(proj, {**spec, "historical_acceptance_id": None})
    path = root / "project.yaml"
    data = yaml.safe_load(path.read_text())
    data["workflow"]["deliverables"] = [{"id": "revision", "kind": "picture", "required": True}]
    data["workflow"]["scenes"]["whole"]["deliverable"] = "revision"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    code, stage = run_json("stage")
    assert code == 1 and any("identity" in issue for issue in stage["missing"])


def test_partial_user_range_does_not_approve_uncovered_output(project):
    _workflow(project, ["picture"])
    _register_cut(project, coverage=[[0, 10]])
    code, stage = run_json("stage")
    assert code == 1 and any("does not cover output frames" in issue for issue in stage["missing"])


def test_accepted_limit_keeps_exact_picture_approval_until_rejected(project):
    _workflow(project, ["picture"])
    proj, final, _ = _register_cut(project)
    initial = delivery.inspect_deliverable(proj, "picture-master")
    assert initial["passed"] and initial["approval_id"]

    common = {"version": final["sha256"], "scope": "final picture"}
    record_decision(proj, "accept-limit", "picture", "picture-master", **common,
                    reason="known visual limit accepted", source_ref="thread:limit",
                    source_message="I accept this limit.")
    inspected = delivery.inspect_deliverable(proj, "picture-master")
    code, stage = run_json("stage")
    assert inspected["passed"] and inspected["approval_id"] == initial["approval_id"]
    assert code == 0 and stage["passed"] and stage["deliverables"]["picture-master"]["approval_id"] == initial["approval_id"]

    record_decision(proj, "reject", "picture", "picture-master", **common,
                    reason="later rejection", source_ref="thread:reject",
                    source_message="I reject this picture.")
    record_decision(proj, "accept-limit", "picture", "picture-master", **common,
                    reason="other limit accepted", source_ref="thread:other-limit",
                    source_message="I accept this other limit.")
    inspected = delivery.inspect_deliverable(proj, "picture-master")
    code, stage = run_json("stage")
    assert not inspected["passed"] and inspected["approval_id"] is None
    assert code == 1 and any("not a user approval" in issue for issue in stage["missing"])


def test_repeated_scene_source_is_probed_once_and_hash_bound_facts_are_reused(project, monkeypatch):
    root, proj = project["root"], load_project_dir(project["root"])
    source_path = _video(root / "inputs" / "repeat.mp4", "red")
    output_path = _video(root / "renders" / "repeat-final.mp4", "blue")
    source = register.register(proj, {"kind": "vid", "origin": "supplied", "media": str(source_path)})
    final = register.register(proj, {"kind": "vid", "origin": "assembly", "media": str(output_path),
                                     "source_refs": [{"id": source["take"], "sha256": source["sha256"],
                                                      "role": "picture"}],
                                     "coverage": [{"story": "first", "output_frames": [0, 11]},
                                                  {"story": "second", "output_frames": [12, 23]}]})
    recipe = root / "edit" / "repeated.json"
    recipe.write_text('{"edit":"repeated"}\n')
    original_probe = delivery._video_probe
    probed: list[Path] = []

    def count_probe(path):
        probed.append(path)
        return original_probe(path)

    monkeypatch.setattr(delivery, "_video_probe", count_probe)
    segments = [{"scene": scene, "output_frames": frames,
                 "source": {"artifact": source["take"], "sha256": source["sha256"]},
                 "source_frames": frames}
                for scene, frames in (("first", [0, 11]), ("second", [12, 23]))]
    assembly = delivery.register_assembly(proj, {"id": "repeat-cut", "route": "custom",
                                                 "output": {"artifact": final["take"], "sha256": final["sha256"]},
                                                 "recipe": {"path": str(recipe), "sha256": file_hash(recipe)},
                                                 "segments": segments})
    assert len(probed) == 2 and len(assembly["verified_probes"]) == 2
    record_decision(proj, "approve", "picture", "repeat-final", version=final["sha256"],
                    scope="final picture", reason="approved", source_ref="thread:repeat",
                    source_message="This repeat cut is final.")
    delivery.register_deliverable(proj, {"id": "repeat-final", "kind": "picture",
                                         "assembly": "repeat-cut",
                                         "output": {"artifact": final["take"], "sha256": final["sha256"]},
                                         "approval_scope": "final picture"})
    assert delivery.inspect_deliverable(proj, "repeat-final")["passed"]
    assert len(probed) == 2
    assembly_path = root / "edit" / "assemblies" / "repeat-cut.yaml"
    stored = assembly_path.read_text()
    legacy = yaml.safe_load(stored)
    del legacy["verified_probes"]
    assembly_path.write_text(yaml.safe_dump(legacy, sort_keys=False))
    assert delivery.inspect_deliverable(proj, "repeat-final")["passed"]
    assert len(probed) == 4  # Legacy fallback counts each unique asset once per inspection.
    assembly_path.write_text(stored)
    _video(source_path, "green")
    result = delivery.inspect_deliverable(proj, "repeat-final")
    assert not result["passed"] and any("SHA-256" in issue for issue in result["blockers"])
    assert len(probed) == 4


def test_requirement_reference_is_generated_from_runtime_registry():
    path = Path(__file__).resolve().parents[1] / "skills" / "studio" / "references" / "workflow-gates.md"
    assert path.read_text() == requirements_markdown()


def test_agent_decision_cannot_approve_final_deliverable(project):
    _workflow(project, ["picture"])
    _, final, _ = _register_cut(project, approve=False)
    code, decision = run_json("decision", "approve", "picture", "picture-master", "--version", final["sha256"],
                              "--scope", "final picture", "--reason", "agent reviewed", "--source-kind", "agent",
                              "--source-ref", "review:one", "--source-message", "The technical checks passed.")
    assert code == 0 and decision["source_kind"] == "agent"
    code, stage = run_json("stage")
    assert code == 1 and any("user approval" in issue for issue in stage["missing"])


def test_reviewer_rejection_keeps_agent_source_kind(project):
    root = project["root"]
    source = _video(root / "inputs" / "rejected.mp4", "red")
    take = register.register(load_project_dir(root), {"kind": "vid", "origin": "supplied", "media": str(source)})
    code, _ = run_json("reject", take["take"], "--reason", "visible continuity defect",
                       "--source-ref", "review:frame-10", "--source-message", "Frame ten changes the costume.")
    assert code == 0
    decisions = list((project["vault_project"] / "Records" / "decisions").glob("dec-*.yaml"))
    assert len(decisions) == 1 and yaml.safe_load(decisions[0].read_text())["source_kind"] == "agent"


def test_review_score_and_archive_cli_wrappers_use_local_evidence(project):
    root = project["root"]
    cut = _video(root / "renders" / "review.mp4", "red")
    review_spec = root / "review.json"
    review_spec.write_text(json.dumps({
        "subject": {"kind": "render", "id": "renders/review.mp4", "sha256": file_hash(cut)},
        "source": {"kind": "agent_review", "ref": "fixture:review", "observed_at": "2026-10-02T09:00:00Z"},
        "coverage": {"mode": "full_playback"},
        "technical": {"checks": [{"name": "decode", "result": "pass", "evidence": ["fixture:ffprobe"]}]},
        "semantic": {"criteria": [{"id": "intent", "name": "intent visible", "result": "pass", "evidence": ["fixture:playback"]}]},
        "context": {"status": "not_applicable", "reason": "abstract cut"},
    }))
    code, review = run_json("review-record", str(review_spec))
    assert code == 0 and review["outcome"] == "pass"
    assert (project["vault_project"] / "Records" / "reviews" / f"{review['id']}.yaml").is_file()

    score = root / "inputs" / "score.wav"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=1", str(score)], check=True)
    score_spec = root / "score.json"
    score_spec.write_text(json.dumps({"cut": str(cut), "score": str(score), "title_end_boundary": 0,
                                      "gain_db": -3, "cue_plan": {"cut_sha256": file_hash(cut), "fps": "24/1",
                                      "frame_count": 24, "time_origin": {"kind": "picture_start", "frame_boundary": 0},
                                      "cues": [{"start_frame": 0, "end_frame": 12}]}}))
    code, planned = run_json("score-plan", str(score_spec))
    assert code == 0 and planned["cut_sha256"] == file_hash(cut) and planned["frame_count"] == 24

    archive_spec = root / "archive.json"
    archive_spec.write_text(json.dumps({"manifest_path": "edit/archive.json",
                                        "files": [{"source": str(cut), "path": "outputs/review.mp4", "role": "review cut"}]}))
    assert run_json("archive", "create", str(archive_spec))[0] == 0
    code, checked = run_json("archive", "check", "edit/archive.json")
    assert code == 0 and checked["ok"] and checked["checked"] == ["outputs/review.mp4"]

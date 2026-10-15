from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from backlot import frontmatter
from backlot.errors import EXIT_BUDGET, EXIT_CONFIRM
from backlot.models import parse_model_note
from backlot.project import load_project_dir
from backlot.takes import allocate_id
from tests.conftest import FFMPEG, FakeProvider, run_cli, run_json


def test_frontmatter_roundtrip(tmp_path):
    note = tmp_path / "n.md"
    note.write_text("---\nid: x\nlist: [a, b]\nnested: {k: 1}\n---\n\n# Body\n\ntext\n")
    data, body = frontmatter.read(note)
    assert data == {"id": "x", "list": ["a", "b"], "nested": {"k": 1}}
    assert body.strip() == "# Body\n\ntext"
    frontmatter.update(note, status="stale")
    data2, body2 = frontmatter.read(note)
    assert data2["status"] == "stale" and data2["id"] == "x"
    assert body2 == body


def test_frontmatter_missing_and_malformed(tmp_path):
    assert frontmatter.split("no frontmatter") == ({}, "no frontmatter")
    with pytest.raises(ValueError):
        frontmatter.split("---\n: : bad\n  - x\n---\n")


def test_model_note_parse(studio):
    m = parse_model_note(studio["vault"] / "Studio" / "Models" / "fake-video.md")
    assert m.kind == "video" and m.cost_unit == "per_second" and m.take_prefix == "vid"
    assert m.defaults == {"duration": 4} and m.inputs == ["prompt", "image"]


def test_init_scaffold(project):
    vp = project["vault_project"]
    for rel in ("demo.md", "Brief.md", "Treatment.md", "Script.md", "Decisions.md", "Status.md", "Costs.md",
                "Context/Rules.md", "Context/World.md", "Context/Visual Language.md", "Shots/Shots.base", "Takes/Takes.base"):
        assert (vp / rel).exists(), rel
    home, _ = frontmatter.read(vp / "demo.md")
    assert home["budget_eur"] == 2 and "ask_before_generate" not in home and home["format"] == "16:9"
    assert "file.inFolder(this.file.folder)" in (vp / "Shots" / "Shots.base").read_text()
    assert (vp / "_thumbs" / ".gitkeep").exists() and (vp / "Shots" / "_template.md").exists()
    root = project["root"]
    assert (root / ".git").is_dir() and (root / ".gitignore").exists() and (root / "edit" / "timeline.yaml").exists()
    p = load_project_dir(root)
    assert p.vault_project == vp and p.budget_eur == 2


def test_gen_requires_confirmation_then_generates(project):
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "a red cube")
    assert code == EXIT_CONFIRM and data["needs_confirmation"] and data["estimate_eur"] == 0.5
    assert FakeProvider.calls == []
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "a red cube", "--yes", "--shot", "S010", "--depends-on", "Cast/Mia")
    assert code == 0 and data[0]["take"] == "img-001"
    root = project["root"]
    assert (root / "takes" / "img-001" / "out.png").exists()
    assert (root / "takes" / "img-001" / "meta.yaml").exists()
    assert (root / "takes" / "img-001" / "prompt.txt").read_text() == "a red cube"
    manifest = [json.loads(l) for l in (root / "takes" / "manifest.jsonl").read_text().splitlines()]
    assert manifest[0]["take"] == "img-001" and manifest[0]["cost_eur"] == 0.5
    note = project["vault_project"] / "Takes" / "img-001.md"
    fm, body = frontmatter.read(note)
    assert fm["status"] == "new" and fm["shot"] == "S010" and fm["depends_on"] == ["Cast/Mia"] and fm["model"] == "fake-image"
    assert "![[Projects/demo/_thumbs/img-001.jpg]]" in body and "a red cube" in body
    assert fm["type"] == "take" and fm["kind"] == "img" and fm["thumb"] == "[[Projects/demo/_thumbs/img-001.jpg]]" and fm["created"]
    assert (project["vault_project"] / "_thumbs" / "img-001.jpg").exists()
    home, _ = frontmatter.read(project["vault_project"] / "demo.md")
    assert home["spent_eur"] == 0.5
    assert "img-001" in (project["vault_project"] / "Costs.md").read_text()


def test_take_id_allocation_and_variations(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 0 and data[0]["take"] == "img-002"
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p2", "--yes", "--parent", "img-001")
    assert code == 0 and data[0]["take"] == "img-001.2" and data[0]["parent"] == "img-001"
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p3", "--yes", "--parent", "img-001.2")
    assert data[0]["take"] == "img-001.3"
    p = load_project_dir(project["root"])
    assert allocate_id(p, "img") == "img-003"
    assert allocate_id(p, "vid") == "vid-001"
    fm, _ = frontmatter.read(project["vault_project"] / "Takes" / "img-001.2.md")
    assert fm["parent"] == "img-001"


def test_budget_refusal(project):
    for _ in range(4):
        assert run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")[0] == 0
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == EXIT_BUDGET and data["budget_exceeded"]
    assert len(FakeProvider.calls) == 4
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--dry-run")
    assert code == 0 and data["dry_run"]


def test_ask_before_generate_false_does_not_skip_exact_authorization(project):
    yml = project["root"] / "project.yaml"
    data = yaml.safe_load(yml.read_text())
    data["ask_before_generate"] = False
    yml.write_text(yaml.safe_dump(data))
    code, out = run_json("gen", "img", "--model", "fake-image", "--prompt", "p")
    assert code == EXIT_CONFIRM and out["needs_confirmation"]
    assert FakeProvider.calls == []


def test_per_second_estimate_and_image_input(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    code, data = run_json("gen", "video", "--model", "fake-video", "--prompt", "move", "--image", "img-001")
    assert code == EXIT_CONFIRM and data["estimate_eur"] == pytest.approx(0.8)
    code, data = run_json("gen", "video", "--model", "fake-video", "--prompt", "move", "--image", "img-001", "--yes", "--param", "duration=2")
    assert code == 0 and data[0]["take"] == "vid-001" and data[0]["cost_eur"] == pytest.approx(0.4)
    assert FakeProvider.calls[-1][1].image.name == "out.png"
    assert (project["vault_project"] / "_thumbs" / "vid-001.jpg").exists()


def test_tts_and_waveform_thumb(project):
    code, data = run_json("tts", "--model", "fake-tts", "--voice", "v1", "--text", "hello there", "--yes", "--shot", "S010")
    assert code == 0 and data[0]["take"] == "vo-001" and data[0]["cost_eur"] == pytest.approx(0.011)
    assert (project["vault_project"] / "_thumbs" / "vo-001.jpg").exists() and not (project["vault_project"] / "_thumbs" / "vo-001.png").exists()
    fm, body = frontmatter.read(project["vault_project"] / "Takes" / "vo-001.md")
    assert "![[Projects/demo/_thumbs/vo-001.jpg]]" in body and fm["thumb"] == "[[Projects/demo/_thumbs/vo-001.jpg]]"


def test_approve_reject_and_lock(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010", "--depends-on", "Cast/Mia")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010")
    code, data = run_json("approve", "img-001", "--reason", "great light", "--lock", "Cast/Mia")
    assert code == 0 and data["status"] == "approved"
    shot, _ = frontmatter.read(project["vault_project"] / "Shots" / "S010.md")
    assert shot["board_take"] == "img-001" and shot["status"] == "approved"
    mia, _ = frontmatter.read(project["vault_project"] / "Context" / "Cast" / "Mia.md")
    assert mia["locked"] is True and mia["locked_take"] == "img-001"
    code, _ = run_json("reject", "img-002", "--reason", "wrong palette")
    assert code == 0
    decisions = (project["vault_project"] / "Decisions.md").read_text()
    lines = [l for l in decisions.splitlines() if l.startswith("- ")]
    assert "## Ledger" in decisions and decisions.index("## Ledger") < decisions.index(lines[0])
    assert "**reject** img-002 (S010) [legacy scope unverified] - wrong palette" in lines[0]
    assert "**lock** Mia" in lines[1] and "**approve** take:img-001@" in lines[2]
    assert "# Decisions" in decisions
    code, takes = run_json("takes", "--status", "approved")
    assert [t["take"] for t in takes] == ["img-001"]
    code, show = run_json("show", "img-002")
    assert show["status"] == "rejected" and show["reason"] == "wrong palette"


def test_stale_propagation(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010", "--depends-on", "Cast/Mia")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S020")
    run_json("approve", "img-002", "--reason", "ok")
    code, data = run_json("stale", "Mia", "--reason", "Mia is blonde now")
    assert code == 0 and data["takes"] == ["img-001"] and data["shots"] == ["S010"]
    fm, _ = frontmatter.read(project["vault_project"] / "Takes" / "img-001.md")
    assert fm["status"] == "stale"
    fm2, _ = frontmatter.read(project["vault_project"] / "Takes" / "img-002.md")
    assert fm2["status"] == "approved"
    s10, _ = frontmatter.read(project["vault_project"] / "Shots" / "S010.md")
    s20, _ = frontmatter.read(project["vault_project"] / "Shots" / "S020.md")
    assert s10["status"] == "stale" and s20["status"] == "approved"
    code, takes = run_json("takes", "--stale")
    assert [t["take"] for t in takes] == ["img-001"]
    assert "**stale** Mia" in (project["vault_project"] / "Decisions.md").read_text()
    code, data = run_json("stale", "Mia", "--reason", "again")
    assert code == 0 and data["takes"] == []


def test_status_and_cost_regeneration(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010")
    run_json("approve", "img-001", "--reason", "ok")
    code, data = run_json("status")
    assert code == 0
    text = (project["vault_project"] / "Status.md").read_text()
    assert text == data["status"]
    assert "0.500 / 2.00 EUR" in text and "| approved | 1 |" in text and "| planned | 1 |" in text
    assert "generate video for S010" in text and "board S020" in text
    code, data = run_json("cost")
    costs = (project["vault_project"] / "Costs.md").read_text()
    assert "| fake-image | 1 | 0.500 |" in costs and "| img-001 | img |" in costs
    home, _ = frontmatter.read(project["vault_project"] / "demo.md")
    assert home["spent_eur"] == 0.5


def test_models_listing(studio):
    code, data = run_json("models", "--kind", "image")
    assert code == 0 and [m["id"] for m in data] == ["fake-image"]
    code, data = run_json("models", "--provider", "fal")
    assert len(data) == 6
    code, out = run_cli("models")
    assert "fake-video" in out and "per_second" in out


def test_captions(project):
    run_json("tts", "--model", "fake-tts", "--text", "hello world this is a test", "--yes")
    code, data = run_json("captions", "vo-001", "--model", "fake-stt", "--yes")
    assert code == 0 and data["cues"] >= 1
    srt = Path(data["srt"])
    assert srt == project["root"] / "takes" / "vo-001" / "out.srt"
    assert "00:00:00,000 --> " in srt.read_text() and "hello world" in srt.read_text()
    words = json.loads(Path(data["words"]).read_text())
    assert len(words["words"]) == 6
    code, data = run_json("captions", "vo-001", "--model", "fake-image")
    assert code == 1


def test_doctor_runs(project):
    code, data = run_json("doctor")
    names = {c["name"]: c for c in data}
    assert names["ffmpeg"]["ok"] and names["vault"]["ok"] and names["model notes"]["ok"]
    assert names["comfyui-local"]["warn"]


def test_unknown_model_and_missing_project(studio, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code, data = run_json("gen", "img", "--model", "nope", "--prompt", "p", "--yes")
    assert code == 1 and "not inside a project" in data["error"]
    run_json("init", "x")
    code, data = run_json("gen", "img", "--model", "nope", "--prompt", "p", "--yes", "--project", "x")
    assert code == 1 and "unknown model" in data["error"]


def test_stub_providers():
    from backlot.providers import ProviderNotConfigured, get_provider

    for name in ("comfyui-cloud", "higgsfield"):
        with pytest.raises(ProviderNotConfigured, match="Providers/"):
            get_provider(name).run(None, None)


@pytest.mark.parametrize("bad", ["../../etc/passwd", "img-001/../../x", "S010", "img-1", "evil-001"])
def test_take_ids_are_validated_before_path_use(project, bad):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    for cmd in (("show", bad), ("approve", bad, "--reason", "r"), ("reject", bad, "--reason", "r")):
        code, data = run_json(*cmd)
        assert code == 1 and "invalid take id" in data["error"], (cmd, data)
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--parent", bad)
    assert code == 1 and "invalid take id" in data["error"]
    assert not (project["root"].parent / "etc").exists()


def test_shot_ids_are_validated(project):
    for bad in ("../../x", "S10", "s010", "S010/evil"):
        code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", bad)
        assert code == 1 and "invalid shot id" in data["error"], data
    assert FakeProvider.calls == []


def test_lipsync_requires_video_and_audio_before_billing(project):
    run_json("tts", "--model", "fake-tts", "--text", "hi", "--yes")
    code, data = run_json("gen", "video", "--model", "fake-lipsync", "--audio", "vo-001", "--yes")
    assert code == 1 and "needs --video" in data["error"] and FakeProvider.calls[-1][0] == "fake-tts"
    code, data = run_json("gen", "video", "--model", "fake-lipsync", "--yes")
    assert code == 1 and "--video" in data["error"] and "--audio" in data["error"]
    clip = project["root"] / "inputs" / "face.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=64x64:rate=24", "-t", "1", "-pix_fmt", "yuv420p", str(clip)], check=True)
    code, data = run_json("gen", "video", "--model", "fake-lipsync", "--video", "inputs/face.mp4", "--audio", "vo-001", "--yes", "--param", "duration=2")
    assert code == 0 and data[0]["take"] == "vid-001" and data[0]["params"]["video"].endswith("face.mp4")
    submitted = FakeProvider.calls[-1][1]
    assert submitted.video.name == clip.name and submitted.video.parent.name == "inputs"
    assert "approved-inputs" in str(submitted.video) and submitted.audio.name == "out.wav"


def test_param_types_and_min_duration(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    code, data = run_json("gen", "video", "--model", "fake-kling", "--prompt", "m", "--image", "img-001", "--yes", "--param", "duration=10")
    assert code == 0 and FakeProvider.calls[-1][1].params["duration"] == "10"
    assert data[0]["cost_eur"] == pytest.approx(1.0)
    code, data = run_json("gen", "video", "--model", "fake-kling", "--prompt", "m", "--image", "img-001", "--dry-run", "--param", "duration=2")
    assert code == 0 and data["estimate_eur"] == pytest.approx(0.5)
    code, data = run_json("gen", "video", "--model", "fake-video", "--prompt", "m", "--image", "img-001", "--dry-run", "--param", "duration=2")
    assert code == 0 and data["estimate_eur"] == pytest.approx(0.4)


def test_zero_budget_refuses_all_spend(project, studio):
    yml = project["root"] / "project.yaml"
    data = yaml.safe_load(yml.read_text())
    data["budget_eur"] = 0
    yml.write_text(yaml.safe_dump(data))
    code, out = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == EXIT_BUDGET and "budget_eur is 0" in out["error"] and FakeProvider.calls == []
    del data["budget_eur"]
    yml.write_text(yaml.safe_dump(data))
    code, out = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == EXIT_BUDGET and FakeProvider.calls == []
    code, out = run_json("init", "zero", "--budget", "0")
    assert code == 1 and "--budget must be greater than 0" in out["error"]
    assert not (studio["projects"] / "zero").exists()


def test_gen_creates_missing_shot_from_template(project):
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S999")
    assert code == 0 and data[0]["shot"] == "S999"
    note = project["vault_project"] / "Shots" / "S999.md"
    fm, body = frontmatter.read(note)
    assert fm["shot"] == "S999" and fm["status"] == "boarded" and fm["type"] == "shot" and fm["created"]
    assert body.startswith("# S999") and "## Prompt" in body and "S010" not in body
    code, text = run_cli("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S998")
    assert code == 0 and "created shot S998" in text
    (project["vault_project"] / "Shots" / "_template.md").unlink()
    (project["vault"] / "_templates" / "Shots" / "_template.md").unlink()
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S997")
    assert code == 1 and "no shot template" in data["error"]


def test_shot_status_transitions(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010")
    assert frontmatter.read(project["vault_project"] / "Shots" / "S010.md")[0]["status"] == "boarded"
    run_json("approve", "img-001", "--reason", "ok")
    assert frontmatter.read(project["vault_project"] / "Shots" / "S010.md")[0]["status"] == "approved"
    run_json("gen", "video", "--model", "fake-video", "--prompt", "m", "--image", "img-001", "--yes", "--shot", "S010", "--param", "duration=1")
    shot, _ = frontmatter.read(project["vault_project"] / "Shots" / "S010.md")
    assert shot["status"] == "generated" and shot["board_take"] == "img-001"
    run_json("approve", "vid-001", "--reason", "ok")
    shot, _ = frontmatter.read(project["vault_project"] / "Shots" / "S010.md")
    assert shot["status"] == "generated" and shot["video_take"] == "vid-001"


def test_depends_on_must_name_existing_context_notes(project):
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--depends-on", "Cast/Mia,Locations/Lighthouse,Props/Lamp")
    assert code == 1 and FakeProvider.calls == []
    assert "Locations/Lighthouse" in data["error"] and "Props/Lamp" in data["error"] and "Cast/Mia" not in data["error"]
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--depends-on", "Cast/Mia")
    assert code == 0


def test_models_shows_untested_hides_disabled(studio):
    code, data = run_json("models")
    ids = [m["id"] for m in data]
    assert "fake-kling" in ids and "fake-lipsync" in ids and "fake-edit" not in ids
    code, data = run_json("models", "--all")
    assert "fake-edit" in [m["id"] for m in data]
    code, data = run_json("models", "--kind", "video")
    assert {m["id"] for m in data} == {"fake-video", "fake-kling"}
    assert next(m for m in data if m["id"] == "fake-kling")["min_duration_s"] == 5


def test_thumb_failure_still_writes_note(project, monkeypatch):
    from backlot.errors import BacklotError as Err

    def boom(*a, **k):
        raise Err("ffmpeg failed")

    monkeypatch.setattr("backlot.gen.make_thumb", boom)
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 0
    fm, body = frontmatter.read(project["vault_project"] / "Takes" / "img-001.md")
    assert fm["thumb"] == "" and "![[" not in body

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

import pytest
import yaml

from backlot import frontmatter
from backlot.config import load_studio
from backlot.errors import EXIT_BUDGET, EXIT_CONFIRM, BacklotError
from backlot.gen import GenOptions, execute
from backlot.models import ModelSpec
from backlot.project import load_project_dir
from backlot.providers.base import GenRequest, ProviderError, build_arguments
from backlot.stages import STAGES
from tests.conftest import FFMPEG, FakeProvider, run_cli, run_json

MULTI_NOTE = """---
id: fake-multi
provider: fal
kind: image
endpoint: fal-ai/fake-multi
cost_unit: per_image
cost_eur: 0.1
status: active
inputs: [prompt, image]
arg_map: {image: image_urls}
---
"""

END_NOTE = """---
id: fake-end
provider: fal
kind: video
endpoint: fal-ai/fake-end
cost_unit: per_second
cost_eur: 0.05
status: active
inputs: [prompt, image, end_image]
optional_inputs: [image]
defaults: {duration: 2}
---
"""


def _set_project(root: Path, **changes):
    yml = root / "project.yaml"
    data = yaml.safe_load(yml.read_text())
    data.update(changes)
    yml.write_text(yaml.safe_dump(data))


def _lavfi(out: Path, *args: str) -> Path:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args, str(out)], check=True)
    return out


# 1. concurrency ----------------------------------------------------------------------------------


def test_parallel_reservations_get_distinct_ids_and_share_budget(project, monkeypatch):
    studio = load_studio()
    proj = load_project_dir(project["root"])
    seen: list[str] = []

    class Nested(FakeProvider):
        depth = 0

        def run(self, model, req):
            pending = [t for t in _takes(proj) if t["status"] == "pending"]
            seen.append(",".join(sorted(t["take"] for t in pending)))
            if Nested.depth == 0:
                Nested.depth += 1
                inner = execute(studio, proj, GenOptions(kind="img", model_id="fake-image", prompt="inner", yes=True))
                assert inner.takes[0].take == "img-002"
                with pytest.raises(BacklotError) as exc:
                    execute(studio, proj, GenOptions(kind="img", model_id="fake-image", prompt="over", yes=True, n=3))
                assert exc.value.code == EXIT_BUDGET and "1.000 + 1.500 > 2.00" in str(exc.value)
            return super().run(model, req)

    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: Nested(cfg))
    outcome = execute(studio, proj, GenOptions(kind="img", model_id="fake-image", prompt="outer", yes=True))
    assert outcome.takes[0].take == "img-001"
    assert seen == ["img-001", "img-001,img-002"]
    ids = sorted(t["take"] for t in _takes(proj))
    assert ids == ["img-001", "img-002"] and all(t["status"] == "new" for t in _takes(proj))
    assert (project["root"] / "takes" / ".lock").exists()


def test_threads_allocate_distinct_ids(project, monkeypatch):
    studio = load_studio()
    proj = load_project_dir(project["root"])

    class Slow(FakeProvider):
        def run(self, model, req):
            time.sleep(0.2)
            return super().run(model, req)

    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: Slow(cfg))
    results: list[str] = []
    errors: list[BaseException] = []

    def worker():
        try:
            results.append(execute(studio, proj, GenOptions(kind="img", model_id="fake-image", prompt="t", yes=True)).takes[0].take)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors and sorted(results) == ["img-001", "img-002", "img-003"]


def _takes(proj):
    return [yaml.safe_load(p.read_text()) for p in sorted(proj.takes_dir.glob("*/meta.yaml"))]


# 2. billed-but-unrecorded runs -------------------------------------------------------------------


class _Completed:
    pass


class _InProgress:
    pass


def _fal_client(statuses, result, request_id="req-42"):
    class Handler:
        def __init__(self):
            self.request_id = request_id
            self.calls: list[str] = []

        def status(self):
            self.calls.append("status")
            return statuses.pop(0)() if len(statuses) > 1 else statuses[0]()

        def get(self):
            self.calls.append("get")
            return result

    class Client:
        Completed = _Completed
        handler = Handler()

        def upload_file(self, p):
            return "https://up/x"

        def submit(self, endpoint, arguments):
            return self.handler

        def status(self, endpoint, request_id):
            return statuses[0]()

        def result(self, endpoint, request_id):
            return result

    return Client()


def test_fal_records_request_id_before_waiting_and_times_out(tmp_path, monkeypatch):
    from backlot.providers.fal import FalProvider

    order: list[str] = []
    client = _fal_client([_InProgress, _Completed], {"images": [{"url": "https://x/a.png", "content_type": "image/png"}]})
    monkeypatch.setattr(FalProvider, "_client", lambda self: client)
    def fake_download(url, wd, stem):
        wd.mkdir(parents=True, exist_ok=True)
        (wd / f"{stem}.png").write_bytes(b"x")
        return wd / f"{stem}.png"

    monkeypatch.setattr("backlot.providers.fal.download", fake_download)
    monkeypatch.setattr("backlot.providers.fal.time.sleep", lambda s: order.append("sleep"))
    model = ModelSpec(id="m", provider="fal", kind="image", endpoint="fal-ai/x", inputs=["prompt"])
    req = GenRequest(prompt="p", workdir=tmp_path, on_submit=lambda rid: order.append(f"submit:{rid}"))
    res = FalProvider().run(model, req)
    assert res.job_id == "req-42" and res.files[0].exists()
    assert order[0] == "submit:req-42" and client.handler.calls == ["status", "status", "get"]

    stuck = _fal_client([_InProgress], {})
    monkeypatch.setattr(FalProvider, "_client", lambda self: stuck)
    with pytest.raises(ProviderError, match=r"still running after 0 s.*backlot recover"):
        FalProvider({"timeout_s": 0.001}).run(model, GenRequest(prompt="p", workdir=tmp_path))
    assert "get" not in stuck.handler.calls

    monkeypatch.setattr(FalProvider, "_client", lambda self: client)
    fetched = FalProvider().fetch("fal-ai/x", "req-42", tmp_path / "rec")
    assert fetched.files[0].name == "out.png" and fetched.job_id == "req-42"
    monkeypatch.setattr(FalProvider, "_client", lambda self: _fal_client([_InProgress], {}))
    with pytest.raises(ProviderError, match="is _inprogress; try again later"):
        FalProvider().fetch("fal-ai/x", "req-42", tmp_path / "rec2")


def test_failed_download_keeps_take_failed_and_recover_completes_it(project, monkeypatch):
    class Flaky(FakeProvider):
        def run(self, model, req):
            req.on_submit("req-7")
            raise ProviderError("download of https://x failed: boom")

        def fetch(self, endpoint, request_id, workdir):
            assert (endpoint, request_id) == ("fal-ai/fake", "req-7")
            return FakeProvider.run(self, ModelSpec(id="fake-image", provider="fal", kind="image"), GenRequest(workdir=workdir))

    class NeverReached(FakeProvider):
        def run(self, model, req):
            raise ProviderError("no FAL_KEY")

    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: Flaky(cfg))
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010")
    assert code == 1 and "kept as failed, request req-7" in data["error"]
    meta = yaml.safe_load((project["root"] / "takes" / "img-001" / "meta.yaml").read_text())
    assert meta["status"] == "failed" and meta["request_id"] == "req-7" and meta["cost_eur"] == 0.5 and meta["endpoint"] == "fal-ai/fake"
    assert "boom" in meta["error"]
    code, rows = run_json("takes", "--status", "failed")
    assert [t["take"] for t in rows] == ["img-001"]
    assert run_json("takes", "--status", "pending")[1] == []
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--dry-run")
    assert data["spent_eur"] == 0.5
    fm, body = frontmatter.read(project["vault_project"] / "Takes" / "img-001.md")
    assert fm["status"] == "failed" and fm["request_id"] == "req-7" and "backlot recover img-001" in body
    code, data = run_json("approve", "img-001", "--reason", "x")
    assert code == 1 and "recover or discard" in data["error"]

    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: NeverReached(cfg))
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 1 and not (project["root"] / "takes" / "img-002").exists()

    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: Flaky(cfg))
    code, data = run_json("recover", "img-001")
    assert code == 0 and data["status"] == "new" and data["file"] == "takes/img-001/out.png"
    assert (project["root"] / "takes" / "img-001" / "out.png").exists()
    fm, _ = frontmatter.read(project["vault_project"] / "Takes" / "img-001.md")
    assert fm["status"] == "new" and fm["thumb"] == "[[Projects/demo/_thumbs/img-001.jpg]]"
    assert frontmatter.read(project["vault_project"] / "Shots" / "S010.md")[0]["status"] == "boarded"
    code, data = run_json("recover", "img-001")
    assert code == 1 and "only pending or failed" in data["error"]


# 3. clip audio -----------------------------------------------------------------------------------


@pytest.fixture
def clips(project):
    inputs = project["root"] / "inputs"
    talking = _lavfi(inputs / "talk.mp4", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=24", "-f", "lavfi", "-i", "sine=frequency=500", "-t", "3", "-pix_fmt", "yuv420p", "-shortest")
    silent = _lavfi(inputs / "silent.mp4", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=24", "-t", "2", "-pix_fmt", "yuv420p")
    return {"talk": talking, "silent": silent, "root": project["root"]}


def test_clip_audio_keep_is_mixed_at_timeline_position(clips):
    tl = clips["root"] / "edit" / "clip-audio.yaml"
    tl.write_text(yaml.safe_dump({
        "resolution": "320x180",
        "video": [
            {"src": "inputs/silent.mp4", "out": 1.0, "transition": {"type": "xfade", "duration": 0.5}},
            {"src": "inputs/talk.mp4", "in": 0.5, "out": 2.5, "audio": "keep", "gain_db": -3},
        ],
    }))
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 0, data
    assert "atrim=start=0.500:end=2.500,asetpts=PTS-STARTPTS" in data["command"]
    assert "volume=-3.0dB,adelay=500|500" in data["command"] and "[aout]" in data["command"]
    code, data = run_json("render", str(tl), "--preset", "draft")
    assert code == 0, data
    from backlot import ffmpeg

    assert any(s["codec_type"] == "audio" for s in ffmpeg.probe(Path(data["output"]))["streams"])
    tl.write_text(yaml.safe_dump({"video": [{"src": "inputs/silent.mp4", "audio": "keep"}]}))
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 1 and "no audio stream" in data["error"]


# 4. captions from all vo rows --------------------------------------------------------------------


def test_captions_merged_from_vo_rows_and_srt_emitted(project):
    from backlot.overlays import Cue, parse_srt, write_srt

    for text in ("first line", "second line"):
        run_json("tts", "--model", "fake-tts", "--text", text, "--yes")
    write_srt([Cue(0.0, 1.0, "first")], project["root"] / "takes" / "vo-001" / "out.srt")
    write_srt([Cue(0.0, 1.0, "second")], project["root"] / "takes" / "vo-002" / "out.srt")
    _lavfi(project["root"] / "inputs" / "bg.mp4", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=24", "-t", "5", "-pix_fmt", "yuv420p")
    tl = project["root"] / "edit" / "caps.yaml"
    base = {
        "resolution": "320x180",
        "video": [{"src": "inputs/bg.mp4"}],
        "audio": [
            {"track": "vo", "src": "vo-002", "at": 3.0},
            {"track": "vo", "src": "vo-001", "at": 1.0},
            {"track": "music", "src": "vo-001", "at": 0.0},
        ],
    }
    tl.write_text(yaml.safe_dump({**base, "captions": {"from": "vo", "burn": False}}))
    code, data = run_json("render", str(tl), "--preset", "draft")
    assert code == 0, data
    assert "overlay" not in data["command"]
    cues = parse_srt((project["root"] / "renders" / "caps-draft.srt").read_text())
    assert [(c.start, c.end, c.text) for c in cues] == [(1.0, 2.0, "first"), (3.0, 4.0, "second")]
    tl.write_text(yaml.safe_dump({**base, "captions": {"from": "vo", "burn": True}}))
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 0 and "between(t,1.000,2.000)" in data["command"] and "between(t,3.000,4.000)" in data["command"]
    tl.write_text(yaml.safe_dump({**base, "captions": {"src": "vo-002"}}))
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 0 and "between(t,3.000,4.000)" in data["command"] and "between(t,1.000" not in data["command"]
    tl.write_text(yaml.safe_dump({**base, "audio": [], "captions": {"from": "vo"}}))
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 1 and "no `track: vo` rows" in data["error"]


# 5. --parent kind --------------------------------------------------------------------------------


def test_parent_must_match_kind(project):
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    code, data = run_json("gen", "video", "--model", "fake-video", "--prompt", "m", "--image", "img-001", "--parent", "img-001", "--yes", "--param", "duration=1")
    assert code == 1 and "img-001 is a img take" in data["error"] and "vid-* parent" in data["error"]
    assert [c[0] for c in FakeProvider.calls] == ["fake-image"]
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--parent", "img-001")
    assert code == 0 and data[0]["take"] == "img-001.2"


# 7. vault wikilinks ------------------------------------------------------------------------------


def test_take_note_links_are_vault_root_relative(project):
    (project["vault_project"] / "Context" / "Locations").mkdir(exist_ok=True)
    (project["vault_project"] / "Context" / "Locations" / "Lighthouse.md").write_text("---\nlocked: false\n---\n# Lighthouse\n")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010", "--depends-on", "Cast/Mia,Lighthouse")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--parent", "img-001")
    fm, body = frontmatter.read(project["vault_project"] / "Takes" / "img-001.md")
    assert fm["thumb"] == "[[Projects/demo/_thumbs/img-001.jpg]]"
    assert "![[Projects/demo/_thumbs/img-001.jpg]]" in body
    assert "Shot: [[Projects/demo/Shots/S010|S010]]" in body
    assert "[[Projects/demo/Context/Cast/Mia|Mia]]" in body and "[[Projects/demo/Context/Locations/Lighthouse|Lighthouse]]" in body
    _, body2 = frontmatter.read(project["vault_project"] / "Takes" / "img-001.2.md")
    assert "Variation of [[Projects/demo/Takes/img-001|img-001]]" in body2


# 8. captions go through confirm + budget ---------------------------------------------------------


def test_captions_require_confirmation_and_budget(project):
    run_json("tts", "--model", "fake-tts", "--text", "hello world this is a test", "--yes")
    code, data = run_json("captions", "vo-001", "--model", "fake-stt")
    assert code == EXIT_CONFIRM and data["needs_confirmation"] and data["estimate_eur"] == 0.01
    code, data = run_json("captions", "vo-001", "--model", "fake-stt", "--dry-run")
    assert code == 0 and data["dry_run"]
    _set_project(project["root"], budget_eur=0)
    code, data = run_json("captions", "vo-001", "--model", "fake-stt", "--yes")
    assert code == EXIT_BUDGET and "budget_eur is 0" in data["error"]
    _set_project(project["root"], budget_eur=2)
    code, data = run_json("captions", "vo-001", "--model", "fake-stt", "--yes")
    assert code == 0 and data["cost_eur"] == 0.01


# 9. next actions ---------------------------------------------------------------------------------


def test_status_lists_voice_action(project):
    (project["vault_project"] / "Shots" / "S010.md").write_text("---\nshot: S010\nstatus: generated\nboard_take: img-001\nvideo_take: vid-001\n---\n")
    (project["vault_project"] / "Shots" / "S020.md").write_text("---\nshot: S020\nstatus: generated\nboard_take: img-002\nvideo_take: vid-002\nvo: false\n---\n")
    code, data = run_json("status")
    assert "- voice S010" in data["status"] and "voice S020" not in data["status"]


# 10. comfyui placeholders ------------------------------------------------------------------------


def test_comfy_frames_and_image_placeholders(tmp_path, monkeypatch):
    from backlot.providers.comfyui_local import ComfyUILocalProvider

    prov = ComfyUILocalProvider({})
    monkeypatch.setattr(prov, "_upload", lambda p: f"up/{p.name}")
    model = ModelSpec(id="m", provider="comfyui-local", kind="video", defaults={"fps": 25, "steps": 8})
    values = prov._values(model, GenRequest(prompt="p", duration_s=2.0), '{"length": "{{frames}}", "fps": "{{fps}}"}')
    assert values["frames"] == 50 and values["duration"] == 2.0
    assert "frames" not in prov._values(model, GenRequest(prompt="p", duration_s=2.0), '{"x": "{{prompt}}"}')
    assert prov._values(model, GenRequest(prompt="p", duration_s=2.0, params={"frames": 9}), '{"l": "{{frames}}"}')["frames"] == 9
    img = tmp_path / "i.png"
    img.write_bytes(b"x")
    assert prov._values(model, GenRequest(prompt="p", image=img), '{"image": "{{image}}"}')["image"] == "up/i.png"
    with pytest.raises(ProviderError, match=r"workflow template has no \{\{image\}\} node"):
        prov._values(model, GenRequest(prompt="p", image=img), '{"x": "{{prompt}}"}')


# 11. thresholds ----------------------------------------------------------------------------------


def test_thresholds_from_project_and_studio(project, studio):
    yml = yaml.safe_load((project["root"] / "project.yaml").read_text())
    assert yml["confirm_over_eur"] == 0 and yml["max_call_eur"] == 1.0 and yml["escalate_pct"] == 80
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    code, data = run_json("gen", "video", "--model", "fake-kling", "--prompt", "m", "--image", "img-001", "--yes", "--param", "duration=10.5")
    assert code == EXIT_BUDGET and data["max_call_exceeded"] and "above max_call_eur 1.00" in data["error"]
    assert len(FakeProvider.calls) == 1
    _set_project(project["root"], budget_eur=5)
    code, data = run_json("gen", "video", "--model", "fake-kling", "--prompt", "m", "--image", "img-001", "--yes", "--param", "duration=10.5", "--force")
    assert code == 0 and data[0]["cost_eur"] == pytest.approx(1.05)
    _set_project(project["root"], confirm_over_eur=0.6)
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p")
    assert code == 0 and data[0]["take"] == "img-002"
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--n", "2")
    assert code == EXIT_CONFIRM
    cfg = yaml.safe_load(studio["cfg"].read_text())
    cfg["defaults"] = {"max_call_eur": 0.2, "escalate_pct": 40}
    studio["cfg"].write_text(yaml.safe_dump(cfg))
    _set_project(project["root"], max_call_eur=None, escalate_pct=None)
    code, data = run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == EXIT_BUDGET and data["max_call_eur"] == 0.2
    code, data = run_json("status")
    assert "ESCALATE: budget at 41%" in data["status"] and "threshold 40%" in data["status"]
    assert frontmatter.read(project["vault_project"] / "Status.md")[0]["escalation"] is True
    _set_project(project["root"], escalate_pct=90)
    code, data = run_json("status")
    assert "ESCALATE" not in data["status"]


# 12. batch ---------------------------------------------------------------------------------------


def test_batch_plan(project, monkeypatch):
    plan = project["root"] / "plan.yaml"
    (project["root"] / "vo.txt").write_text("from a file\n")
    plan.write_text(yaml.safe_dump({"requests": [
        {"kind": "image", "model": "fake-image", "prompt": "a", "shot": "S010", "n": 2, "depends_on": "Cast/Mia"},
        {"kind": "tts", "model": "fake-tts", "voice": "v", "file": "vo.txt", "shot": "S010"},
        {"kind": "image", "model": "fake-image", "prompt": "b", "params": {"seed": 3}},
    ]}))
    code, data = run_json("batch", str(plan))
    assert code == EXIT_CONFIRM and data["needs_confirmation"] and data["estimate_eur"] == pytest.approx(1.511)
    assert len(data["table"]) == 5 and FakeProvider.calls == []
    code, text = run_cli("batch", str(plan), "--dry-run")
    assert code == 0 and "fake-image" in text and "total" in text
    plan.write_text(yaml.safe_dump([{"kind": "image", "model": "fake-image", "prompt": "a", "bogus": 1}]))
    code, data = run_json("batch", str(plan), "--yes")
    assert code == 1 and "unknown keys: bogus" in data["error"]
    plan.write_text(yaml.safe_dump({"requests": [
        {"kind": "image", "model": "fake-image", "prompt": "a", "shot": "S010", "n": 2, "depends_on": "Cast/Mia"},
        {"kind": "tts", "model": "fake-tts", "voice": "v", "file": "vo.txt", "shot": "S010"},
        {"kind": "image", "model": "fake-image", "prompt": "b", "params": {"seed": 3}},
    ]}))
    code, data = run_json("batch", str(plan), "--yes")
    assert code == 0 and data["takes"] == ["img-001", "img-002", "vo-001", "img-003"] and data["error"] is None
    assert FakeProvider.calls[-1][1].params == {"seed": 3} and FakeProvider.calls[2][1].text == "from a file"

    class Boom(FakeProvider):
        def run(self, model, req):
            if model.kind == "tts":
                raise ProviderError("tts down")
            return super().run(model, req)

    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: Boom(cfg))
    _set_project(project["root"], budget_eur=10)
    code, data = run_json("batch", str(plan), "--yes")
    assert code == 1 and data["failed_at"] == 2 and "tts down" in data["error"] and data["takes"] == ["img-004", "img-005"]
    _set_project(project["root"], budget_eur=0.1)
    code, data = run_json("batch", str(plan), "--yes")
    assert code == EXIT_BUDGET


# 13. stale --dry-run and transitive context ------------------------------------------------------


def test_stale_dry_run_and_transitive_context(project):
    ctx = project["vault_project"] / "Context"
    (ctx / "Locations").mkdir(exist_ok=True)
    (ctx / "Locations" / "Bar.md").write_text("---\nlocked: false\ndepends_on: [Cast/Mia]\n---\n# Bar\n")
    (ctx / "Props").mkdir(exist_ok=True)
    (ctx / "Props" / "Glass.md").write_text("---\ndepends_on: [Locations/Bar]\n---\n# Glass\n")
    (ctx / "Cast" / "Mia.md").write_text("---\nlocked: false\ndepends_on: [Props/Glass]\n---\n# Mia\n")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S020", "--depends-on", "Props/Glass")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--depends-on", "Cast/Mia")
    run_json("approve", "img-001", "--reason", "ok")
    code, data = run_json("stale", "Mia", "--reason", "blonde", "--dry-run")
    assert code == 0 and data["dry_run"] and data["takes"] == ["img-001", "img-002"] and data["shots"] == ["S010", "S020"]
    assert data["context"] == ["Locations/Bar", "Props/Glass"]
    assert frontmatter.read(project["vault_project"] / "Takes" / "img-001.md")[0]["status"] == "approved"
    assert "stale" not in (ctx / "Locations" / "Bar.md").read_text()
    code, text = run_cli("stale", "Mia", "--reason", "blonde", "--dry-run")
    assert "dry-run: would mark stale Mia" in text and "context Locations/Bar, Props/Glass" in text
    code, data = run_json("stale", "Mia", "--reason", "blonde")
    assert code == 0 and not data["dry_run"] and data["context"] == ["Locations/Bar", "Props/Glass"]
    assert frontmatter.read(project["vault_project"] / "Takes" / "img-001.md")[0]["status"] == "stale"
    bar, _ = frontmatter.read(ctx / "Locations" / "Bar.md")
    assert bar["stale"] is True and bar["stale_reason"] == "blonde"
    assert "3 context notes" not in (project["vault_project"] / "Decisions.md").read_text()
    assert "2 context notes" in (project["vault_project"] / "Decisions.md").read_text()


# 14. contact sheet -------------------------------------------------------------------------------


def test_contact_sheet(project):
    from PIL import Image

    _set_project(project["root"], budget_eur=10)
    for _ in range(5):
        run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", "S010")
    run_json("gen", "video", "--model", "fake-video", "--prompt", "m", "--image", "img-001", "--yes", "--shot", "S010", "--param", "duration=1")
    run_json("approve", "img-002", "--reason", "ok")
    shot = project["vault_project"] / "Shots" / "S010.md"
    shot.write_text(shot.read_text() + "\n## Candidates\n\nold\n\n## Notes\nkeep me\n")
    code, data = run_json("sheet", "--shot", "S010")
    assert code == 0, data
    sheet = Path(data["sheet"])
    assert sheet == project["root"] / "renders" / "sheets" / "S010.jpg" and data["takes"] == ["img-001", "img-002", "img-003", "img-004", "img-005", "vid-001"]
    with Image.open(sheet) as im:
        assert im.width <= 1600 and im.format == "JPEG" and im.height > im.width / 2
    embed = project["vault_project"] / "_thumbs" / "sheet-S010.jpg"
    assert embed.exists()
    with Image.open(embed) as im:
        assert im.width <= 512
    body = shot.read_text()
    assert body.count("## Candidates") == 1 and "old" not in body and "keep me" in body
    assert "![[Projects/demo/_thumbs/sheet-S010.jpg]]" in body and "[[Projects/demo/Takes/img-002|img-002]] (approved)" in body
    assert body.index("## Candidates") < body.index("## Notes")
    code, data = run_json("sheet", "--shot", "S010", "--kind", "img")
    assert code == 0 and data["takes"] == ["img-001", "img-002", "img-003", "img-004", "img-005"]
    assert shot.read_text().count("## Candidates") == 1
    code, data = run_json("sheet", "--shot", "S020")
    assert code == 1 and "no image/video takes" in data["error"]


# 15. stage gates ---------------------------------------------------------------------------------


def test_stage_gates_and_advance(project):
    vp = project["vault_project"]
    assert STAGES[0] == "idea" and STAGES[-1] == "delivered" and "deliver" in STAGES

    def stage_is(expected):
        assert frontmatter.read(vp / "demo.md")[0]["status"] == expected

    code, data = run_json("stage", "--advance")
    assert code == 0 and data["stage"] == "idea" and data["advanced"]
    stage_is("brief")
    code, data = run_json("stage")
    assert code == 1 and not data["passed"] and data["missing"] == ["Brief.md is still the template"]
    stage_is("brief")
    (vp / "Brief.md").write_text((vp / "Brief.md").read_text() + "\nSell the lighthouse to night owls.\n")
    code, data = run_json("stage", "--advance")
    assert code == 0 and data["next"] == "develop"
    stage_is("develop")
    code, data = run_json("stage", "--advance")
    assert code == 1 and "no `## Beats`" in data["missing"][0]
    (vp / "Script.md").write_text("---\ntype: script\n---\n# Script\n\n## Beats\n\n| Beat | Shot |\n|---|---|\n\n## VO\n")
    assert run_json("stage")[1]["missing"] == ["Script.md `## Beats` has no rows"]
    (vp / "Script.md").write_text("---\ntype: script\n---\n# Script\n\n## Beats\n\n| Beat | Shot |\n|---|---|\n| 1 | S010 |\n")
    assert run_json("stage", "--advance")[0] == 0
    stage_is("preproduction")
    code, data = run_json("stage")
    assert code == 1 and data["missing"] == ["Cast/Mia not locked"]
    frontmatter.update(vp / "Context" / "Cast" / "Mia.md", locked=True)
    assert run_json("stage", "--advance")[0] == 0
    stage_is("boards")
    code, data = run_json("stage")
    assert data["missing"] == ["S010 has no board_take", "S020 has no board_take"]
    for shot in ("S010", "S020"):
        run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes", "--shot", shot)
    run_json("approve", "img-001", "--reason", "ok")
    code, data = run_json("stage")
    assert data["missing"] == ["S020 has no board_take"]
    run_json("approve", "img-002", "--reason", "ok")
    assert run_json("stage", "--advance")[0] == 0
    stage_is("shots")
    assert run_json("stage")[1]["missing"] == ["S010 has no video_take", "S020 has no video_take"]
    for s in ("S010", "S020"):
        frontmatter.update(vp / "Shots" / f"{s}.md", video_take="vid-001")
    assert run_json("stage", "--advance")[0] == 0
    stage_is("voice")
    frontmatter.update(vp / "Shots" / "S020.md", vo=False)
    assert run_json("stage")[1]["missing"] == ["S010 has no vo_take"]
    frontmatter.update(vp / "Shots" / "S010.md", vo_take="vo-001")
    assert run_json("stage", "--advance")[0] == 0
    stage_is("score")
    assert run_json("stage")[0] == 1
    (project["root"] / "edit" / "timeline.yaml").write_text(yaml.safe_dump({"video": [{"src": "img-001", "duration": 1}], "audio": [{"track": "music", "src": "x"}]}))
    assert run_json("stage", "--advance")[0] == 0
    stage_is("assemble")
    assert run_json("stage")[1]["missing"] == ["no render of timeline.yaml in renders/"]
    (project["root"] / "renders" / "timeline-draft.mp4").write_bytes(b"x")
    assert run_json("stage", "--advance")[0] == 0
    stage_is("review")
    assert run_json("stage")[1]["missing"] == ["Review.md"]
    (vp / "Review.md").write_text("# Review\n")
    assert run_json("stage", "--advance")[0] == 0
    stage_is("deliver")
    code, data = run_json("stage", "--advance")
    assert code == 0 and data["advanced"]
    stage_is("delivered")
    code, data = run_json("stage", "--advance")
    assert code == 0 and data["passed"] and not data["advanced"] and data["next"] is None
    frontmatter.update(vp / "demo.md", status="bogus")
    assert run_json("stage")[0] == 1


# 16. repeatable media flags ----------------------------------------------------------------------


def test_repeatable_image_flags_and_end_image(project, studio):
    (studio["vault"] / "Studio" / "Models" / "fake-multi.md").write_text(MULTI_NOTE)
    (studio["vault"] / "Studio" / "Models" / "fake-end.md").write_text(END_NOTE)
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    code, data = run_json("gen", "img", "--model", "fake-multi", "--prompt", "merge", "--image", "img-001", "--image", "img-002", "--yes")
    assert code == 0 and data[0]["params"]["images"] == [str(project["root"] / "takes" / "img-001" / "out.png"), str(project["root"] / "takes" / "img-002" / "out.png")]
    req = FakeProvider.calls[-1][1]
    assert [p.parent.name for p in req.images] == ["img-001", "img-002"] and req.image.parent.name == "img-001"
    args = build_arguments(ModelSpec(id="m", provider="fal", kind="image", inputs=["prompt", "image"], arg_map={"image": "image_urls"}), req, lambda p: p.parent.name)
    assert args["image_urls"] == ["img-001", "img-002"]
    code, data = run_json("gen", "video", "--model", "fake-video", "--prompt", "m", "--image", "img-001", "--image", "img-002", "--yes")
    assert code == 1 and "single --image" in data["error"] and "image_url" in data["error"]
    assert FakeProvider.calls[-1][0] == "fake-multi"
    code, data = run_json("gen", "video", "--model", "fake-end", "--prompt", "m", "--image", "img-001", "--end-image", "img-002", "--yes")
    assert code == 0 and data[0]["params"]["end_image"].endswith("img-002/out.png")
    req = FakeProvider.calls[-1][1]
    args = build_arguments(ModelSpec(id="m", provider="fal", kind="video", inputs=["prompt", "image", "end_image"], arg_map={"end_image": "last_frame_url"}), req, lambda p: p.parent.name)
    assert args == {"prompt": "m", "image_url": "img-001", "last_frame_url": "img-002"}
    code, data = run_json("gen", "video", "--model", "fake-video", "--prompt", "m", "--image", "img-001", "--end-image", "img-002", "--yes")
    assert code == 1 and "does not take --end-image" in data["error"]


# 17. model promotion on approve ------------------------------------------------------------------


def test_approve_promotes_untested_model(project, studio):
    note = studio["vault"] / "Studio" / "Models" / "fake-kling.md"
    note.write_text(note.read_text() + "# fake-kling\n\nNotes.\n")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    run_json("gen", "video", "--model", "fake-kling", "--prompt", "m", "--image", "img-001", "--yes", "--param", "duration=5")
    code, data = run_json("approve", "vid-001", "--reason", "smooth")
    assert code == 0 and data["model_promoted"] == str(note)
    fm, body = frontmatter.read(note)
    assert fm["status"] == "active" and fm["arg_map"] == {"image": "start_image_url"}
    lines = body.strip().splitlines()
    assert "## Observed" in lines and lines[-1].startswith("- 20") and "vid-001 · 0.1 s · 0.500 EUR" in lines[-1]
    assert "Notes." in body
    run_json("gen", "video", "--model", "fake-kling", "--prompt", "m", "--image", "img-001", "--yes", "--param", "duration=5")
    code, data = run_json("approve", "vid-002", "--reason", "again")
    assert data["model_promoted"] is None and frontmatter.read(note)[1].count("- 20") == 1
    code, data = run_json("approve", "img-001", "--reason", "fine")
    assert data["model_promoted"] is None


# init: settings symlink, gitignore, inputs README -------------------------------------------------


def test_init_links_claude_settings_and_ignores_inputs(project):
    from backlot.scaffold import CLAUDE_SETTINGS

    root = project["root"]
    link = root / ".claude" / "settings.json"
    assert link.is_symlink() and link.resolve() == CLAUDE_SETTINGS.resolve() and "PreToolUse" in link.read_text()
    ignore = (root / ".gitignore").read_text().splitlines()
    assert ignore == ["takes/**/out.*", "takes/**/*.wav", "takes/**/*.mp3", "takes/**/*.mp4", "renders/", "inputs/**", "!inputs/README.md", ".DS_Store"]
    readme = root / "inputs" / "README.md"
    assert readme.read_text() == "Drop treatments, decks, footage, references here; binaries are git-ignored.\n"
    (root / "inputs" / "deck.pdf").write_bytes(b"%PDF")
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "--cached"], capture_output=True, text=True, check=True).stdout.split()
    assert "inputs/README.md" in tracked and "inputs/deck.pdf" not in tracked

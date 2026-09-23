from __future__ import annotations

import io
import json
import shutil
import subprocess
from contextlib import redirect_stdout
from pathlib import Path

import pytest
import yaml

from backlot import cli
from backlot.providers.base import BaseProvider, GenRequest, GenResult

FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

MODEL_NOTE = """---
id: fake-image
provider: fal
kind: image
endpoint: fal-ai/fake
tier: lite
cost_unit: per_image
cost_eur: 0.5
status: active
inputs: [prompt]
defaults: {image_size: square}
---
# fake-image
"""

VIDEO_NOTE = """---
id: fake-video
provider: fal
kind: video
endpoint: fal-ai/fake-video
tier: pro
cost_unit: per_second
cost_eur: 0.2
status: active
inputs: [prompt, image]
max_duration_s: 5
defaults: {duration: 4}
---
"""

TTS_NOTE = """---
id: fake-tts
provider: fal
kind: tts
endpoint: fal-ai/fake-tts
cost_unit: per_1k_chars
cost_eur: 1.0
status: active
inputs: [text, voice]
---
"""

LIPSYNC_NOTE = """---
id: fake-lipsync
provider: fal
kind: lipsync
endpoint: fal-ai/fake-lipsync
cost_unit: per_second
cost_eur: 0.1
status: untested
inputs: [video, audio]
max_duration_s: 10
---
"""

KLING_NOTE = """---
id: fake-kling
provider: fal
kind: video
endpoint: fal-ai/fake-kling
tier: pro
cost_unit: per_second
cost_eur: 0.1
status: untested
inputs: [prompt, image]
max_duration_s: 10
min_duration_s: 5
defaults: {duration: '5'}
param_types: {duration: str}
arg_map: {image: start_image_url}
---
"""

EDIT_NOTE = """---
id: fake-edit
provider: fal
kind: image
endpoint: fal-ai/fake-edit
cost_unit: per_image
cost_eur: 0.1
status: disabled
inputs: [prompt, image]
arg_map: {image: image_urls}
---
"""

STT_NOTE = """---
id: fake-stt
provider: fal
kind: stt
endpoint: fal-ai/fake-stt
cost_unit: per_run
cost_eur: 0.01
status: active
inputs: [audio]
---
"""


class FakeProvider(BaseProvider):
    """Writes a synthetic file per run; records calls. Never touches the network."""

    name = "fal"
    calls: list[tuple[str, GenRequest]] = []

    def run(self, model, req):
        FakeProvider.calls.append((model.id, req))
        req.workdir.mkdir(parents=True, exist_ok=True)
        if model.kind == "image":
            from PIL import Image

            out = req.workdir / "out.png"
            Image.new("RGB", (640, 360), (200, 30, 30)).save(out)
        elif model.kind in ("video", "lipsync"):
            out = req.workdir / "out.mp4"
            subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=24", "-t", "2", "-pix_fmt", "yuv420p", str(out)], check=True)
        else:
            out = req.workdir / "out.wav"
            subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", str(out)], check=True)
        return GenResult(files=[out], job_id="fake-job", seconds=0.1, raw={"ok": True})

    def call_json(self, model, req):
        return {
            "text": "hello world this is a test",
            "words": [
                {"text": "hello", "start": 0.0, "end": 0.4, "type": "word"},
                {"text": "world", "start": 0.5, "end": 0.9, "type": "word"},
                {"text": "this", "start": 1.0, "end": 1.2, "type": "word"},
                {"text": "is", "start": 1.2, "end": 1.3, "type": "word"},
                {"text": "a", "start": 1.3, "end": 1.4, "type": "word"},
                {"text": "test", "start": 1.4, "end": 1.8, "type": "word"},
            ],
        }


@pytest.fixture
def studio(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    projects = tmp_path / "projects"
    (vault / "Studio" / "Models").mkdir(parents=True)
    shutil.copytree(FIXTURES / "vault_templates", vault / "_templates")
    projects.mkdir()
    for name, note in (("fake-image", MODEL_NOTE), ("fake-video", VIDEO_NOTE), ("fake-tts", TTS_NOTE), ("fake-stt", STT_NOTE),
                       ("fake-lipsync", LIPSYNC_NOTE), ("fake-kling", KLING_NOTE), ("fake-edit", EDIT_NOTE)):
        (vault / "Studio" / "Models" / f"{name}.md").write_text(note)
    cfg = tmp_path / "studio.yaml"
    cfg.write_text(yaml.safe_dump({
        "vault": str(vault), "projects_root": str(projects), "currency": "EUR",
        "providers": {"fal": {"keychain_service": "fal-api", "keychain_account": "FAL_KEY"}, "comfyui-local": {"url": "http://127.0.0.1:1"}},
    }))
    monkeypatch.setenv("BACKLOT_STUDIO", str(cfg))
    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: FakeProvider(cfg))
    monkeypatch.setattr("backlot.captions.get_provider", lambda name, cfg=None: FakeProvider(cfg))
    FakeProvider.calls = []
    return {"vault": vault, "projects": projects, "cfg": cfg}


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(list(argv))
    return code, buf.getvalue()


def run_json(*argv: str):
    code, out = run_cli(*argv, "--json")
    return code, json.loads(out.strip().splitlines()[-1]) if out.strip() else None


@pytest.fixture
def project(studio, monkeypatch):
    code, info = run_json("init", "demo", "--budget", "2")
    assert code == 0, info
    root = Path(info["project_dir"])
    monkeypatch.chdir(root)
    shots = Path(info["vault_project"]) / "Shots"
    (shots / "S010.md").write_text("---\nshot: S010\nstatus: planned\nduration_s: 4\ncast: [Mia]\ndepends_on: [Cast/Mia]\n---\n# S010\n")
    (shots / "S020.md").write_text("---\nshot: S020\nstatus: planned\nduration_s: 3\ndepends_on: []\n---\n# S020\n")
    cast = Path(info["vault_project"]) / "Context" / "Cast"
    (cast / "Mia.md").write_text("---\nlocked: false\nlocked_take: null\nvoice: null\n---\n# Mia\n")
    return {"root": root, "vault_project": Path(info["vault_project"]), **studio}

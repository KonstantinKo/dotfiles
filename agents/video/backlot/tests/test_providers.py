from __future__ import annotations

from pathlib import Path

import pytest

from backlot.captions import cues_from_words, normalize_words
from backlot.models import ModelSpec
from backlot.providers.base import GenRequest, build_arguments
from backlot.providers.comfyui_local import substitute
from backlot.providers.fal import extract_media
from backlot.providers.base import ProviderError


def test_extract_media_shapes():
    assert extract_media({"images": [{"url": "https://x/a.png", "content_type": "image/png"}, {"url": "https://x/b.png"}]}) == ["https://x/a.png", "https://x/b.png"]
    assert extract_media({"video": {"url": "https://fal.media/v.mp4"}}) == ["https://fal.media/v.mp4"]
    assert extract_media({"audio": {"url": "https://x/a.wav", "content_type": "audio/wav"}}) == ["https://x/a.wav"]
    assert extract_media({"audio_url": "https://x/a.mp3", "text": "https://not-media"}) == ["https://x/a.mp3"]
    assert extract_media({"output": {"image": {"url": "https://x/i.jpg"}}}) == ["https://x/i.jpg"]
    assert extract_media({"text": "hi"}) == []


def test_build_arguments_maps_inputs(tmp_path):
    model = ModelSpec(id="m", provider="fal", kind="video", inputs=["prompt", "image", "audio"], defaults={"fps": 24}, extra={"arg_map": {"image": "start_image_url"}})
    img = tmp_path / "i.png"
    img.write_bytes(b"x")
    req = GenRequest(prompt="go", image=img, params={"fps": 30, "seed": 1})
    args = build_arguments(model, req, lambda p: f"uploaded:{p.name}")
    assert args == {"fps": 30, "prompt": "go", "start_image_url": "uploaded:i.png", "seed": 1}


def test_workflow_substitution():
    wf = {"1": {"inputs": {"text": "{{prompt}}", "width": "{{width}}", "note": "seed {{seed}} here", "keep": [1, "{{prompt}}"]}}}
    out = substitute(wf, {"prompt": "cat", "width": 512, "seed": 7})
    assert out == {"1": {"inputs": {"text": "cat", "width": 512, "note": "seed 7 here", "keep": [1, "cat"]}}}
    with pytest.raises(ProviderError, match="height"):
        substitute({"a": "{{height}}"}, {})


def test_normalize_words_shapes():
    text, items = normalize_words({"text": "a b", "chunks": [{"timestamp": [0.0, 0.5], "text": "a"}, {"timestamp": [0.6, None], "text": "b"}]})
    assert text == "a b" and [i["end"] for i in items] == [0.5, 0.6]
    _, items = normalize_words({"segments": [{"start": 1, "end": 2, "text": "seg"}]})
    assert items == [{"start": 1.0, "end": 2.0, "text": "seg"}]
    assert normalize_words({"text": "no timings"})[1] == []


def test_cues_group_words():
    words = [{"start": i * 0.3, "end": i * 0.3 + 0.25, "text": f"w{i}"} for i in range(30)]
    cues = cues_from_words(words)
    assert len(cues) > 1 and all(len(c.text) <= 42 for c in cues) and all(c.end - c.start <= 4.5 for c in cues)
    segs = [{"start": 0, "end": 3, "text": "long segment"}, {"start": 3, "end": 6, "text": "another"}]
    assert [c.text for c in cues_from_words(segs)] == ["long segment", "another"]


def test_local_provider_rejects_unknown_engine(tmp_path):
    from backlot.providers.local import LocalProvider

    model = ModelSpec(id="t", provider="local", kind="tts", endpoint="nope")
    with pytest.raises(ProviderError, match="endpoint must be one of"):
        LocalProvider().run(model, GenRequest(text="hi", workdir=tmp_path))


def test_build_arguments_list_wrap_and_nesting(tmp_path):
    img = tmp_path / "i.png"
    img.write_bytes(b"x")
    model = ModelSpec(id="m", provider="fal", kind="image", inputs=["prompt", "image"], arg_map={"image": "image_urls"})
    args = build_arguments(model, GenRequest(prompt="edit", image=img), lambda p: "u")
    assert args == {"prompt": "edit", "image_urls": ["u"]}
    model = ModelSpec(id="m", provider="fal", kind="tts", inputs=["text", "voice"], arg_map={"text": "prompt", "voice": "voice_setting.voice_id"}, defaults={"voice_setting": {"speed": 1}})
    args = build_arguments(model, GenRequest(text="hi", voice="Wise_Woman"), lambda p: "u")
    assert args == {"prompt": "hi", "voice_setting": {"speed": 1, "voice_id": "Wise_Woman"}}


def test_apply_param_types_and_min_duration_estimate():
    from backlot.models import apply_param_types, estimate_cost

    model = ModelSpec(id="m", provider="fal", kind="video", cost_unit="per_second", cost_eur=1.0, min_duration_s=5, param_types={"duration": "str", "seed": "int"})
    assert apply_param_types(model, {"duration": 10, "seed": "7", "other": 1}) == {"duration": "10", "seed": 7, "other": 1}
    assert apply_param_types(model, {"duration": 8.0}) == {"duration": "8"}
    assert estimate_cost(model, duration_s=2) == 5.0 and estimate_cost(model, duration_s=8) == 8.0


def test_rounded_minute_estimate_boundaries_and_composition_plan_duration():
    from backlot.gen import _duration
    from backlot.models import estimate_cost

    model = ModelSpec(id="music", provider="fal", kind="music", cost_unit="per_minute_ceil", cost_eur=0.552, max_duration_s=600)
    assert estimate_cost(model, duration_s=60) == 0.552
    assert estimate_cost(model, duration_s=60.001) == 1.104
    assert estimate_cost(model, duration_s=150.417) == 1.656
    assert estimate_cost(model) == 5.52
    params = {"composition_plan": {"chunks": [{"duration_ms": 26417}, {"duration_ms": 19000}, {"duration_ms": 35083}, {"duration_ms": 16042}, {"duration_ms": 12000}, {"duration_ms": 14791}, {"duration_ms": 27084}]}}
    assert _duration(model, params) == 150.417
    assert estimate_cost(model, duration_s=_duration(model, params)) == 1.656


def test_composition_plan_build_arguments_omits_empty_prompt():
    plan = {"chunks": [{"text": "[A]", "duration_ms": 3000, "positive_styles": ["instrumental"]}]}
    model = ModelSpec(id="music", provider="fal", kind="music", inputs=["prompt"])
    args = build_arguments(model, GenRequest(params={"composition_plan": plan, "output_format": "mp3_48000_320"}), lambda p: "unused")
    assert args == {"composition_plan": plan, "output_format": "mp3_48000_320"}


def test_fal_errors_are_provider_errors(tmp_path, monkeypatch):
    from backlot.providers.fal import FalProvider

    class Client:
        def upload_file(self, p):
            raise RuntimeError("boom")

        def submit(self, endpoint, arguments):
            raise ConnectionError("no route")

    monkeypatch.setattr(FalProvider, "_client", lambda self: Client())
    model = ModelSpec(id="m", provider="fal", kind="image", endpoint="fal-ai/x", inputs=["prompt"])
    with pytest.raises(ProviderError, match="fal-ai/x failed: no route"):
        FalProvider().run(model, GenRequest(prompt="p", workdir=tmp_path))
    with pytest.raises(ProviderError, match="upload of i.png failed: boom"):
        FalProvider()._upload(tmp_path / "i.png")


def test_local_provider_timeout(tmp_path, monkeypatch):
    import subprocess

    from backlot.providers.local import LocalProvider

    def slow(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))

    monkeypatch.setattr("backlot.providers.local.find_cli", lambda name: "/bin/kokoro")
    monkeypatch.setattr(subprocess, "run", slow)
    model = ModelSpec(id="kokoro", provider="local", kind="tts", endpoint="kokoro")
    with pytest.raises(ProviderError, match="timed out after 5 s.*edge-tts"):
        LocalProvider({"timeout_s": 5}).run(model, GenRequest(text="hi", workdir=tmp_path))

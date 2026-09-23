from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from backlot import ffmpeg
from backlot.overlays import Cue, parse_srt, write_srt
from backlot.reframe import crop_box
from tests.conftest import FFMPEG, run_json


def _lavfi(out: Path, *args: str) -> Path:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args, str(out)], check=True)
    return out


@pytest.fixture
def media(project):
    root = project["root"]
    inputs = root / "inputs"
    clip_a = _lavfi(inputs / "a.mp4", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24", "-t", "3", "-pix_fmt", "yuv420p")
    clip_b = _lavfi(inputs / "b.mp4", "-f", "lavfi", "-i", "smptebars=size=320x240:rate=30", "-t", "2", "-pix_fmt", "yuv420p")
    still = _lavfi(inputs / "still.png", "-f", "lavfi", "-i", "color=c=blue:size=800x600", "-frames:v", "1")
    vo = _lavfi(inputs / "vo.wav", "-f", "lavfi", "-i", "sine=frequency=660:duration=3")
    music = _lavfi(inputs / "music.wav", "-f", "lavfi", "-i", "sine=frequency=110:duration=8")
    run_json("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    write_srt([Cue(0.2, 1.0, "Hello"), Cue(1.2, 2.5, "Second line\nwraps")], inputs / "vo.srt")
    return {"a": clip_a, "b": clip_b, "still": still, "vo": vo, "music": music, "srt": inputs / "vo.srt", "root": root}


def test_render_full_timeline(media, project):
    timeline = {
        "fps": 24,
        "resolution": "640x360",
        "video": [
            {"src": "inputs/a.mp4", "in": 0.5, "out": 2.5, "transition": {"type": "xfade", "name": "fade", "duration": 0.5}},
            {"src": "img-001", "duration": 1.5, "motion": "kenburns"},
            {"src": "inputs/still.png", "duration": 1.0},
            {"src": "inputs/b.mp4", "in": 0, "out": 1.0},
        ],
        "audio": [
            {"track": "vo", "src": "inputs/vo.wav", "at": 0.5, "gain_db": 0},
            {"track": "music", "src": "inputs/music.wav", "at": 0.0, "gain_db": -14, "duck_under": "vo", "duck_db": -10},
        ],
        "captions": {"src": "inputs/vo.srt", "burn": True},
        "titles": [{"text": "Backlot test", "at": 0.0, "duration": 1.0, "style": "lower-third"}],
    }
    tl = media["root"] / "edit" / "timeline.yaml"
    tl.write_text(yaml.safe_dump(timeline))
    code, data = run_json("render", "--preset", "draft")
    assert code == 0, data
    out = Path(data["output"])
    assert out == media["root"] / "renders" / "timeline-draft.mp4" and out.exists()
    assert data["duration_s"] == pytest.approx(5.0)
    assert ffmpeg.duration(out) == pytest.approx(5.0, abs=0.2)
    assert ffmpeg.dimensions(out) == (1280, 720)
    streams = {s["codec_type"]: s for s in ffmpeg.probe(out)["streams"]}
    assert streams["video"]["codec_name"] == "h264" and streams["audio"]["codec_name"] == "aac"
    code, data = run_json("render", "-o", "renders/custom.mp4")
    assert code == 0 and ffmpeg.dimensions(Path(data["output"])) == (640, 360)


def test_render_shorts_and_video_only(media):
    tl = media["root"] / "edit" / "short.yaml"
    tl.write_text(yaml.safe_dump({"video": [{"src": "inputs/a.mp4", "out": 1.0}, {"src": "img-001", "duration": 1.0}]}))
    code, data = run_json("render", str(tl), "--preset", "shorts")
    assert code == 0, data
    out = Path(data["output"])
    assert out.name == "short-shorts.mp4" and ffmpeg.dimensions(out) == (1080, 1920)
    assert all(s["codec_type"] != "audio" for s in ffmpeg.probe(out)["streams"])
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 0 and "-filter_complex" in data["command"]


def test_render_errors(media):
    tl = media["root"] / "edit" / "bad.yaml"
    tl.write_text(yaml.safe_dump({"video": [{"src": "nope-000"}]}))
    code, data = run_json("render", str(tl))
    assert code == 1 and "cannot resolve" in data["error"]
    tl.write_text(yaml.safe_dump({"video": [{"src": "inputs/a.mp4"}], "captions": {"src": "inputs/a.mp4"}}))
    code, data = run_json("render", str(tl))
    assert code == 1 and "no .srt" in data["error"]


def test_reframe_video_and_image(media):
    code, data = run_json("reframe", "inputs/a.mp4", "--to", "9:16", "--focus", "left")
    assert code == 0, data
    assert ffmpeg.dimensions(Path(data["output"])) == (1080, 1920)
    code, data = run_json("reframe", "img-001", "--to", "1:1")
    assert code == 0 and ffmpeg.dimensions(Path(data["output"])) == (1080, 1080)
    assert Path(data["output"]).name == "img-001-1x1.png"


def test_crop_box_focus():
    assert crop_box(1920, 1080, (9, 16), "center") == (608, 1080, 656, 0)
    assert crop_box(1920, 1080, (9, 16), "left")[2] == 0
    assert crop_box(1920, 1080, (9, 16), "right")[2] == 1920 - 608
    assert crop_box(1080, 1920, (16, 9), "center") == (1080, 608, 0, 656)


def test_srt_roundtrip(tmp_path):
    cues = [Cue(0.0, 1.25, "One"), Cue(61.5, 62.0, "Two\nlines")]
    text = write_srt(cues, tmp_path / "x.srt").read_text()
    assert "00:01:01,500 --> 00:01:02,000" in text
    parsed = parse_srt(text)
    assert [(c.start, c.end, c.text) for c in parsed] == [(0.0, 1.25, "One"), (61.5, 62.0, "Two\nlines")]


def test_render_refuses_rejected_and_stale_sources(media):
    run_json("reject", "img-001", "--reason", "no")
    tl = media["root"] / "edit" / "rej.yaml"
    tl.write_text(yaml.safe_dump({"video": [{"src": "inputs/a.mp4", "out": 1.0}, {"src": "img-001", "duration": 1.0}]}))
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 1 and "img-001 (rejected)" in data["error"] and "--allow-stale" in data["error"]
    code, data = run_json("render", str(tl), "--dry-run", "--allow-stale")
    assert code == 0


def test_audio_track_out_and_fade(media):
    tl = media["root"] / "edit" / "fade.yaml"
    tl.write_text(yaml.safe_dump({
        "resolution": "320x180",
        "video": [{"src": "inputs/a.mp4", "out": 3.0}],
        "audio": [{"track": "music", "src": "inputs/music.wav", "at": 0.0, "out": 3.0, "fade_out_s": 1.0}],
    }))
    code, data = run_json("render", str(tl), "--dry-run")
    assert code == 0 and "atrim=end=3.000" in data["command"] and "afade=t=out:st=2.000:d=1.000" in data["command"]
    code, data = run_json("render", str(tl), "--preset", "draft")
    assert code == 0 and ffmpeg.duration(Path(data["output"])) == pytest.approx(3.0, abs=0.2)

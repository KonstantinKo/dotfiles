from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from backlot import archive, finishing
from backlot.errors import BacklotError


FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def _run(*args: str) -> None:
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def _media(root: Path) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    cut = root / "accepted-cut.mp4"
    _run("-f", "lavfi", "-i", "testsrc=size=160x90:rate=10:duration=2",
         "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "ultrafast",
         "-g", "10", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cut))
    score = root / "score-short.wav"
    _run("-f", "lavfi", "-i", "sine=frequency=880:sample_rate=48000:duration=0.5", str(score))
    return cut, score


def _cue_plan(cut: Path, boundary: int) -> dict:
    picture, frame_count = finishing._picture(cut)
    return {
        "cut_sha256": finishing._sha256(cut),
        "fps": f"{picture['fps'].numerator}/{picture['fps'].denominator}",
        "frame_count": frame_count,
        "time_origin": {"kind": "title_end", "frame_boundary": boundary},
        "cues": [{"id": "first-cue", "start_frame": 0, "end_frame": 3}],
    }


def test_score_mix_uses_measured_audio_and_preserves_picture(tmp_path: Path):
    cut, short_score = _media(tmp_path / "sources")
    cue_plan = _cue_plan(cut, boundary=10)
    plan = finishing.plan_score(cut, short_score, cue_plan, title_end_boundary=10, gain_db=-6.0)
    short_output = tmp_path / "short-mix.mp4"
    short_result = finishing.mix_score(plan, short_output)
    assert plan.frame_count == 20
    assert plan.base_audio_stream_indices
    assert short_result["score_duration_seconds"] == pytest.approx(0.5, abs=0.002)
    assert short_result["score_padded_seconds"] == pytest.approx(0.5, abs=0.003)
    assert short_result["score_trimmed_seconds"] == pytest.approx(0.0)
    assert short_result["picture_identity"]["verified"] is True
    assert short_result["picture_identity"]["packet_count"] == plan.frame_count

    long_score = tmp_path / "score-long.wav"
    _run("-f", "lavfi", "-i", "sine=frequency=990:sample_rate=48000:duration=2.2", str(long_score))
    long_plan = finishing.plan_score(cut, long_score, cue_plan, title_end_boundary=10, gain_db=0.0)
    long_result = finishing.mix_score(long_plan, tmp_path / "long-mix.mp4")
    assert long_result["score_duration_seconds"] == pytest.approx(2.2, abs=0.002)
    assert long_result["score_trimmed_seconds"] == pytest.approx(1.2, abs=0.003)
    assert long_result["score_padded_seconds"] == pytest.approx(0.0)


def test_score_plan_rejects_wrong_cut_boundary_and_ambiguous_audio(tmp_path: Path):
    cut, score = _media(tmp_path / "sources")
    cue_plan = _cue_plan(cut, boundary=10)
    wrong_hash = {**cue_plan, "cut_sha256": "0" * 64}
    with pytest.raises(BacklotError, match="cut_sha256"):
        finishing.plan_score(cut, score, wrong_hash, title_end_boundary=10, gain_db=-3)
    wrong_boundary = {**cue_plan, "time_origin": {"kind": "title_end", "frame_boundary": 9}}
    with pytest.raises(BacklotError, match="time origin"):
        finishing.plan_score(cut, score, wrong_boundary, title_end_boundary=10, gain_db=-3)
    before_title = {**cue_plan,
                    "time_origin": {"kind": "picture_start", "frame_boundary": 0},
                    "cues": [{"start_frame": 2, "end_frame": 4}]}
    with pytest.raises(BacklotError, match="before the title-end"):
        finishing.plan_score(cut, score, before_title, title_end_boundary=10, gain_db=-3)

    first = tmp_path / "track-1.wav"
    second = tmp_path / "track-2.wav"
    _run("-f", "lavfi", "-i", "sine=frequency=330:duration=1", str(first))
    _run("-f", "lavfi", "-i", "sine=frequency=660:duration=1", str(second))
    multi = tmp_path / "multi-track.mka"
    _run("-i", str(first), "-i", str(second), "-map", "0:a:0", "-map", "1:a:0", "-c:a", "pcm_s16le", str(multi))
    with pytest.raises(BacklotError, match="multiple audio streams"):
        finishing.plan_score(cut, multi, cue_plan, title_end_boundary=10, gain_db=-3)
    selected = finishing.plan_score(cut, multi, cue_plan, title_end_boundary=10, gain_db=-3, score_stream=1)
    assert selected.score_audio_ordinal == 1


def test_score_mix_rejects_sources_changed_after_planning(tmp_path: Path):
    cut, score = _media(tmp_path / "sources")
    plan = finishing.plan_score(cut, score, _cue_plan(cut, 10), title_end_boundary=10, gain_db=-3)
    score.write_bytes(score.read_bytes() + b"changed")
    with pytest.raises(BacklotError, match="score file changed"):
        finishing.mix_score(plan, tmp_path / "must-not-exist.mp4")
    assert not (tmp_path / "must-not-exist.mp4").exists()


def test_archive_bundle_checks_closure_and_reproduces_in_fresh_folder(tmp_path: Path):
    cut, score = _media(tmp_path / "sources")
    cue_plan = _cue_plan(cut, 10)
    plan = finishing.plan_score(cut, score, cue_plan, title_end_boundary=10, gain_db=-6)
    final = tmp_path / "final.mp4"
    finishing.mix_score(plan, final)
    recipe_file = tmp_path / "score-recipe.json"
    recipe_file.write_text(json.dumps({"gain_db": -6, "title_end_boundary": 10}), encoding="utf-8")
    recipe = {
        "kind": "backlot.finishing.mix_score",
        "inputs": {"cut": "sources/accepted-cut.mp4", "score": "sources/score-short.wav"},
        "extras": ["recipes/score-recipe.json"],
        "outputs": ["outputs/final.mp4"],
        "portability": "relative source bindings; local ffmpeg required",
    }
    manifest_path = tmp_path / "inventory" / "archive-manifest.json"
    archive.create_archive([
        {"source": cut, "path": "sources/accepted-cut.mp4", "role": "accepted picture"},
        {"source": score, "path": "sources/score-short.wav", "role": "score source"},
        {"source": recipe_file, "path": "recipes/score-recipe.json", "role": "recipe input"},
        {"source": final, "path": "outputs/final.mp4", "role": "scored output"},
    ], manifest_path, recipe=recipe)
    assert archive.check_archive(manifest_path)["ok"] is True

    bundle = tmp_path / "fresh-bundle"
    result = archive.bundle_archive(manifest_path, bundle)
    assert result["ok"] is True and result["bundle_files_verified"] is True
    assert result["backup_verified"] is False and result["reproduction_verified"] is False
    bundle_cut = bundle / "sources" / "accepted-cut.mp4"
    bundle_score = bundle / "sources" / "score-short.wav"
    bundled_cues = _cue_plan(bundle_cut, 10)
    reproduced = bundle / "reproduction" / "scored.mp4"
    reproduced.parent.mkdir()
    reproduced_result = finishing.mix_score(
        finishing.plan_score(bundle_cut, bundle_score, bundled_cues, title_end_boundary=10, gain_db=-6),
        reproduced,
    )
    assert reproduced_result["picture_identity"]["verified"] is True
    assert reproduced_result["sha256"] == finishing._sha256(bundle / "outputs" / "final.mp4")

    with pytest.raises(BacklotError, match="new directory"):
        archive.bundle_archive(manifest_path, bundle)


def test_archive_check_reports_missing_mutated_and_unsafe_members(tmp_path: Path):
    source = tmp_path / "selected.bin"
    source.write_bytes(b"declared source")
    manifest = tmp_path / "inventory" / "archive.json"
    archive.create_archive([{"source": source, "path": "sources/selected.bin", "role": "input"}], manifest)
    source.write_bytes(b"mutated source")
    check = archive.check_archive(manifest)
    assert check["ok"] is False and check["mutated"][0]["path"] == "sources/selected.bin"
    with pytest.raises(BacklotError, match="mutated"):
        archive.bundle_archive(manifest, tmp_path / "should-not-be-created")

    source.write_bytes(b"declared source")
    manifest2 = tmp_path / "inventory" / "archive-missing.json"
    archive.create_archive([{"source": source, "path": "sources/selected.bin", "role": "input"}], manifest2)
    source.unlink()
    assert archive.check_archive(manifest2)["missing"] == ["sources/selected.bin"]

    bad_manifest = tmp_path / "inventory" / "bad.json"
    bad_manifest.write_text(json.dumps({"schema_version": 1, "files": [{
        "path": "../escape", "source_path": str(tmp_path), "role": "input", "size_bytes": 0, "sha256": "0" * 64,
    }]}), encoding="utf-8")
    with pytest.raises(BacklotError, match="escapes"):
        archive.check_archive(bad_manifest)

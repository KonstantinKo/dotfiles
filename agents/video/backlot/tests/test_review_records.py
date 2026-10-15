from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from backlot import decisions, reviews, takes
from backlot.authority import file_hash
from backlot.errors import BacklotError
from backlot.project import load_project_dir

FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
NOW = "2026-10-02T09:00:00Z"


def _video(path: Path, color: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"color=c={color}:s=64x64:r=24", "-t", "2", "-pix_fmt", "yuv420p",
                    str(path)], check=True)
    return path


@pytest.fixture
def subject(project, tmp_path):
    proj = load_project_dir(project["root"])
    media = _video(tmp_path / "source.mp4", "red")
    take = takes.Take(
        take="vid-001", kind="vid", model="fixture", provider="local",
        original_request={"prompt": "one red square", "source": "fixture"},
        effective_request={"route": "local", "prompt": "one red square", "seed": 7},
        source_refs=[{"id": "ref-1", "sha256": "a" * 64}],
    )
    take = takes.save_take(proj, take, media)
    return proj, take


def _source(kind="review_playback", ref="fixture:review-1"):
    return {"kind": kind, "ref": ref, "observed_at": NOW}


def _criterion(result="fail", criterion_id="mid-morph", *, evidence="playback:mid"):
    return {"id": criterion_id, "name": "subject remains singular through motion",
            "result": result, "timecodes": ["00:00:01.000"], "evidence": [evidence]}


def _review_spec(take, *, presentation=True, coverage="full_playback", semantic=None,
                 context=None, accepted_limits=None):
    return {
        "subject": {"kind": "take", "id": take.take, "sha256": take.sha256},
        "source": _source(),
        "coverage": {"mode": coverage, "ranges": ([{"start_s": 0, "end_s": 2}]
                                                       if coverage == "sampled" else [])},
        "technical": {"checks": [
            {"name": "full decode", "result": "pass", "evidence": ["ffmpeg:decode"]},
            {"name": "start and end frame", "result": "pass", "evidence": ["frames:0,47"]},
        ]},
        "semantic": {"criteria": semantic or [_criterion()]},
        "context": context or {"status": "not_applicable", "reason": "standalone clip"},
        "presentation": ({"status": "presented", "kind": "user_message",
                           "ref": "thread:review-shown", "observed_at": NOW}
                          if presentation else None),
        "accepted_limits": accepted_limits or [],
    }


def _plan_spec(review_id, *, targets=None, reopen_limits=None):
    return {
        "parent_review_id": review_id,
        "repair_kind": "provider_job",
        "target_criteria": targets or ["mid-morph"],
        "changes": [{"field": "prompt", "before": "one red square", "after": "one stable red square",
                     "reason": "address the observed mid-shot morph"}],
        "source": _source("user_message", "thread:repair-request"),
        **({"reopen_limits": reopen_limits} if reopen_limits is not None else {}),
    }


def test_decode_and_endpoints_do_not_make_midshot_semantic_failure_pass(subject):
    proj, take = subject
    record = reviews.register_review(proj, _review_spec(take))

    assert record["technical"]["status"] == "pass"
    assert record["semantic"]["criteria"][0]["result"] == "fail"
    assert record["outcome"] == "fail"
    assert record["listening"]["status"] == "unsupported"
    assert "user_decision" not in record


def test_sampled_pass_is_limited_and_technical_only_cannot_claim_semantic_pass(subject):
    proj, take = subject
    sampled = reviews.register_review(
        proj, _review_spec(take, coverage="sampled", semantic=[_criterion("pass")]))
    assert sampled["outcome"] == "pass_limited"

    technical_only = _review_spec(take, coverage="technical_only", semantic=[_criterion("pass")])
    with pytest.raises(BacklotError, match="technical-only evidence"):
        reviews.register_review(proj, technical_only)


def test_listening_failure_blocks_otherwise_passing_review(subject):
    proj, take = subject
    spec = _review_spec(
        take,
        semantic=[_criterion("pass")],
        context={"criteria": [_criterion("pass", "splice", evidence="cut-review:join")]},
    )
    spec["listening"] = {"criteria": [_criterion("fail", "score-level", evidence="audio:mix")]}

    record = reviews.register_review(proj, spec)

    assert record["semantic"]["status"] == "pass"
    assert record["context"]["status"] == "pass"
    assert record["listening"]["status"] == "fail"
    assert record["outcome"] == "fail"


def test_pending_listening_blocks_but_not_applicable_listening_allows_silent_review(subject):
    proj, take = subject
    base = _review_spec(
        take,
        semantic=[_criterion("pass")],
        context={"status": "not_applicable", "reason": "standalone clip"},
    )
    pending_spec = {**base, "listening": {"status": "pending", "reason": "audio review not done"}}
    pending = reviews.register_review(proj, pending_spec)
    assert pending["listening"]["status"] == "pending"
    assert pending["outcome"] == "pending"

    not_applicable_spec = {**base, "listening": {"status": "not_applicable", "reason": "silent clip"}}
    not_applicable = reviews.register_review(proj, not_applicable_spec)
    assert not_applicable["listening"]["status"] == "not_applicable"
    assert not_applicable["outcome"] == "pass"


def test_review_and_repair_bind_exact_parent_bytes_and_require_presented_first_pass(subject):
    proj, take = subject
    wrong_hash = _review_spec(take)
    wrong_hash["subject"]["sha256"] = "0" * 64
    with pytest.raises(BacklotError, match="hash differs"):
        reviews.register_review(proj, wrong_hash)

    unpresented = reviews.register_review(proj, _review_spec(take, presentation=False))
    with pytest.raises(BacklotError, match="present the first-pass review"):
        reviews.plan_repair(proj, _plan_spec(unpresented["id"]))

    review = reviews.register_review(proj, _review_spec(take))
    path = takes.take_file(proj, take.take)
    path.write_bytes(path.read_bytes() + b"changed after review")
    with pytest.raises(BacklotError, match="bytes do not match"):
        reviews.plan_repair(proj, _plan_spec(review["id"]))


def test_repair_cannot_reopen_accepted_limit_without_sourced_user_reopening(subject):
    proj, take = subject
    accepted = decisions.record_decision(
        proj, "accept-limit", "take", take.take, version=take.sha256,
        scope="this take", reason="minor age drift accepted for this cut",
        source_ref="thread:decision-1", source_message="Accept the age drift in this cut.")
    semantic = [_criterion("fail", "mid-morph"), _criterion("fail", "accepted-age", evidence="playback:age")]
    review = reviews.register_review(
        proj, _review_spec(take, semantic=semantic,
                           accepted_limits=[{"criterion_id": "accepted-age", "decision_id": accepted["id"]}]))

    with pytest.raises(BacklotError, match="accepted limitation"):
        reviews.plan_repair(proj, _plan_spec(review["id"], targets=["accepted-age"]))

    repair = reviews.plan_repair(proj, _plan_spec(review["id"], targets=["mid-morph"]))
    assert repair["inherited_accepted_limits"][0]["criterion_id"] == "accepted-age"

    later = reviews.register_review(proj, _review_spec(take, semantic=semantic))
    assert later["accepted_limits"][0]["decision_id"] == accepted["id"]
    with pytest.raises(BacklotError, match="accepted limitation"):
        reviews.plan_repair(proj, _plan_spec(later["id"], targets=["accepted-age"]))

    reopen = {"decision_id": accepted["id"], "source_kind": "user_message",
              "source_ref": "thread:reopen-1", "source_message": "Please reopen age drift for this cut.",
              "observed_at": NOW}
    reopened = reviews.plan_repair(proj, _plan_spec(review["id"], targets=["accepted-age"],
                                                      reopen_limits=[reopen]))
    assert reopened["reopened_limits"][0]["ref"] == "thread:reopen-1"


def test_identical_output_cannot_be_effective_and_context_failure_survives_target_fix(subject):
    proj, take = subject
    review = reviews.register_review(proj, _review_spec(take))
    plan = reviews.plan_repair(proj, _plan_spec(review["id"]))
    target_pass = {"criteria": [_criterion("pass")]}

    with pytest.raises(BacklotError, match="byte-identical"):
        reviews.record_repair_result(proj, {
            "repair_id": plan["id"], "source": _source("human_playback", "fixture:repair-review"),
            "job_status": "completed", "target_outcome": "effective",
            "output": {"kind": "take", "id": take.take, "sha256": take.sha256},
            "target_review": target_pass,
        })
    unchanged = reviews.record_repair_result(proj, {
        "repair_id": plan["id"], "source": _source("human_playback", "fixture:repair-review"),
        "job_status": "completed", "target_outcome": "ineffective",
        "output": {"kind": "take", "id": take.take, "sha256": take.sha256},
        "target_review": target_pass,
    })
    assert unchanged["byte_identical_to_parent"] is True
    assert unchanged["outcome"] == "ineffective"

    output = _video(proj.renders_dir / "repaired.mp4", "blue")
    still_failing = reviews.record_repair_result(proj, {
        "repair_id": plan["id"], "source": _source("human_playback", "fixture:repair-review"),
        "job_status": "completed", "target_outcome": "effective",
        "output": {"kind": "render", "id": "repaired.mp4", "sha256": file_hash(output)},
        "target_review": {"criteria": [_criterion("fail")]},
    })
    assert still_failing["outcome"] == "ineffective"

    result = reviews.record_repair_result(proj, {
        "repair_id": plan["id"], "source": _source("human_playback", "fixture:repair-review"),
        "job_status": "completed", "target_outcome": "effective",
        "output": {"kind": "render", "id": "repaired.mp4", "sha256": file_hash(output)},
        "target_review": target_pass,
        "context": {"criteria": [{"id": "splice", "name": "join matches adjacent shot",
                                   "result": "fail", "timecodes": ["00:00:01.900"],
                                   "evidence": ["cut-review:join"]}]},
    })
    assert result["target_review"]["status"] == "pass"
    assert result["outcome"] == "context_fail"
    assert result["approval_changed"] is False


def test_failed_job_does_not_invent_moderation_cause(subject):
    proj, take = subject
    review = reviews.register_review(proj, _review_spec(take))
    plan = reviews.plan_repair(proj, _plan_spec(review["id"]))
    result = reviews.record_repair_result(proj, {
        "repair_id": plan["id"], "source": _source("job_log", "fixture:failed-job"),
        "job_status": "failed", "target_outcome": "pending",
        "failure": {"message": "The fictional moderation system rejected it."},
    })
    assert result["failure"] is None
    assert result["failure_cause"] == "failed; cause unavailable"
    assert result["outcome"] == "pending"

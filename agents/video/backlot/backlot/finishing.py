"""Small, cut-bound score finishing helpers.

This module only adds a score to an already accepted picture. It stream-copies
the picture, mixes every existing audio stream with one explicitly selected
score stream, and verifies the encoded video packet sequence after the mux.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from backlot import ffmpeg
from backlot.authority import file_hash as _sha256
from backlot.errors import BacklotError


@dataclass(frozen=True)
class ScorePlan:
    cut: Path
    score: Path
    cut_sha256: str
    score_sha256: str
    fps: Fraction
    frame_count: int
    width: int
    height: int
    title_end_boundary: int
    score_audio_ordinal: int
    score_stream_index: int
    score_sample_rate: int
    score_sample_count: int
    base_audio_stream_indices: tuple[int, ...]
    sample_rate: int
    target_sample_count: int
    gain_db: float
    cues: tuple[dict[str, Any], ...]

    @property
    def picture_duration(self) -> Fraction:
        return Fraction(self.frame_count, 1) / self.fps

    @property
    def score_start(self) -> Fraction:
        return Fraction(self.title_end_boundary, 1) / self.fps

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["cut"] = str(self.cut)
        data["score"] = str(self.score)
        data["fps"] = f"{self.fps.numerator}/{self.fps.denominator}"
        data["picture_duration"] = float(self.picture_duration)
        data["score_start"] = float(self.score_start)
        return data


def _json_probe(args: list[str], *, subject: Path) -> dict[str, Any]:
    tool = ffmpeg.which("ffprobe")
    if not tool:
        raise BacklotError("ffprobe not found")
    proc = subprocess.run([tool, *args, str(subject)], capture_output=True, text=True, check=False)
    if proc.returncode:
        raise BacklotError(f"ffprobe failed on {subject}: {proc.stderr.strip()[-300:]}")
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise BacklotError(f"ffprobe returned invalid JSON for {subject}") from exc


def _rate(value: Any, label: str) -> Fraction:
    try:
        if isinstance(value, str) and "/" in value:
            numerator, denominator = value.split("/", 1)
            result = Fraction(int(numerator), int(denominator))
        else:
            result = Fraction(str(value))
    except (ValueError, ZeroDivisionError, TypeError) as exc:
        raise BacklotError(f"{label} must be a positive frame or sample rate") from exc
    if result <= 0:
        raise BacklotError(f"{label} must be a positive frame or sample rate")
    return result


def _picture(path: Path) -> tuple[dict[str, Any], int]:
    data = _json_probe(
        ["-v", "error", "-count_frames", "-select_streams", "v:0", "-show_streams",
         "-show_entries", "stream=codec_name,width,height,avg_frame_rate,r_frame_rate,nb_read_frames",
         "-of", "json"],
        subject=path,
    )
    streams = data.get("streams") or []
    if not streams:
        raise BacklotError(f"accepted cut has no video stream: {path}")
    stream = streams[0]
    average = stream.get("avg_frame_rate")
    if not average or average == "0/0":
        average = stream.get("r_frame_rate")
    fps = _rate(average, f"{path} frame rate")
    nominal = stream.get("r_frame_rate")
    if nominal and _rate(nominal, f"{path} nominal frame rate") != fps:
        raise BacklotError(f"accepted cut has an ambiguous or variable frame rate: {path}")
    try:
        frame_count = int(stream.get("nb_read_frames"))
        width, height = int(stream["width"]), int(stream["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise BacklotError(f"cannot measure frames and dimensions for {path}") from exc
    if frame_count <= 0 or width <= 0 or height <= 0:
        raise BacklotError(f"accepted cut has invalid picture metadata: {path}")
    return {**stream, "fps": fps, "frame_count": frame_count}, frame_count


def _audio_streams(path: Path) -> list[dict[str, Any]]:
    data = ffmpeg.probe(path)
    return [stream for stream in (data.get("streams") or []) if stream.get("codec_type") == "audio"]


def _decoded_samples(path: Path, ordinal: int, stream: dict[str, Any]) -> tuple[int, int]:
    try:
        sample_rate = int(stream.get("sample_rate"))
    except (TypeError, ValueError) as exc:
        raise BacklotError(f"cannot measure sample rate for audio stream {ordinal} in {path}") from exc
    if sample_rate <= 0:
        raise BacklotError(f"invalid sample rate for audio stream {ordinal} in {path}")
    data = _json_probe(
        ["-v", "error", "-select_streams", f"a:{ordinal}", "-show_frames",
         "-show_entries", "frame=nb_samples", "-of", "json"],
        subject=path,
    )
    samples = sum(int(frame.get("nb_samples") or 0) for frame in data.get("frames") or [])
    if samples <= 0:
        # Some demuxers expose duration only at stream level. The decoded frame
        # count above is preferred because it reflects the selected audio data.
        try:
            duration_ts = int(stream["duration_ts"])
            time_base = _rate(stream["time_base"], f"{path} audio time base")
            samples = int(round(Fraction(duration_ts, 1) * time_base * sample_rate))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            samples = 0
    if samples <= 0:
        raise BacklotError(f"cannot measure decoded audio samples for stream {ordinal} in {path}")
    return sample_rate, samples


def _validate_cue_plan(cue_plan: dict[str, Any], *, cut_hash: str, fps: Fraction,
                       frame_count: int, title_end_boundary: int) -> tuple[dict[str, Any], ...]:
    if not isinstance(cue_plan, dict):
        raise BacklotError("cue_plan must be a JSON object bound to the accepted cut")
    if cue_plan.get("cut_sha256") != cut_hash:
        raise BacklotError("cue plan cut_sha256 does not match the accepted cut")
    if _rate(cue_plan.get("fps"), "cue plan fps") != fps:
        raise BacklotError("cue plan frame rate does not match the accepted cut")
    planned_frames = cue_plan.get("frame_count")
    if isinstance(planned_frames, bool) or not isinstance(planned_frames, int):
        raise BacklotError("cue plan needs an integer accepted cut frame_count")
    if planned_frames != frame_count:
        raise BacklotError("cue plan frame_count does not match the accepted cut")
    origin = cue_plan.get("time_origin")
    if not isinstance(origin, dict) or origin.get("kind") not in {"picture_start", "title_end"}:
        raise BacklotError("cue plan time_origin.kind must be picture_start or title_end")
    expected_origin_frame = 0 if origin["kind"] == "picture_start" else title_end_boundary
    origin_frame = origin.get("frame_boundary")
    if isinstance(origin_frame, bool) or not isinstance(origin_frame, int) or origin_frame != expected_origin_frame:
        raise BacklotError("cue plan time origin does not match the declared picture/title boundary")
    cues = cue_plan.get("cues")
    if not isinstance(cues, list):
        raise BacklotError("cue plan cues must be a list of frame-boundary cues")
    converted = []
    for index, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise BacklotError(f"cue {index + 1} must be an object")
        try:
            start, end = cue["start_frame"], cue["end_frame"]
        except KeyError as exc:
            raise BacklotError(f"cue {index + 1} needs integer start_frame and end_frame") from exc
        if (isinstance(start, bool) or isinstance(end, bool) or
                not isinstance(start, int) or not isinstance(end, int)):
            raise BacklotError(f"cue {index + 1} needs integer start_frame and end_frame")
        if start < 0 or end <= start:
            raise BacklotError(f"cue {index + 1} must cover a positive frame range")
        absolute_start = start if origin["kind"] == "picture_start" else title_end_boundary + start
        absolute_end = end if origin["kind"] == "picture_start" else title_end_boundary + end
        if absolute_start < title_end_boundary:
            raise BacklotError(f"cue {index + 1} starts before the title-end score boundary")
        if absolute_end > frame_count:
            raise BacklotError(f"cue {index + 1} extends beyond the accepted cut")
        converted.append({**cue, "start_frame": absolute_start, "end_frame": absolute_end})
    return tuple(converted)


def plan_score(cut: Path, score: Path, cue_plan: dict[str, Any], *, title_end_boundary: int,
               gain_db: float, score_stream: int | None = None) -> ScorePlan:
    """Plan a score mix using measured files and zero-based frame boundaries.

    ``title_end_boundary`` is the count of picture frames before score begins,
    so a value equal to frame_count starts at the final picture boundary.
    Cue ranges use half-open frame intervals relative to their declared origin.
    """
    cut, score = Path(cut).expanduser().resolve(), Path(score).expanduser().resolve()
    if not cut.is_file() or not score.is_file():
        raise BacklotError("accepted cut and score files must both exist")
    if cut == score:
        raise BacklotError("accepted cut and score must be different files")
    try:
        gain_db = float(gain_db)
    except (TypeError, ValueError) as exc:
        raise BacklotError("gain_db must be an explicit finite number") from exc
    if not math.isfinite(gain_db):
        raise BacklotError("gain_db must be an explicit finite number")
    picture, frame_count = _picture(cut)
    if isinstance(title_end_boundary, bool) or not isinstance(title_end_boundary, int):
        raise BacklotError("title_end_boundary must be an integer frame boundary")
    boundary = title_end_boundary
    if not 0 <= boundary <= frame_count:
        raise BacklotError(f"title_end_boundary must be between 0 and {frame_count}")
    cut_hash, score_hash = _sha256(cut), _sha256(score)
    cues = _validate_cue_plan(cue_plan, cut_hash=cut_hash, fps=picture["fps"],
                              frame_count=frame_count, title_end_boundary=boundary)
    selected_streams = _audio_streams(score)
    if not selected_streams:
        raise BacklotError(f"score has no audio stream: {score}")
    if score_stream is None:
        if len(selected_streams) != 1:
            raise BacklotError("score has multiple audio streams; pass score_stream to select one explicitly")
        score_ordinal = 0
    else:
        if isinstance(score_stream, bool) or not isinstance(score_stream, int):
            raise BacklotError("score_stream must be an integer audio stream ordinal")
        score_ordinal = score_stream
    if not 0 <= score_ordinal < len(selected_streams):
        raise BacklotError(f"score_stream must select one of {len(selected_streams)} audio streams")
    score_info = selected_streams[score_ordinal]
    score_rate, score_samples = _decoded_samples(score, score_ordinal, score_info)
    base_streams = _audio_streams(cut)
    base_indices = tuple(int(stream["index"]) for stream in base_streams)
    sample_rates = [score_rate]
    for index, stream in enumerate(base_streams):
        try:
            rate = int(stream.get("sample_rate"))
        except (TypeError, ValueError) as exc:
            raise BacklotError(f"cannot measure sample rate for base audio stream {index} in {cut}") from exc
        if rate <= 0:
            raise BacklotError(f"invalid sample rate for base audio stream {index} in {cut}")
        sample_rates.append(rate)
    mix_rate = max(sample_rates)
    target_samples = int(round(Fraction(frame_count, 1) / picture["fps"] * mix_rate))
    if target_samples <= 0:
        raise BacklotError("accepted cut has no measurable picture duration")
    return ScorePlan(
        cut=cut, score=score, cut_sha256=cut_hash, score_sha256=score_hash,
        fps=picture["fps"], frame_count=frame_count, width=int(picture["width"]),
        height=int(picture["height"]), title_end_boundary=boundary,
        score_audio_ordinal=score_ordinal, score_stream_index=int(score_info["index"]),
        score_sample_rate=score_rate, score_sample_count=score_samples,
        base_audio_stream_indices=base_indices, sample_rate=mix_rate,
        target_sample_count=target_samples, gain_db=gain_db, cues=cues,
    )


def _video_packets(path: Path) -> dict[str, Any]:
    data = _json_probe(
        ["-v", "error", "-select_streams", "v:0", "-show_streams", "-show_packets",
         "-show_data_hash", "sha256", "-show_entries",
         "stream=codec_name,width,height,avg_frame_rate:packet=pts_time,duration_time,data_hash", "-of", "json"],
        subject=path,
    )
    streams = data.get("streams") or []
    packets = data.get("packets") or []
    if not streams or not packets or any(not packet.get("data_hash") for packet in packets):
        raise BacklotError(f"cannot verify encoded picture packet identity for {path}")
    first_pts = float(packets[0].get("pts_time") or 0.0)
    normalized = []
    for packet in packets:
        try:
            if packet.get("pts_time") in (None, "N/A") or packet.get("duration_time") in (None, "N/A"):
                raise ValueError
            pts = float(packet["pts_time"]) - first_pts
            duration = float(packet["duration_time"])
        except (TypeError, ValueError) as exc:
            raise BacklotError(f"cannot verify picture packet timing for {path}") from exc
        if not math.isfinite(pts) or not math.isfinite(duration) or duration <= 0:
            raise BacklotError(f"cannot verify picture packet timing for {path}")
        normalized.append((packet["data_hash"], pts, duration))
    return {"stream": streams[0], "packets": normalized}


def _verify_picture(plan: ScorePlan, output: Path) -> dict[str, Any]:
    source = _video_packets(plan.cut)
    result = _video_packets(output)
    before, after = source["stream"], result["stream"]
    for key in ("codec_name", "width", "height"):
        if before.get(key) != after.get(key):
            raise BacklotError(f"score mix changed accepted picture {key}")
    if _rate(after.get("avg_frame_rate"), "mixed picture frame rate") != plan.fps:
        raise BacklotError("score mix changed accepted picture frame rate")
    if len(source["packets"]) != len(result["packets"]):
        raise BacklotError("score mix changed accepted picture packet count")
    tolerance = max(float(Fraction(1, 1) / plan.fps) / 1000, 1e-6)
    for i, (old, new) in enumerate(zip(source["packets"], result["packets"])):
        if old[0] != new[0]:
            raise BacklotError(f"score mix changed accepted picture packet {i + 1}")
        if abs(old[1] - new[1]) > tolerance or abs(old[2] - new[2]) > tolerance:
            raise BacklotError(f"score mix changed accepted picture timing at packet {i + 1}")
    return {"verified": True, "packet_count": len(source["packets"]),
            "packet_sequence_sha256": hashlib.sha256("\n".join(p[0] for p in source["packets"]).encode()).hexdigest()}


def mix_score(plan: ScorePlan, output: Path) -> dict[str, Any]:
    """Create a score variant, keeping the encoded accepted picture unchanged."""
    if not isinstance(plan, ScorePlan):
        raise BacklotError("mix_score needs a ScorePlan returned by plan_score")
    requested_output = Path(output).expanduser()
    if requested_output.exists() or requested_output.is_symlink():
        raise BacklotError(f"score output already exists: {requested_output}")
    output = requested_output.resolve()
    if output in (plan.cut, plan.score):
        raise BacklotError("score output must be a new path separate from its sources")
    if _sha256(plan.cut) != plan.cut_sha256:
        raise BacklotError("accepted cut changed after score planning")
    if _sha256(plan.score) != plan.score_sha256:
        raise BacklotError("score file changed after score planning")
    ffm = ffmpeg.which("ffmpeg")
    if not ffm:
        raise BacklotError("ffmpeg not found")
    start_samples = int(round(plan.score_start * plan.sample_rate))
    target_samples = plan.target_sample_count
    filters = []
    labels = []
    for ordinal, stream_index in enumerate(plan.base_audio_stream_indices):
        label = f"base{ordinal}"
        filters.append(
            f"[0:a:{ordinal}]aresample={plan.sample_rate}:async=1:first_pts=0,"
            f"atrim=end_sample={target_samples}[{label}]"
        )
        labels.append(f"[{label}]")
    gain = f"{plan.gain_db:.8f}dB"
    filters.append(
        f"[1:a:{plan.score_audio_ordinal}]aresample={plan.sample_rate},asetpts=PTS-STARTPTS,"
        f"volume={gain},adelay={start_samples}S:all=1,apad=whole_len={target_samples},"
        f"atrim=end_sample={target_samples}[score]"
    )
    labels.append("[score]")
    if len(labels) == 1:
        filters.append(f"{labels[0]}anull,atrim=end_sample={target_samples}[outa]")
    else:
        filters.append(
            f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,"
            f"apad=whole_len={target_samples},atrim=end_sample={target_samples}[outa]"
        )
    graph = ";".join(filters)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [ffm, "-n", "-hide_banner", "-loglevel", "error", "-i", str(plan.cut),
               "-i", str(plan.score), "-filter_complex", graph, "-map", "0:v:0", "-map", "[outa]",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", str(plan.sample_rate),
               "-map_metadata", "-1"]
    if output.suffix.lower() in {".mp4", ".m4v", ".mov"}:
        command += ["-movflags", "+faststart"]
    command.append(str(output))
    try:
        ffmpeg.run(command)
        if not output.is_file() or output.stat().st_size <= 0:
            raise BacklotError("ffmpeg produced no score mix output")
        picture = _picture(output)[0]
        if int(picture["frame_count"]) != plan.frame_count:
            raise BacklotError("score mix changed accepted picture frame count")
        identity = _verify_picture(plan, output)
        output_probe = ffmpeg.probe(output)
        audio_count = sum(1 for stream in output_probe.get("streams") or [] if stream.get("codec_type") == "audio")
        if audio_count != 1:
            raise BacklotError(f"score mix produced {audio_count} audio streams; expected one mixed stream")
    except Exception:
        output.unlink(missing_ok=True)
        raise
    score_duration = Fraction(plan.score_sample_count, plan.score_sample_rate)
    available = max(Fraction(0), plan.picture_duration - plan.score_start)
    return {
        "output": str(output), "sha256": _sha256(output), "cut_sha256": plan.cut_sha256,
        "score_sha256": plan.score_sha256, "fps": f"{plan.fps.numerator}/{plan.fps.denominator}",
        "frame_count": plan.frame_count, "picture_duration_seconds": float(plan.picture_duration),
        "score_start_seconds": float(plan.score_start), "score_duration_seconds": float(score_duration),
        "score_trimmed_seconds": float(max(Fraction(0), score_duration - available)),
        "score_padded_seconds": float(max(Fraction(0), available - score_duration)),
        "score_stream_index": plan.score_stream_index,
        "base_audio_stream_indices": list(plan.base_audio_stream_indices),
        "gain_db": plan.gain_db, "sample_rate": plan.sample_rate,
        "target_sample_count": plan.target_sample_count, "picture_identity": identity,
        "technical_checks": ["source hashes", "frame count", "video packet hashes and timing", "audio stream"],
        "listening_review": "not performed by this helper",
    }

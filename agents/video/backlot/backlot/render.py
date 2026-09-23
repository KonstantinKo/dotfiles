"""Render edit/timeline.yaml with a single ffmpeg filter graph."""

from __future__ import annotations

import shlex
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from backlot import ffmpeg
from backlot.errors import BacklotError
from backlot.overlays import parse_srt, render_text_png
from backlot.project import Project
from backlot.ids import is_take_id
from backlot.takes import load_take, resolve_media
from backlot.thumbs import media_kind

PRESETS: dict[str, dict[str, Any]] = {
    "youtube": {"resolution": "1920x1080", "fit": "pad", "crf": 18, "speed": "medium", "abr": "192k"},
    "shorts": {"resolution": "1080x1920", "fit": "crop", "crf": 20, "speed": "medium", "abr": "160k"},
    "draft": {"resolution": "1280x720", "fit": "pad", "crf": 28, "speed": "ultrafast", "abr": "128k"},
}


@dataclass
class Clip:
    path: Path
    still: bool
    duration: float
    start: float = 0.0
    motion: str | None = None
    transition: dict[str, Any] | None = None


@dataclass
class Track:
    name: str
    path: Path
    at: float = 0.0
    gain_db: float = 0.0
    duck_under: str | None = None
    duck_db: float = -10.0
    out: float | None = None
    fade_out_s: float = 0.0


@dataclass
class Plan:
    width: int
    height: int
    fps: int
    fit: str
    clips: list[Clip]
    tracks: list[Track]
    captions: Path | None
    titles: list[dict[str, Any]]
    crf: int
    speed: str
    abr: str
    total: float = 0.0
    overlays: list[tuple[Path, float, float]] = field(default_factory=list)


def _res(text: str) -> tuple[int, int]:
    try:
        w, h = str(text).lower().split("x")
        return int(w), int(h)
    except ValueError as exc:
        raise BacklotError(f"bad resolution {text!r}") from exc


_BLOCKED_STATUSES = ("rejected", "stale")


def _src(project: Project, ref: str, blocked: list[str] | None = None) -> Path:
    ref = str(ref)
    if blocked is not None and is_take_id(ref) and (project.takes_dir / ref / "meta.yaml").exists():
        take = load_take(project, ref)
        if take.status in _BLOCKED_STATUSES:
            blocked.append(f"{ref} ({take.status})")
    return resolve_media(project, ref)


def _check_blocked(blocked: list[str]) -> None:
    if blocked:
        raise BacklotError("timeline uses rejected or stale takes: " + ", ".join(blocked) + "; fix the timeline or pass --allow-stale")


def _caption_src(project: Project, ref: str) -> Path:
    p = Path(ref).expanduser()
    if p.suffix.lower() == ".srt" and p.exists():
        return p
    if (project.root / ref).suffix.lower() == ".srt" and (project.root / ref).exists():
        return project.root / ref
    media = _src(project, ref)
    for cand in (media.with_suffix(".srt"), media.parent / "captions.srt"):
        if cand.exists():
            return cand
    raise BacklotError(f"no .srt found for {ref!r}; run `backlot captions {ref} --model <stt>` first")


def load_timeline(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BacklotError(f"timeline not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not data.get("video"):
        raise BacklotError("timeline has no `video` clips")
    return data


def build_plan(project: Project, timeline: dict[str, Any], preset: str | None, workdir: Path, allow_stale: bool = False) -> Plan:
    settings = dict(PRESETS.get(preset or "", {}))
    width, height = _res(settings.get("resolution") or timeline.get("resolution") or project.resolution)
    fps = int(timeline.get("fps") or project.fps)
    blocked: list[str] | None = None if allow_stale else []
    clips: list[Clip] = []
    for item in timeline["video"]:
        path = _src(project, item["src"], blocked)
        kind = media_kind(path)
        if kind == "image":
            dur = float(item.get("duration") or 3.0)
            clips.append(Clip(path=path, still=True, duration=dur, motion=item.get("motion"), transition=item.get("transition")))
        elif kind == "video":
            start = float(item.get("in") or 0.0)
            end = item.get("out")
            dur = (float(end) if end is not None else ffmpeg.duration(path)) - start
            if dur <= 0:
                raise BacklotError(f"clip {item['src']} has non-positive duration")
            clips.append(Clip(path=path, still=False, duration=dur, start=start, transition=item.get("transition")))
        else:
            raise BacklotError(f"clip {item['src']} is not an image or video")
    tracks = [
        Track(
            name=str(a.get("track") or f"t{i}"), path=_src(project, a["src"], blocked), at=float(a.get("at") or 0.0),
            gain_db=float(a.get("gain_db") or 0.0), duck_under=a.get("duck_under"), duck_db=float(a.get("duck_db") or -10.0),
            out=float(a["out"]) if a.get("out") is not None else None, fade_out_s=float(a.get("fade_out_s") or 0.0),
        )
        for i, a in enumerate(timeline.get("audio") or [])
    ]
    for track in tracks:
        if track.out is not None and track.out <= 0:
            raise BacklotError(f"audio track {track.name}: out must be positive")
        if track.fade_out_s < 0:
            raise BacklotError(f"audio track {track.name}: fade_out_s must not be negative")
    _check_blocked(blocked or [])
    caps = timeline.get("captions") or {}
    captions = _caption_src(project, str(caps["src"])) if caps and caps.get("burn", True) and caps.get("src") else None
    plan = Plan(
        width=width, height=height, fps=fps, fit=settings.get("fit", "pad"), clips=clips, tracks=tracks,
        captions=captions, titles=list(timeline.get("titles") or []), crf=int(settings.get("crf", 20)),
        speed=str(settings.get("speed", "medium")), abr=str(settings.get("abr", "192k")),
    )
    total = 0.0
    for i, clip in enumerate(clips):
        total += clip.duration
        if i > 0 and clips[i - 1].transition and (clips[i - 1].transition or {}).get("type", "xfade") == "xfade":
            total -= float((clips[i - 1].transition or {}).get("duration") or 0.5)
    plan.total = round(total, 3)
    _prepare_overlays(plan, workdir)
    return plan


def _prepare_overlays(plan: Plan, workdir: Path) -> None:
    n = 0
    for title in plan.titles:
        at = float(title.get("at") or 0.0)
        dur = float(title.get("duration") or 2.0)
        png, _, _ = render_text_png(str(title.get("text", "")), plan.width, plan.height, workdir / f"title{n}.png", style=str(title.get("style") or "lower-third"))
        plan.overlays.append((png, at, at + dur))
        n += 1
    if plan.captions:
        cues = parse_srt(plan.captions.read_text(encoding="utf-8"))
        if len(cues) > 300:
            raise BacklotError(f"too many caption cues to burn ({len(cues)}); merge cues first")
        for cue in cues:
            png, _, _ = render_text_png(cue.text, plan.width, plan.height, workdir / f"cue{n}.png", style="caption")
            plan.overlays.append((png, cue.start, cue.end))
            n += 1


def _fit(plan: Plan) -> str:
    w, h = plan.width, plan.height
    if plan.fit == "crop":
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    return f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1"


def build_command(plan: Plan, output: Path) -> list[str]:
    ffm = ffmpeg.which("ffmpeg")
    if not ffm:
        raise BacklotError("ffmpeg not found")
    inputs: list[str] = []
    filters: list[str] = []
    idx = 0
    fit = _fit(plan)
    labels: list[str] = []
    for i, clip in enumerate(plan.clips):
        frames = max(int(round(clip.duration * plan.fps)), 1)
        if clip.still and clip.motion == "kenburns":
            inputs += ["-i", str(clip.path)]
            step = 0.25 / frames
            filters.append(
                f"[{idx}:v]scale={plan.width * 2}:{plan.height * 2}:force_original_aspect_ratio=increase,"
                f"crop={plan.width * 2}:{plan.height * 2},zoompan=z='min(zoom+{step:.6f},1.25)':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d={frames}:s={plan.width}x{plan.height}:fps={plan.fps},"
                f"setsar=1,format=yuv420p,setpts=PTS-STARTPTS[c{i}]"
            )
        elif clip.still:
            inputs += ["-loop", "1", "-framerate", str(plan.fps), "-t", f"{clip.duration:.3f}", "-i", str(clip.path)]
            filters.append(f"[{idx}:v]{fit},fps={plan.fps},format=yuv420p,trim=duration={clip.duration:.3f},setpts=PTS-STARTPTS[c{i}]")
        else:
            inputs += ["-i", str(clip.path)]
            end = clip.start + clip.duration
            filters.append(
                f"[{idx}:v]trim=start={clip.start:.3f}:end={end:.3f},setpts=PTS-STARTPTS,{fit},fps={plan.fps},format=yuv420p[c{i}]"
            )
        labels.append(f"[c{i}]")
        idx += 1
    cur = labels[0]
    cur_dur = plan.clips[0].duration
    for i in range(1, len(plan.clips)):
        trans = plan.clips[i - 1].transition or {}
        out = f"[m{i}]"
        if trans and trans.get("type", "xfade") == "xfade":
            d = float(trans.get("duration") or 0.5)
            name = str(trans.get("name") or "fade")
            filters.append(f"{cur}{labels[i]}xfade=transition={name}:duration={d:.3f}:offset={max(cur_dur - d, 0):.3f}{out}")
            cur_dur += plan.clips[i].duration - d
        else:
            filters.append(f"{cur}{labels[i]}concat=n=2:v=1:a=0{out}")
            cur_dur += plan.clips[i].duration
        cur = out
    for j, (png, start, end) in enumerate(plan.overlays):
        inputs += ["-loop", "1", "-i", str(png)]
        out = f"[o{j}]"
        filters.append(f"{cur}[{idx}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})':format=auto{out}")
        cur = out
        idx += 1
    filters.append(f"{cur}format=yuv420p[vout]")

    audio_labels: list[str] = []
    if plan.tracks:
        by_name: dict[str, int] = {}
        for k, track in enumerate(plan.tracks):
            inputs += ["-i", str(track.path)]
            ms = int(round(track.at * 1000))
            chain = f"[{idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
            if track.out is not None:
                chain += f",atrim=end={track.out:.3f},asetpts=PTS-STARTPTS"
            if track.fade_out_s > 0:
                end = track.out if track.out is not None else ffmpeg.duration(track.path)
                chain += f",afade=t=out:st={max(end - track.fade_out_s, 0):.3f}:d={track.fade_out_s:.3f}"
            filters.append(f"{chain},volume={track.gain_db:+.1f}dB,adelay={ms}|{ms}[a{k}]")
            by_name[track.name] = k
            idx += 1
        duckers: dict[int, list[int]] = {}
        for k, track in enumerate(plan.tracks):
            if track.duck_under:
                src = by_name.get(track.duck_under)
                if src is None:
                    raise BacklotError(f"duck_under {track.duck_under!r} names no track")
                duckers.setdefault(src, []).append(k)
        mix_label = {k: f"[a{k}]" for k in range(len(plan.tracks))}
        for src, ducked in duckers.items():
            outs = [f"[a{src}mix]"] + [f"[a{src}sc{k}]" for k in ducked]
            filters.append(f"[a{src}]asplit={len(outs)}{''.join(outs)}")
            mix_label[src] = f"[a{src}mix]"
            for k in ducked:
                ratio = max(1.5, min(20.0, 10.0 / max(10.0 - abs(plan.tracks[k].duck_db), 0.5)))
                filters.append(
                    f"[a{k}][a{src}sc{k}]sidechaincompress=threshold=0.03:ratio={ratio:.2f}:attack=30:release=400:level_sc=1[a{k}d]"
                )
                mix_label[k] = f"[a{k}d]"
        audio_labels = [mix_label[k] for k in range(len(plan.tracks))]
        if len(audio_labels) == 1:
            filters.append(f"{audio_labels[0]}anull[aout]")
        else:
            filters.append(f"{''.join(audio_labels)}amix=inputs={len(audio_labels)}:duration=longest:normalize=0[aout]")

    cmd = [ffm, "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters), "-map", "[vout]"]
    if plan.tracks:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", plan.abr]
    else:
        cmd += ["-an"]
    cmd += [
        "-t", f"{plan.total:.3f}", "-r", str(plan.fps), "-c:v", "libx264", "-preset", plan.speed, "-crf", str(plan.crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    return cmd


def render(project: Project, timeline_path: Path | None, output: Path | None, preset: str | None, dry_run: bool = False, allow_stale: bool = False) -> tuple[Path, str, float]:
    timeline_path = timeline_path or (project.root / "edit" / "timeline.yaml")
    timeline = load_timeline(timeline_path)
    if preset and preset not in PRESETS:
        raise BacklotError(f"unknown preset {preset!r}; choose from {', '.join(PRESETS)}")
    output = output or project.renders_dir / f"{timeline_path.stem}{('-' + preset) if preset else ''}.mp4"
    if not output.is_absolute():
        output = project.root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="backlot-render-") as tmp:
        plan = build_plan(project, timeline, preset, Path(tmp), allow_stale=allow_stale)
        cmd = build_command(plan, output)
        if dry_run:
            return output, shlex.join(cmd), plan.total
        ffmpeg.run(cmd)
    return output, shlex.join(cmd), plan.total

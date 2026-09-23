"""backlot command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from backlot import __version__
from backlot.errors import EXIT_ERROR, EXIT_OK, BacklotError
from backlot.output import Printer


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    common.add_argument("--project", metavar="SLUG", help="project slug (default: walk up from cwd to project.yaml)")

    p = argparse.ArgumentParser(
        prog="backlot",
        description="Agent-driven video production studio: vault notes + project dir + provider plugins.",
        epilog="Exit codes: 0 ok, 1 error, 2 usage, 3 needs confirmation (re-run with --yes), 4 budget exceeded.",
        parents=[common],
    )
    p.add_argument("--version", action="version", version=f"backlot {__version__}")
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    s = sub.add_parser("init", parents=[common], help="scaffold a project in the vault and the projects root")
    s.add_argument("slug")
    s.add_argument("--format", default="16:9")
    s.add_argument("--fps", type=int, default=24)
    s.add_argument("--res", default="1920x1080")
    s.add_argument("--budget", type=float, default=25.0, help="budget in EUR (must be > 0)")
    s.add_argument("--title")

    s = sub.add_parser("models", parents=[common], help="list models from the vault catalog (untested marked, disabled hidden)")
    s.add_argument("--kind")
    s.add_argument("--provider")
    s.add_argument("--all", action="store_true", help="include disabled models")

    s = sub.add_parser("gen", parents=[common], help="generate image/video/music/sfx/upscale takes")
    s.add_argument("kind", help="image|video|music|sfx|upscale (or img|vid|mus|up)")
    s.add_argument("--model", help="model id (default from project.yaml models.<kind>)")
    s.add_argument("--prompt", default="")
    s.add_argument("--image", help="path or take id used as image input")
    s.add_argument("--audio", help="path or take id used as audio input")
    s.add_argument("--video", help="path or take id used as video input (lipsync, video upscale)")
    s.add_argument("--shot")
    s.add_argument("--n", type=int, default=1)
    s.add_argument("--param", action="append", default=[], metavar="K=V")
    s.add_argument("--parent", metavar="TAKE", help="make a variation of this take (id.<n>)")
    s.add_argument("--depends-on", default="", metavar="NOTES", help="comma-separated Context notes, e.g. Cast/Mia,Locations/Bar")
    s.add_argument("--dry-run", action="store_true", help="only print the estimate")
    s.add_argument("--yes", action="store_true", help="skip the confirmation step")

    s = sub.add_parser("tts", parents=[common], help="generate a voice-over take (kind vo)")
    s.add_argument("--model")
    s.add_argument("--voice", default="")
    s.add_argument("--text", default="")
    s.add_argument("--file", help="read text from file")
    s.add_argument("--shot")
    s.add_argument("--n", type=int, default=1)
    s.add_argument("--param", action="append", default=[], metavar="K=V")
    s.add_argument("--parent", metavar="TAKE")
    s.add_argument("--depends-on", default="", metavar="NOTES")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--yes", action="store_true")

    s = sub.add_parser("takes", parents=[common], help="list takes")
    s.add_argument("--shot")
    s.add_argument("--kind")
    s.add_argument("--status")
    s.add_argument("--stale", action="store_true")

    s = sub.add_parser("show", parents=[common], help="show one take")
    s.add_argument("take")

    s = sub.add_parser("approve", parents=[common], help="approve a take (updates shot note, ledger)")
    s.add_argument("take")
    s.add_argument("--reason", required=True)
    s.add_argument("--lock", metavar="NOTE", help="lock a Context note to this take, e.g. Cast/Mia")

    s = sub.add_parser("reject", parents=[common], help="reject a take")
    s.add_argument("take")
    s.add_argument("--reason", required=True)

    s = sub.add_parser("stale", parents=[common], help="mark takes/shots depending on a Context note as stale")
    s.add_argument("note", help="Context note name, e.g. Cast/Mia or Mia")
    s.add_argument("--reason", required=True)

    s = sub.add_parser("captions", parents=[common], help="speech-to-text -> .srt + words json next to the take")
    s.add_argument("src", help="take id or audio/video file")
    s.add_argument("--model", help="stt model id (default: first active stt model)")

    s = sub.add_parser("render", parents=[common], help="render edit/timeline.yaml with ffmpeg")
    s.add_argument("timeline", nargs="?", help="timeline YAML (default edit/timeline.yaml)")
    s.add_argument("-o", "--output", help="output file (default renders/<timeline>[-preset].mp4)")
    s.add_argument("--preset", choices=["youtube", "shorts", "draft"])
    s.add_argument("--dry-run", action="store_true", help="print the ffmpeg command only")
    s.add_argument("--allow-stale", action="store_true", help="render even when a source take is rejected or stale")

    s = sub.add_parser("reframe", parents=[common], help="crop/scale a take or render to another aspect")
    s.add_argument("src")
    s.add_argument("--to", default="9:16")
    s.add_argument("--focus", default="center", choices=["center", "left", "right", "top", "bottom", "auto"])
    s.add_argument("-o", "--output")

    sub.add_parser("status", parents=[common], help="regenerate Status.md and print it")
    sub.add_parser("cost", parents=[common], help="regenerate Costs.md and print it")
    sub.add_parser("thumbs", parents=[common], help="regenerate all thumbnails")
    sub.add_parser("doctor", parents=[common], help="check tools, keys, vault, ComfyUI, model notes")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return EXIT_OK
    out = Printer(as_json=args.json)
    try:
        return _dispatch(args, out) or EXIT_OK
    except BacklotError as exc:
        if exc.code == EXIT_OK:
            out.line(str(exc), exc.data or None)
            return EXIT_OK
        out.error(str(exc), {"code": exc.code, **exc.data})
        return exc.code
    except KeyboardInterrupt:
        out.error("interrupted")
        return 130


def _studio():
    from backlot.config import load_studio

    return load_studio()


def _project(args):
    from backlot.project import resolve_project

    return resolve_project(_studio(), args.project)


def _dispatch(args: argparse.Namespace, out: Printer) -> int:
    cmd = args.cmd
    if cmd == "doctor":
        return cmd_doctor(out)
    if cmd == "init":
        from backlot.scaffold import init_project

        info = init_project(_studio(), args.slug, fmt=args.format, fps=args.fps, res=args.res, budget=args.budget, title=args.title)
        out.line(f"init {info['slug']}: vault {info['vault_project']} · dir {info['project_dir']} · git {info['git']}", info, "green")
        return EXIT_OK
    if cmd == "models":
        return cmd_models(args, out)
    if cmd in ("gen", "tts"):
        return cmd_gen(args, out)
    if cmd == "takes":
        return cmd_takes(args, out)
    if cmd == "show":
        return cmd_show(args, out)
    if cmd == "approve":
        from backlot.decisions import approve

        info = approve(_project(args), args.take, args.reason, args.lock)
        out.line(f"approved {info['take']}" + (f" (shot {info['shot']})" if info["shot"] else "") + (f" · locked {args.lock}" if args.lock else ""), info, "green")
        return EXIT_OK
    if cmd == "reject":
        from backlot.decisions import reject

        info = reject(_project(args), args.take, args.reason)
        out.line(f"rejected {info['take']}", info, "yellow")
        return EXIT_OK
    if cmd == "stale":
        from backlot.decisions import stale

        info = stale(_project(args), args.note, args.reason)
        out.line(f"stale {info['note']}: takes {', '.join(info['takes']) or '-'} · shots {', '.join(info['shots']) or '-'}", info, "yellow")
        return EXIT_OK
    if cmd == "captions":
        from backlot.captions import run_captions

        info = run_captions(_studio(), _project(args), args.src, args.model)
        out.line(f"captions {info['srt']} ({info['cues']} cues, {info['cost_eur']:.3f} EUR)", info, "green")
        return EXIT_OK
    if cmd == "render":
        from backlot.render import render

        project = _project(args)
        path, command, total = render(project, Path(args.timeline) if args.timeline else None, Path(args.output) if args.output else None, args.preset, args.dry_run, allow_stale=args.allow_stale)
        if args.dry_run:
            out.line(command, {"command": command, "output": str(path), "duration_s": total})
        else:
            out.line(f"rendered {path} ({total:.1f}s)", {"output": str(path), "duration_s": total, "command": command}, "green")
        return EXIT_OK
    if cmd == "reframe":
        from backlot.reframe import reframe

        path = reframe(_project(args), args.src, args.to, args.focus, Path(args.output) if args.output else None)
        out.line(f"reframed -> {path}", {"output": str(path)}, "green")
        return EXIT_OK
    if cmd == "status":
        from backlot.vault import write_status

        text = write_status(_project(args))
        out.line(text.rstrip(), {"status": text})
        return EXIT_OK
    if cmd == "cost":
        from backlot.vault import write_costs

        text = write_costs(_project(args))
        out.line(text.rstrip(), {"costs": text})
        return EXIT_OK
    if cmd == "thumbs":
        return cmd_thumbs(args, out)
    raise BacklotError(f"unknown command {cmd}")


def cmd_doctor(out: Printer) -> int:
    from backlot.doctor import run_checks

    checks = run_checks()
    rows = []
    for c in checks:
        mark = "ok" if c.ok else ("warn" if c.warn else "FAIL")
        rows.append(out.color(f"{mark:4} {c.name}: {c.detail}", "green" if c.ok else "yellow" if c.warn else "red"))
    out.lines(rows, [{"name": c.name, "ok": c.ok, "warn": c.warn, "detail": c.detail} for c in checks])
    return EXIT_OK if all(c.ok or c.warn for c in checks) else EXIT_ERROR


def cmd_models(args: argparse.Namespace, out: Printer) -> int:
    from backlot.models import load_models, normalize_kind

    models, problems = load_models(_studio().vault)
    kind = normalize_kind(args.kind) if args.kind else None
    rows = [
        m for m in models
        if (args.all or m.status != "disabled") and (not kind or m.kind == kind) and (not args.provider or m.provider == args.provider)
    ]
    lines = [
        out.color(f"{m.id:28} {m.kind:8} {m.provider:14} {m.tier:5} {m.cost_eur:>7.3f} {m.cost_unit:13} {m.status}", "" if m.status == "active" else "yellow")
        for m in rows
    ]
    lines += [out.color(f"broken {p.name}: {msg}", "red") for p, msg in problems]
    out.lines(lines or ["no models"], [m.to_dict() for m in rows])
    return EXIT_OK


def cmd_gen(args: argparse.Namespace, out: Printer) -> int:
    from backlot.gen import GenOptions, execute, parse_params

    project = _project(args)
    is_tts = args.cmd == "tts"
    text = ""
    if is_tts:
        text = Path(args.file).expanduser().read_text(encoding="utf-8").strip() if args.file else args.text
    opts = GenOptions(
        kind="tts" if is_tts else args.kind,
        model_id=args.model,
        prompt="" if is_tts else args.prompt,
        text=text,
        voice=getattr(args, "voice", ""),
        image=getattr(args, "image", None),
        audio=getattr(args, "audio", None),
        video=getattr(args, "video", None),
        shot=args.shot,
        n=args.n,
        params=parse_params(args.param),
        parent=args.parent,
        depends_on=[d.strip() for d in args.depends_on.split(",") if d.strip()],
        dry_run=args.dry_run,
        yes=args.yes,
    )
    outcome = execute(_studio(), project, opts)
    rows = [f"created shot {s}" for s in outcome.created_shots]
    rows += [f"{t.take}  {t.model}  {t.cost_eur:.3f} EUR  {t.file}" + (f"  shot {t.shot}" if t.shot else "") for t in outcome.takes]
    out.lines(rows, [t.to_dict() for t in outcome.takes])
    return EXIT_OK


def cmd_takes(args: argparse.Namespace, out: Printer) -> int:
    from backlot.models import KIND_PREFIX, normalize_kind
    from backlot.takes import list_takes

    takes = list_takes(_project(args))
    kind = KIND_PREFIX.get(normalize_kind(args.kind), args.kind) if args.kind else None
    rows = [
        t for t in takes
        if (not args.shot or t.shot == args.shot) and (not kind or t.kind == kind)
        and (not args.status or t.status == args.status) and (not args.stale or t.status == "stale")
    ]
    color = {"approved": "green", "rejected": "dim", "stale": "yellow"}
    lines = [out.color(f"{t.take:12} {t.kind:8} {t.status:9} {t.shot or '-':6} {t.model:24} {t.cost_eur:.3f}", color.get(t.status, "")) for t in rows]
    out.lines(lines or ["no takes"], [t.to_dict() for t in rows])
    return EXIT_OK


def cmd_show(args: argparse.Namespace, out: Printer) -> int:
    from backlot import vault
    from backlot.takes import load_take

    project = _project(args)
    t = load_take(project, args.take)
    data = t.to_dict()
    data["path"] = str(project.root / t.file)
    data["note"] = str(vault.take_note_path(project, t.take))
    lines = [f"{k}: {v}" for k, v in data.items() if v not in (None, "", [], {})]
    out.lines(lines, data)
    return EXIT_OK


def cmd_thumbs(args: argparse.Namespace, out: Printer) -> int:
    from backlot import vault
    from backlot.takes import list_takes
    from backlot.thumbs import make_thumb

    project = _project(args)
    done: list[str] = []
    for t in list_takes(project):
        src = project.root / t.file
        if src.exists() and make_thumb(src, vault.thumbs_dir(project), t.take):
            done.append(t.take)
    out.line(f"thumbs: {len(done)} regenerated", {"takes": done})
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

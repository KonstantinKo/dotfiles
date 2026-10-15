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
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="machine-readable output")
    common.add_argument("--project", metavar="SLUG", default=argparse.SUPPRESS, help="project slug (default: walk up from cwd to project.yaml)")

    p = argparse.ArgumentParser(
        prog="backlot",
        description="Agent-driven video production studio: vault notes + project dir + provider plugins.",
        epilog="Exit codes: 0 ok, 1 error, 2 usage, 3 exact paid-call authorization required, 4 budget exceeded.",
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
    s.add_argument("--image", action="append", default=[], help="path or take id used as image input (repeatable when the model's arg_map target is a list)")
    s.add_argument("--audio", action="append", default=[], help="path or take id used as audio input (repeatable)")
    s.add_argument("--video", action="append", default=[], help="path or take id used as video input (repeatable; lipsync, video upscale)")
    s.add_argument("--end-image", dest="end_image", help="path or take id for models with an end_image input")
    s.add_argument("--shot")
    s.add_argument("--n", type=int, default=1)
    s.add_argument("--param", action="append", default=[], metavar="K=V")
    s.add_argument("--parent", metavar="TAKE", help="make a variation of this take (id.<n>); must be the same kind")
    s.add_argument("--depends-on", default="", metavar="NOTES", help="comma-separated Context notes, e.g. Cast/Mia,Locations/Bar")
    s.add_argument("--dry-run", action="store_true", help="only print the estimate")
    s.add_argument("--yes", action="store_true", help="execute with recorded exact-call authorization")
    s.add_argument("--authorization", action="append", default=[], help="one recorded authorization ID per paid call")
    s.add_argument("--force", action="store_true", help="allow a single call above max_call_eur")

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
    s.add_argument("--authorization", action="append", default=[])
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("batch", parents=[common], help="run gen/tts plan with one recorded authorization per paid call")
    s.add_argument("plan", help="YAML with `requests:` (fields as the gen/tts flags)")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--yes", action="store_true")
    s.add_argument("--authorization", action="append", default=[])
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("recover", parents=[common], help="fetch a failed/pending take's result by its provider request id")
    s.add_argument("take")

    s = sub.add_parser("takes", parents=[common], help="list takes")
    s.add_argument("--shot")
    s.add_argument("--kind")
    s.add_argument("--status", help="new|approved|rejected|stale|pending|failed")
    s.add_argument("--stale", action="store_true")

    s = sub.add_parser("show", parents=[common], help="show one take")
    s.add_argument("take")

    s = sub.add_parser("approve", parents=[common], help="approve a take (updates shot note, ledger)")
    s.add_argument("take")
    s.add_argument("--reason", required=True)
    s.add_argument("--lock", metavar="NOTE", help="lock a Context note to this take, e.g. Cast/Mia")
    s.add_argument("--source-ref", required=True, help="user message reference for typed approval")
    s.add_argument("--source-message", required=True, help="user approval text")
    s.add_argument("--scope", default="provisional production use")

    s = sub.add_parser("reject", parents=[common], help="reject a take")
    s.add_argument("take")
    s.add_argument("--reason", required=True)
    s.add_argument("--source-ref")
    s.add_argument("--source-message")
    s.add_argument("--source-kind", choices=["user", "agent", "legacy"], default="agent",
                   help="reviewer finding by default; use user only for an explicit user rejection")
    s.add_argument("--scope", default="raw take")

    s = sub.add_parser("stale", parents=[common], help="mark takes/shots (and dependent Context notes) depending on a Context note as stale")
    s.add_argument("note", help="Context note name, e.g. Cast/Mia or Mia")
    s.add_argument("--reason", required=True)
    s.add_argument("--dry-run", action="store_true", help="print what would be marked")

    s = sub.add_parser("captions", parents=[common], help="speech-to-text -> .srt + words json next to the take")
    s.add_argument("src", help="take id or audio/video file")
    s.add_argument("--model", help="stt model id (default: first active stt model)")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--yes", action="store_true")
    s.add_argument("--authorization")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("authorize", parents=[common], help="record explicit user approval for one exact paid call")
    s.add_argument("quote_file", help="JSON output from gen/tts/captions --dry-run --json, or one batch quote")
    s.add_argument("--quote-index", type=int, help="1-based call number in a batch quote")
    s.add_argument("--source-message", required=True, help="the user's explicit approval text")
    s.add_argument("--source-ref", required=True, help="transcript/message reference for the approval")
    s.add_argument("--balance", type=float, required=True, help="observed current account balance")
    s.add_argument("--balance-unit", required=True, help="balance unit, e.g. EUR or credits")
    s.add_argument("--balance-source", required=True, help="where and when the balance was observed")
    s.add_argument("--expires", required=True, help="ISO expiry timestamp with timezone")

    s = sub.add_parser("decision", parents=[common], help="record a scoped approval or rejection")
    s.add_argument("action", choices=["approve", "reject", "accept-limit"])
    s.add_argument("subject_type", choices=["take", "reference", "shot", "range", "picture", "scored", "share"])
    s.add_argument("subject_id")
    s.add_argument("--version", required=True, help="immutable artifact version or SHA-256")
    s.add_argument("--scope", required=True, help="exact use/review/share scope")
    s.add_argument("--reason", required=True)
    s.add_argument("--source-ref", required=True)
    s.add_argument("--source-message", required=True)
    s.add_argument("--source-kind", choices=["user", "agent", "legacy"],
                   help="defaults to user for approval/accepted limit and agent for rejection")
    s.add_argument("--source-at", help="original ISO timestamp with timezone, when known")
    s.add_argument("--coverage", action="append", default=[], metavar="START:END", help="approved inclusive output-frame range; omit for full output")

    s = sub.add_parser("handoff", parents=[common], help="show or refresh current project handoff")
    s.add_argument("--refresh", action="store_true")
    s.add_argument("--claim", help="claim a semantic scene for one worker")
    s.add_argument("--worker", help="worker name for --claim")
    s.add_argument("--base-revision", type=int, help="observed handoff revision for --claim")

    s = sub.add_parser("register", parents=[common], help="register existing provider, supplied or local media without a provider call")
    s.add_argument("spec_file", help="JSON spec with origin, kind, media, exact sources/coverage and optional native expense")
    s.add_argument("--dry-run", action="store_true", help="hash/probe/validate without writing")

    s = sub.add_parser("expense", parents=[common], help="record one existing provider operation in its native unit")
    s.add_argument("spec_file", help="JSON expense spec; this command never calls a provider")

    s = sub.add_parser("expense-allocation", parents=[common], help="classify registered sunk expense use without changing its charge")
    s.add_argument("expense_id")
    s.add_argument("allocation", choices=["current_final", "experiment", "unallocated"])
    s.add_argument("--source-ref", required=True)
    s.add_argument("--reason", required=True)

    sub.add_parser("lineage", parents=[common], help="report descendants needing review after source changes")
    sub.add_parser("manifest", parents=[common], help="rebuild current manifest.jsonl from take metadata")
    s = sub.add_parser("migrate", parents=[common], help="idempotently tag legacy take metadata with the current schema")
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("sheet", parents=[common], help="contact sheet of a shot's takes -> renders/sheets/<shot>.jpg + shot note `## Candidates`")
    s.add_argument("--shot", required=True)
    s.add_argument("--kind", help="img|vid (default both)")

    s = sub.add_parser("stage", parents=[common], help="check the gate for the project's current stage")
    s.add_argument("--advance", action="store_true", help="move `status` to the next stage when the gate passes")

    s = sub.add_parser("assembly", parents=[common], help="register an exact native, external or custom assembly manifest")
    s.add_argument("spec_file", help="JSON assembly spec")
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("deliverable", parents=[common], help="register a named, versioned deliverable")
    s.add_argument("spec_file", help="JSON deliverable spec")
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("historical-import", parents=[common], help="import an original, exact user final approval")
    s.add_argument("spec_file", help="JSON historical acceptance spec")
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("delivery", parents=[common], help="inspect declared deliverables and scene gates")
    s.add_argument("--refresh", action="store_true", help="rewrite derived Deliverables.md index")

    sub.add_parser("requirements", parents=[common], help="show the workflow requirement registry")

    for name, help_text in (("review-record", "record version-bound technical and human review"),
                            ("repair-plan", "record a no-spend repair plan"),
                            ("repair-result", "record the observed outcome of a repair"),
                            ("score-plan", "validate an exact cut-bound score plan without mixing"),
                            ("score-mix", "mix a planned score into an exact cut")):
        s = sub.add_parser(name, parents=[common], help=help_text)
        s.add_argument("spec_file", help="JSON specification")

    s = sub.add_parser("archive", parents=[common], help="create, check or bundle an exact media archive")
    archive_sub = s.add_subparsers(dest="archive_cmd", required=True)
    s = archive_sub.add_parser("create", parents=[common])
    s.add_argument("spec_file", help="JSON file list, manifest_path and optional recipe")
    s = archive_sub.add_parser("check", parents=[common])
    s.add_argument("manifest")
    s = archive_sub.add_parser("bundle", parents=[common])
    s.add_argument("manifest")
    s.add_argument("destination")

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

    s = sub.add_parser("status", parents=[common], help="show computed status without writing")
    s.add_argument("--refresh", action="store_true", help="rewrite Status.md and its derived handoff")
    s = sub.add_parser("cost", parents=[common], help="show computed costs without writing")
    s.add_argument("--refresh", action="store_true", help="rewrite Costs.md and spent_eur")
    sub.add_parser("thumbs", parents=[common], help="regenerate all thumbnails")
    sub.add_parser("doctor", parents=[common], help="check tools, keys, vault, ComfyUI, model notes")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return EXIT_OK
    out = Printer(as_json=getattr(args, "json", False))
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

    return resolve_project(_studio(), getattr(args, "project", None))


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
    if cmd == "authorize":
        import json
        from backlot.authority import authorize

        payload = json.loads(Path(args.quote_file).read_text(encoding="utf-8"))
        quotes = payload.get("quotes")
        if quotes:
            if args.quote_index is None and len(quotes) != 1:
                raise BacklotError("batch quote needs --quote-index (1-based paid call number)")
            index = args.quote_index or 1
            if index < 1 or index > len(quotes):
                raise BacklotError("--quote-index is outside the batch quote")
            quoted = quotes[index - 1]
        else:
            quoted = payload.get("quote") or payload
        record = authorize(_project(args), quoted, source_message=args.source_message,
                           source_ref=args.source_ref, balance_amount=args.balance,
                           balance_unit=args.balance_unit, balance_source=args.balance_source,
                           expires_at=args.expires)
        out.line(f"authorized {record['id']} for {record['request']['provider']} {record['request']['route']}", record)
        return EXIT_OK
    if cmd == "decision":
        from backlot.decisions import record_decision

        ranges = []
        for item in args.coverage:
            try:
                start, end = (int(part) for part in item.split(":"))
            except (ValueError, TypeError) as exc:
                raise BacklotError("--coverage needs START:END") from exc
            ranges.append([start, end])
        record = record_decision(_project(args), args.action, args.subject_type, args.subject_id,
                                 version=args.version, scope=args.scope, reason=args.reason,
                                 source_ref=args.source_ref, source_message=args.source_message,
                                 source_kind=args.source_kind or ("agent" if args.action == "reject" else "user"), source_at=args.source_at,
                                 coverage=ranges or None)
        out.line(f"recorded {record['id']} {record['action']} {record['subject_type']}:{record['subject_id']}", record)
        return EXIT_OK
    if cmd == "handoff":
        from backlot.handoff import claim, render

        project = _project(args)
        if args.claim:
            if not args.worker or args.base_revision is None:
                raise BacklotError("--claim needs --worker and --base-revision")
            claim(project, args.claim, args.worker, args.base_revision)
        path = project.vault_project / "Handoff.md"
        result = render(project) if args.refresh or args.claim or not path.exists() else path.read_text(encoding="utf-8")
        out.line(result.rstrip(), {"handoff": result})
        return EXIT_OK
    if cmd == "register":
        import json
        from backlot.register import register

        spec = json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
        result = register(_project(args), spec, dry_run=args.dry_run)
        out.line(f"{'checked' if args.dry_run else 'registered'} {result.get('take') or spec.get('media')}", result)
        return EXIT_OK
    if cmd == "expense":
        import json
        from backlot import expenses, vault

        project = _project(args)
        record = expenses.register(project, json.loads(Path(args.spec_file).read_text(encoding="utf-8")))
        vault.write_costs(project)
        out.line(f"recorded {record['id']}", record)
        return EXIT_OK
    if cmd == "expense-allocation":
        from backlot import expenses, vault

        project = _project(args)
        record = expenses.allocate(project, args.expense_id, args.allocation,
                                   source_ref=args.source_ref, reason=args.reason)
        vault.write_costs(project)
        out.line(f"allocated {record['id']} as {record['allocation']}", record)
        return EXIT_OK
    if cmd == "lineage":
        from backlot.lineage import check

        result = check(_project(args))
        out.line(f"{len(result['needs_review'])} artifacts need source review", result)
        return EXIT_OK
    if cmd == "manifest":
        from backlot.takes import rebuild_manifest

        path = rebuild_manifest(_project(args))
        out.line(f"rebuilt {path}", {"manifest": str(path)})
        return EXIT_OK
    if cmd == "migrate":
        from backlot.takes import migrate_metadata

        result = migrate_metadata(_project(args), dry_run=args.dry_run)
        out.line(f"{'would migrate' if args.dry_run else 'migrated'} {len(result['changed'])} take records", result)
        return EXIT_OK
    if cmd in ("gen", "tts"):
        return cmd_gen(args, out)
    if cmd == "takes":
        return cmd_takes(args, out)
    if cmd == "show":
        return cmd_show(args, out)
    if cmd == "approve":
        from backlot.decisions import approve

        info = approve(_project(args), args.take, args.reason, args.lock, _studio(),
                       source_ref=args.source_ref, source_message=args.source_message, scope=args.scope)
        out.line(f"approved {info['take']}" + (f" (shot {info['shot']})" if info["shot"] else "") + (f" · locked {args.lock}" if args.lock else "")
                 + (" · model promoted to active" if info.get("model_promoted") else ""), info, "green")
        return EXIT_OK
    if cmd == "batch":
        return cmd_batch(args, out)
    if cmd == "recover":
        from backlot.gen import recover
        from backlot.captions import recover_captions
        from backlot.takes import load_take

        project = _project(args)
        take = (recover_captions(_studio(), project, args.take)
                if load_take(project, args.take).kind == "cap" else recover(_studio(), project, args.take))
        out.line(f"recovered {take.take}  {take.model}  {take.cost_eur:.3f} EUR  {take.file}", take.to_dict(), "green")
        return EXIT_OK
    if cmd == "sheet":
        from backlot.sheet import contact_sheet

        info = contact_sheet(_project(args), args.shot, args.kind)
        out.line(f"sheet {info['sheet']} ({len(info['takes'])} takes) · embedded in Shots/{args.shot}.md", info, "green")
        return EXIT_OK
    if cmd == "stage":
        return cmd_stage(args, out)
    if cmd in ("assembly", "deliverable", "historical-import"):
        import json
        from backlot.delivery import import_historical_acceptance, register_assembly, register_deliverable

        project = _project(args)
        spec = json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
        handler = {"assembly": register_assembly, "deliverable": register_deliverable,
                   "historical-import": import_historical_acceptance}[cmd]
        result = handler(project, spec, dry_run=args.dry_run)
        out.line(f"{'checked' if args.dry_run else 'registered'} {cmd} {result['id']}", result)
        return EXIT_OK
    if cmd == "delivery":
        from backlot.delivery import index_markdown
        from backlot.workflow import evaluate

        project = _project(args)
        result = evaluate(project)
        rows = list(result["deliverables"].values())
        if args.refresh:
            (project.vault_project / "Deliverables.md").write_text(index_markdown(rows), encoding="utf-8")
        out.line(f"delivery: {result['readiness']}", result)
        return EXIT_OK if result["passed"] else EXIT_ERROR
    if cmd == "requirements":
        from backlot.workflow import REQUIREMENTS, requirements_markdown

        out.line(requirements_markdown().rstrip(), REQUIREMENTS)
        return EXIT_OK
    if cmd in ("review-record", "repair-plan", "repair-result"):
        import json
        from backlot.reviews import plan_repair, record_repair_result, register_review

        spec = json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
        operation = {"review-record": register_review, "repair-plan": plan_repair,
                     "repair-result": record_repair_result}[cmd]
        record = operation(_project(args), spec)
        out.line(f"{cmd} {record['id']} · {record.get('outcome') or record.get('status') or 'recorded'}", record)
        return EXIT_OK
    if cmd in ("score-plan", "score-mix"):
        import json
        from backlot.finishing import mix_score, plan_score

        project = _project(args)
        spec = json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
        def local(value: str) -> Path:
            path = Path(value).expanduser()
            return path if path.is_absolute() else project.root / path

        plan = plan_score(local(spec["cut"]), local(spec["score"]), spec["cue_plan"],
                          title_end_boundary=spec["title_end_boundary"], gain_db=spec["gain_db"],
                          score_stream=spec.get("score_stream"))
        result = plan.to_dict() if cmd == "score-plan" else mix_score(plan, local(spec["output"]))
        out.line(f"{cmd} {'checked' if cmd == 'score-plan' else 'mixed'}", result)
        return EXIT_OK
    if cmd == "archive":
        import json
        from backlot.archive import bundle_archive, check_archive, create_archive

        project = _project(args)
        def local(value: str) -> Path:
            path = Path(value).expanduser()
            return path if path.is_absolute() else project.root / path

        if args.archive_cmd == "create":
            spec = json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
            files = [{**row, "source": str(local(row["source"]))} for row in spec["files"]]
            result = create_archive(files, local(spec["manifest_path"]), recipe=spec.get("recipe"))
        elif args.archive_cmd == "check":
            result = check_archive(local(args.manifest))
        else:
            result = bundle_archive(local(args.manifest), local(args.destination))
        out.line(f"archive {args.archive_cmd}: {'ok' if result.get('ok', True) else 'incomplete'}", result)
        return EXIT_OK if result.get("ok", True) else EXIT_ERROR
    if cmd == "reject":
        from backlot.decisions import reject

        info = reject(_project(args), args.take, args.reason,
                      source_ref=args.source_ref, source_message=args.source_message,
                      scope=args.scope, source_kind=args.source_kind)
        out.line(f"rejected {info['take']}", info, "yellow")
        return EXIT_OK
    if cmd == "stale":
        from backlot.decisions import stale

        info = stale(_project(args), args.note, args.reason, dry_run=args.dry_run)
        prefix = "dry-run: would mark stale" if args.dry_run else "stale"
        out.line(f"{prefix} {info['note']}: takes {', '.join(info['takes']) or '-'} · shots {', '.join(info['shots']) or '-'} · context {', '.join(info['context']) or '-'}", info, "yellow")
        return EXIT_OK
    if cmd == "captions":
        from backlot.captions import run_captions

        info = run_captions(_studio(), _project(args), args.src, args.model, yes=args.yes,
                            dry_run=args.dry_run, force=args.force, authorization=args.authorization)
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

        text = write_status(_project(args), _studio(), refresh=args.refresh)
        out.line(text.rstrip(), {"status": text})
        return EXIT_OK
    if cmd == "cost":
        from backlot.vault import write_costs

        text = write_costs(_project(args), refresh=args.refresh)
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
    from backlot.models import load_models, normalize_kind, validate_price

    models, problems = load_models(_studio().vault)
    kind = normalize_kind(args.kind) if args.kind else None
    rows = [
        m for m in models
        if (args.all or m.status != "disabled") and (not kind or m.kind == kind) and (not args.provider or m.provider == args.provider)
    ]
    def readiness(m):
        if m.provider in {"higgsfield", "comfyui-cloud"}:
            return "stub: not callable"
        if m.provider not in {"fal", "local", "comfyui-local"}:
            return "unknown provider route"
        try:
            validate_price(m)
        except BacklotError:
            return "price unverified: not callable"
        return "configured route; runtime readiness unverified"

    lines = [
        out.color(f"{m.id:28} {m.kind:8} {m.provider:14} {m.tier:5} {m.cost_eur:>7.3f} {m.cost_unit:13} {m.status} · {readiness(m)} · {m.endpoint}", "" if m.status == "active" else "yellow")
        for m in rows
    ]
    lines += [out.color(f"broken {p.name}: {msg}", "red") for p, msg in problems]
    out.lines(lines or ["no models"], [{**m.to_dict(), "readiness": readiness(m)} for m in rows])
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
        image=getattr(args, "image", None) or None,
        audio=getattr(args, "audio", None) or None,
        video=getattr(args, "video", None) or None,
        end_image=getattr(args, "end_image", None),
        shot=args.shot,
        n=args.n,
        params=parse_params(args.param),
        parent=args.parent,
        depends_on=[d.strip() for d in args.depends_on.split(",") if d.strip()],
        dry_run=args.dry_run,
        yes=args.yes,
        force=args.force,
        authorizations=args.authorization,
    )
    outcome = execute(_studio(), project, opts)
    rows = [f"created shot {s}" for s in outcome.created_shots]
    rows += [f"{t.take}  {t.model}  {t.cost_eur:.3f} EUR  {t.file}" + (f"  shot {t.shot}" if t.shot else "") for t in outcome.takes]
    out.lines(rows, [t.to_dict() for t in outcome.takes])
    return EXIT_OK


def cmd_batch(args: argparse.Namespace, out: Printer) -> int:
    from backlot.batch import run_batch

    info = run_batch(_studio(), _project(args), Path(args.plan), yes=args.yes, dry_run=args.dry_run,
                     force=args.force, authorizations=args.authorization)
    rows = list(info["table"]) + [f"takes: {', '.join(info['takes']) or '-'}"]
    if info["error"]:
        rows.append(f"stopped at request #{info['failed_at']}: {info['error']}")
    out.lines(rows, info)
    return EXIT_ERROR if info["error"] else EXIT_OK


def cmd_stage(args: argparse.Namespace, out: Printer) -> int:
    from backlot.stages import advance, check

    project = _project(args)
    info = advance(project) if args.advance else check(project)
    if info["passed"]:
        text = f"stage {info['stage']}: pass" + (f" -> advanced to {info['next']}" if info.get("advanced") else (f" (next: {info['next']})" if info["next"] else " (final)"))
        out.line(text, info, "green")
        return EXIT_OK
    out.line(f"stage {info['stage']}: FAIL - " + "; ".join(info["missing"]), info, "yellow")
    return EXIT_ERROR


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
    color = {"approved": "green", "rejected": "dim", "stale": "yellow", "pending": "cyan", "failed": "red"}
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

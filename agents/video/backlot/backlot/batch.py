"""`backlot batch <plan.yaml>`: several gen/tts requests, one cost table, one confirmation, sequential runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backlot import takes as takes_mod
from backlot.config import Studio
from backlot.errors import EXIT_BUDGET, EXIT_CONFIRM, BacklotError
from backlot.gen import GenOptions, Planned, execute, parse_params, plan
from backlot.project import Project

_FIELDS = ("kind", "model", "prompt", "text", "file", "voice", "image", "audio", "video", "end_image", "shot", "n", "params", "parent", "depends_on")


def load_plan(path: Path, project: Project) -> list[GenOptions]:
    if not path.exists():
        raise BacklotError(f"plan not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = data.get("requests") if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise BacklotError(f"{path.name}: expected `requests:` (a list of gen/tts requests) or a top-level list")
    out: list[GenOptions] = []
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict) or not row.get("kind"):
            raise BacklotError(f"{path.name}: request {i} needs `kind` (image|video|tts|...)")
        unknown = sorted(set(row) - set(_FIELDS))
        if unknown:
            raise BacklotError(f"{path.name}: request {i} has unknown keys: {', '.join(unknown)}")
        text = str(row.get("text") or "")
        if row.get("file"):
            file = Path(str(row["file"])).expanduser()
            if not file.is_absolute():
                file = project.root / file
            text = file.read_text(encoding="utf-8").strip()
        params = row.get("params") or {}
        if isinstance(params, list):
            params = parse_params([str(p) for p in params])
        deps = row.get("depends_on") or []
        if isinstance(deps, str):
            deps = [d.strip() for d in deps.split(",") if d.strip()]
        out.append(GenOptions(
            kind=str(row["kind"]), model_id=str(row["model"]) if row.get("model") else None,
            prompt=str(row.get("prompt") or ""), text=text, voice=str(row.get("voice") or ""),
            image=row.get("image"), audio=row.get("audio"), video=row.get("video"),
            end_image=str(row["end_image"]) if row.get("end_image") else None,
            shot=str(row["shot"]) if row.get("shot") else None, n=int(row.get("n") or 1),
            params=dict(params), parent=str(row["parent"]) if row.get("parent") else None, depends_on=[str(d) for d in deps],
        ))
    return out


def cost_table(planned: list[tuple[GenOptions, Planned]]) -> list[str]:
    rows = [f"{'#':>2}  {'kind':6} {'model':28} {'n':>2} {'EUR':>8}  detail"]
    for i, (opts, p) in enumerate(planned, 1):
        detail = (opts.prompt or opts.text or "")[:40].replace("\n", " ")
        rows.append(f"{i:>2}  {p.model.kind:6} {p.model.id:28} {opts.n:>2} {p.total:>8.3f}  {opts.shot or '-':5} {detail}")
    rows.append(f"{'':>2}  {'total':6} {'':28} {'':>2} {sum(p.total for _, p in planned):>8.3f}")
    return rows


def run_batch(studio: Studio, project: Project, path: Path, *, yes: bool, dry_run: bool = False, force: bool = False) -> dict[str, Any]:
    """Plan every request first (all validation errors surface before any spend), then guard the
    whole batch once: one table, one `--yes`, one budget check. Runs stop at the first provider error."""
    requests = load_plan(path, project)
    planned = [(o, plan(studio, project, o)) for o in requests]
    table = cost_table(planned)
    total = round(sum(p.total for _, p in planned), 4)
    spent = takes_mod.spent_eur(project)
    budget = project.budget_eur
    info = {"plan": str(path), "requests": len(planned), "estimate_eur": total, "spent_eur": spent, "budget_eur": budget, "table": table}
    text = "\n".join(table)
    if dry_run:
        raise BacklotError(f"{text}\ndry-run batch: ~{total:.3f} EUR (spent {spent:.3f} / {budget:.2f})", code=0, data={"dry_run": True, **info})
    if budget <= 0:
        raise BacklotError("budget_eur is 0 or missing in project.yaml; set a positive budget before generating", code=EXIT_BUDGET, data={"budget_exceeded": True, **info})
    max_call = project.threshold("max_call_eur", studio)
    over = [f"#{i}" for i, (_, p) in enumerate(planned, 1) if p.per_run > max_call]
    if over and not force:
        raise BacklotError(f"{text}\nrequests {', '.join(over)} are above max_call_eur {max_call:.2f} per call; re-run with --force", code=EXIT_BUDGET, data={"max_call_exceeded": True, **info})
    if spent + total > budget:
        raise BacklotError(f"{text}\nbudget exceeded: {spent:.3f} + {total:.3f} > {budget:.2f} EUR", code=EXIT_BUDGET, data={"budget_exceeded": True, **info})
    if project.ask_before_generate and not yes and total > project.threshold("confirm_over_eur", studio):
        raise BacklotError(f"{text}\nconfirm batch: {len(planned)} requests ~{total:.3f} EUR (spent {spent:.3f} / {budget:.2f}); re-run with --yes", code=EXIT_CONFIRM, data={"needs_confirmation": True, **info})
    takes: list[str] = []
    error: str | None = None
    failed_at: int | None = None
    for i, (opts, _) in enumerate(planned, 1):
        opts.yes, opts.force, opts.dry_run = True, force, False
        try:
            outcome = execute(studio, project, opts)
        except BacklotError as exc:
            error, failed_at = str(exc), i
            break
        takes += [t.take for t in outcome.takes]
    return {**info, "takes": takes, "error": error, "failed_at": failed_at}

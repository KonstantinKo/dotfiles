"""Vault writers: take notes, shot/context notes, Decisions.md, Status.md, Costs.md, project home."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from backlot import frontmatter
from backlot.config import Studio
from backlot.errors import BacklotError
from backlot.ids import validate_shot_id, validate_take_id
from backlot.project import Project
from backlot.takes import Take, list_takes, spent_eur

SHOT_STATUSES = ("planned", "boarded", "approved", "generated", "locked", "stale")
_TAKE_SLOT = {"img": "board_take", "vid": "video_take", "vo": "vo_take"}
_APPROVED_SHOT_STATUS = {"img": "approved"}
_SAVED_SHOT_STATUS = {"img": "boarded", "vid": "generated"}
_SAVED_FROM = {"img": ("planned",), "vid": ("planned", "boarded", "approved")}
_TEMPLATE_SHOT_ID = "S010"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def takes_dir(project: Project) -> Path:
    return project.vault_project / "Takes"


def shots_dir(project: Project) -> Path:
    return project.vault_project / "Shots"


def thumbs_dir(project: Project) -> Path:
    return project.vault_project / "_thumbs"


def take_note_path(project: Project, take_id: str) -> Path:
    return takes_dir(project) / f"{validate_take_id(take_id)}.md"


def link(project: Project, rel: str, alias: str | None = None) -> str:
    """Wikilink with a vault-root-relative target: [[Projects/<slug>/<rel>|alias]]."""
    target = f"{project.vault_prefix}/{rel}"
    return f"[[{target}|{alias}]]" if alias else f"[[{target}]]"


def thumb_link(project: Project, thumb: Path) -> str:
    return link(project, f"_thumbs/{thumb.name}")


def context_link(project: Project, dep: str) -> str:
    """`Cast/Mia` -> [[Projects/<slug>/Context/Cast/Mia|Mia]]; unknown notes keep the given path."""
    try:
        path = context_note(project, dep)
        rel = path.relative_to(project.vault_project).with_suffix("")
    except BacklotError:
        clean = dep.strip().strip("[]")
        rel = Path("Context") / (clean[:-3] if clean.lower().endswith(".md") else clean)
    return link(project, str(rel), rel.name)


def write_take_note(project: Project, take: Take, thumb: Path | None) -> Path:
    data = {
        "type": "take",
        "take": take.take,
        "kind": take.kind,
        "model": take.model,
        "provider": take.provider,
        "shot": take.shot,
        "status": take.status,
        "cost_eur": take.cost_eur,
        "parent": take.parent,
        "depends_on": list(take.depends_on),
        "file": take.file,
        "thumb": thumb_link(project, thumb) if thumb is not None else "",
        "prompt": take.prompt,
        "params": take.params,
        "created": take.created,
    }
    if take.voice:
        data["voice"] = take.voice
    if take.request_id:
        data["request_id"] = take.request_id
    if take.error:
        data["error"] = take.error
    body = [f"# {take.take}", ""]
    if thumb is not None:
        body.append("!" + thumb_link(project, thumb))
        body.append("")
    body.append(f"**Model:** {take.model} ({take.provider}) · **Shot:** {take.shot or '-'} · **Cost:** {take.cost_eur:.3f} EUR")
    if take.status == "failed":
        body.append(f"**Failed:** {take.error or 'provider error'} · request `{take.request_id}` · `backlot recover {take.take}`")
    if take.shot:
        body.append(f"Shot: {link(project, f'Shots/{take.shot}', take.shot)}")
    if take.parent:
        body.append(f"Variation of {link(project, f'Takes/{take.parent}', take.parent)}")
    if take.depends_on:
        body.append("Depends on: " + ", ".join(context_link(project, d) for d in take.depends_on))
    body += ["", "## Prompt", "", take.prompt or "_(none)_", "", "## Params", "", "```yaml",
             yaml.safe_dump(take.params or {}, sort_keys=False, allow_unicode=True).rstrip(), "```", ""]
    path = take_note_path(project, take.take)
    frontmatter.write(path, data, "\n".join(body))
    return path


def set_take_note_status(project: Project, take_id: str, status: str, reason: str | None = None) -> None:
    path = take_note_path(project, take_id)
    if not path.exists():
        return
    changes: dict[str, Any] = {"status": status}
    if reason:
        changes["reason"] = reason
    frontmatter.update(path, **changes)


def shot_note_path(project: Project, shot: str) -> Path:
    return shots_dir(project) / f"{validate_shot_id(shot)}.md"


def load_shots(project: Project) -> list[dict[str, Any]]:
    folder = shots_dir(project)
    shots = []
    if not folder.is_dir():
        return shots
    for path in sorted(folder.glob("*.md")):
        if path.name.startswith("_"):
            continue
        try:
            data, _ = frontmatter.read(path)
        except ValueError:
            continue
        if not data.get("shot"):
            data["shot"] = path.stem
        data["_path"] = path
        shots.append(data)
    return shots


def shot_template_path(project: Project) -> Path:
    for candidate in (shots_dir(project) / "_template.md", project.vault_project.parent.parent / "_templates" / "Shots" / "_template.md"):
        if candidate.is_file():
            return candidate
    raise BacklotError(f"no shot template: expected {shots_dir(project) / '_template.md'} or <vault>/_templates/Shots/_template.md")


def ensure_shot_note(project: Project, shot: str) -> bool:
    """Create Shots/<shot>.md from the shot template when missing. Returns True when created."""
    path = shot_note_path(project, shot)
    if path.exists():
        return False
    data, body = frontmatter.read(shot_template_path(project))
    template_id = str(data.get("shot") or _TEMPLATE_SHOT_ID)
    data.update({"type": "shot", "shot": shot, "status": "planned", "created": _today()})
    frontmatter.write(path, data, body.replace(template_id, shot))
    return True


def update_shot(project: Project, shot: str, **changes: Any) -> None:
    ensure_shot_note(project, shot)
    frontmatter.update(shot_note_path(project, shot), **changes)


def _shot_status(project: Project, shot: str) -> str:
    path = shot_note_path(project, shot)
    if not path.exists():
        return "planned"
    data, _ = frontmatter.read(path)
    return str(data.get("status") or "planned")


def record_take_on_shot(project: Project, take: Take) -> None:
    """A saved board take moves a planned shot to `boarded`; a saved video take moves it to `generated`."""
    if not take.shot or take.kind not in _SAVED_SHOT_STATUS:
        return
    current = _shot_status(project, take.shot)
    if current in _SAVED_FROM[take.kind]:
        update_shot(project, take.shot, status=_SAVED_SHOT_STATUS[take.kind])


def record_approval_on_shot(project: Project, take: Take) -> None:
    """Approval fills the take slot; a board approval moves the shot to `approved`."""
    if not take.shot:
        return
    slot = _TAKE_SLOT.get(take.kind)
    if not slot:
        return
    changes: dict[str, Any] = {slot: take.take}
    current = _shot_status(project, take.shot)
    if current != "locked" and take.kind in _APPROVED_SHOT_STATUS:
        changes["status"] = _APPROVED_SHOT_STATUS[take.kind]
    update_shot(project, take.shot, **changes)


def context_note(project: Project, name: str) -> Path:
    """Resolve 'Cast/Mia', 'Mia' or '[[Mia]]' to Context/<Group>/<Name>.md."""
    clean = name.strip().strip("[]")
    if clean.lower().endswith(".md"):
        clean = clean[:-3]
    ctx = project.vault_project / "Context"
    direct = ctx / f"{clean}.md"
    if direct.exists():
        return direct
    base = clean.split("/")[-1]
    matches = [p for p in ctx.rglob("*.md") if p.stem.lower() == base.lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise BacklotError(f"context note {name!r} not found under {ctx}")
    raise BacklotError(f"context note {name!r} is ambiguous: " + ", ".join(str(m.relative_to(ctx)) for m in matches))


def note_matches(dep: str, target: Path, project: Project) -> bool:
    clean = dep.strip().strip("[]")
    if clean.lower().endswith(".md"):
        clean = clean[:-3]
    rel = target.relative_to(project.vault_project / "Context").with_suffix("")
    return clean.lower() in {str(rel).lower(), rel.name.lower(), f"context/{rel}".lower()}


def lock_context(project: Project, name: str, take_id: str) -> Path:
    path = context_note(project, name)
    frontmatter.update(path, locked=True, locked_take=take_id)
    return path


def context_notes(project: Project) -> list[Path]:
    ctx = project.vault_project / "Context"
    return sorted(p for p in ctx.rglob("*.md") if not p.name.startswith("_")) if ctx.is_dir() else []


def context_dependents(project: Project, target: Path) -> list[Path]:
    """Context notes whose frontmatter `depends_on` reaches `target`, transitively (cycle-safe)."""
    notes = context_notes(project)
    deps: dict[Path, list[str]] = {}
    for path in notes:
        try:
            data, _ = frontmatter.read(path)
        except ValueError:
            continue
        deps[path] = [str(d) for d in (data.get("depends_on") or [])]
    marked: list[Path] = []
    seen = {target}
    frontier = [target]
    while frontier:
        current = frontier.pop(0)
        for path, names in deps.items():
            if path in seen or not any(note_matches(n, current, project) for n in names):
                continue
            seen.add(path)
            marked.append(path)
            frontier.append(path)
    return marked


def replace_section(path: Path, heading: str, content: str) -> None:
    """Replace the `## heading` section body (up to the next `## `) or append the section."""
    data, body = frontmatter.read(path) if path.exists() else ({}, "")
    lines = body.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip().lower() == heading.strip().lower()), None)
    block = [heading, "", *content.rstrip("\n").split("\n"), ""]
    if start is None:
        lines = [*lines, *([""] if lines and lines[-1].strip() else []), *block]
    else:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        lines = lines[:start] + block + lines[end:]
    frontmatter.write(path, data, "\n".join(lines).rstrip("\n") + "\n")


def prepend_decision(project: Project, action: str, subject: str, reason: str, extra: str = "") -> Path:
    """Insert a ledger line under `## Ledger` (or after the H1), newest on top."""
    path = project.vault_project / "Decisions.md"
    entry = f"- {_today()} **{action}** {subject}{(' ' + extra) if extra else ''} - {reason}"
    text = path.read_text(encoding="utf-8") if path.exists() else "---\ntype: decisions\n---\n# Decisions\n\n## Ledger\n"
    lines = text.split("\n")
    anchor = next((i for i, l in enumerate(lines) if l.strip().lower() == "## ledger"), None)
    if anchor is None:
        anchor = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
        if anchor is None:
            m = re.match(r"(?s)---\n.*?\n---\n", text)
            anchor = text[: m.end()].count("\n") - 1 if m else -1
    lines.insert(anchor + 1, entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def update_home(project: Project, **changes: Any) -> None:
    path = project.home_note
    if not path.exists():
        frontmatter.write(path, {"status": "idea", **changes}, f"\n# {project.slug}\n")
        return
    frontmatter.update(path, **changes)


def home_data(project: Project) -> dict[str, Any]:
    path = project.home_note
    if not path.exists():
        return {}
    data, _ = frontmatter.read(path)
    return data


def sync_spent(project: Project) -> float:
    spent = spent_eur(project)
    update_home(project, spent_eur=spent)
    return spent


def write_costs(project: Project) -> str:
    takes = list_takes(project)
    total = round(sum(t.cost_eur for t in takes), 4)
    by_model: dict[str, float] = defaultdict(float)
    counts = Counter(t.model for t in takes)
    for t in takes:
        by_model[t.model] += t.cost_eur
    lines = ["# Costs", "", "Regenerated by `backlot cost`. Do not edit by hand.", "",
             "| Take | Kind | Model | Shot | Status | EUR |", "|---|---|---|---|---|---:|"]
    for t in takes:
        lines.append(f"| {t.take} | {t.kind} | {t.model} | {t.shot or ''} | {t.status} | {t.cost_eur:.3f} |")
    lines += ["", f"**Total:** {total:.3f} EUR of {project.budget_eur:.2f} EUR"
              f" ({(total / project.budget_eur * 100) if project.budget_eur else 0:.0f}%)", "", "## By model", "",
              "| Model | Takes | EUR |", "|---|---:|---:|"]
    for model, eur in sorted(by_model.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {model} | {counts[model]} | {eur:.3f} |")
    body = "\n".join(lines) + "\n"
    path = project.vault_project / "Costs.md"
    frontmatter.write(path, {"type": "costs", "generated": _now(), "total_eur": total}, body)
    update_home(project, spent_eur=total)
    return path.read_text(encoding="utf-8")


def write_status(project: Project, studio: Studio | None = None) -> str:
    home = home_data(project)
    shots = load_shots(project)
    takes = list_takes(project)
    spent = round(sum(t.cost_eur for t in takes), 4)
    by_status = Counter(str(s.get("status") or "planned") for s in shots)
    stale_takes = [t.take for t in takes if t.status == "stale"]
    stale_shots = [str(s["shot"]) for s in shots if s.get("status") == "stale"]
    approved = [t for t in takes if t.status == "approved"]
    actions: list[str] = []
    stage = str(home.get("status") or "idea")
    if stage in ("idea", "brief"):
        actions.append("agree the Brief")
    for s in shots:
        sid = s["shot"]
        if s.get("status") == "stale":
            actions.append(f"regenerate {sid} (stale)")
        elif not s.get("board_take"):
            actions.append(f"board {sid}")
        elif not s.get("video_take"):
            actions.append(f"generate video for {sid}")
        elif not s.get("vo_take") and s.get("vo", True) is not False:
            actions.append(f"voice {sid}")
    escalate_pct = project.threshold("escalate_pct", studio)
    pct = (spent / project.budget_eur * 100) if project.budget_eur else 0.0
    escalation = bool(project.budget_eur) and pct >= escalate_pct
    if escalation:
        actions.insert(0, f"ESCALATE: budget at {pct:.0f}% (threshold {escalate_pct:.0f}%), confirm with the user before spending more")
    lines = ["# Status", "", "Regenerated by `backlot status`. Do not edit by hand.", "",
             "## Stage", stage, "",
             f"Format {home.get('format') or project.data.get('format', '')} @ {home.get('fps') or project.fps} fps · "
             f"{home.get('resolution') or project.resolution}", "",
             "## Shots", "| Status | Count |", "|---|---|"]
    lines += [f"| {st} | {n} |" for st, n in sorted(by_status.items())] or ["| (none) | 0 |"]
    if shots:
        lines += ["", "| Shot | Status | Board | Video | VO |", "|---|---|---|---|---|"]
        lines += [f"| {s['shot']} | {s.get('status', '')} | {s.get('board_take') or ''} | {s.get('video_take') or ''} | {s.get('vo_take') or ''} |" for s in shots]
    lines += ["", "## Stale", str(len(stale_takes) + len(stale_shots))]
    if stale_takes or stale_shots:
        lines.append("takes: " + (", ".join(stale_takes) or "-") + " · shots: " + (", ".join(stale_shots) or "-"))
    unfinished = [t.take for t in takes if t.status in ("pending", "failed")]
    lines += ["", "## Takes", f"{len(takes)} takes, {len(approved)} approved" + (f", unfinished: {', '.join(unfinished)}" if unfinished else ""), "",
              "## Spend", f"{spent:.3f} / {project.budget_eur:.2f} EUR ({pct:.0f}%)" + (" · ESCALATION" if escalation else ""), "",
              "## Next actions"]
    lines += [f"- {a}" for a in actions[:12]] or ["- nothing pending"]
    body = "\n".join(lines) + "\n"
    path = project.vault_project / "Status.md"
    frontmatter.write(path, {"type": "status", "generated": _now(), "stage": stage, "spent_eur": spent, "stale": len(stale_takes) + len(stale_shots), "escalation": escalation}, body)
    update_home(project, spent_eur=spent)
    return path.read_text(encoding="utf-8")

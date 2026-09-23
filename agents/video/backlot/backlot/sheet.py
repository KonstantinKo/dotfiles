"""`backlot sheet --shot S010`: a labelled contact sheet of a shot's takes, embedded in the shot note."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from backlot import takes as takes_mod
from backlot import vault
from backlot.errors import BacklotError
from backlot.ids import validate_shot_id
from backlot.models import KIND_PREFIX, normalize_kind
from backlot.overlays import font
from backlot.project import Project
from backlot.thumbs import SIZE, make_thumb

MAX_WIDTH = 1600
CELL = SIZE
LABEL_H = 28
GAP = 12
COLS = 4
EMBED_WIDTH = 512
SECTION = "## Candidates"
_VISUAL = ("img", "vid")


def _thumb_for(project: Project, take: takes_mod.Take) -> Path | None:
    thumbs = vault.thumbs_dir(project)
    existing = thumbs / f"{take.take}.jpg"
    if existing.exists():
        return existing
    src = project.root / take.file
    if not take.file or not src.exists():
        return None
    try:
        return make_thumb(src, thumbs, take.take)
    except (BacklotError, OSError):
        return None


def contact_sheet(project: Project, shot: str, kind: str | None = None) -> dict[str, Any]:
    validate_shot_id(shot)
    prefix = KIND_PREFIX.get(normalize_kind(kind), kind) if kind else None
    takes = [
        t for t in takes_mod.list_takes(project)
        if t.shot == shot and t.status not in takes_mod.UNFINISHED and (t.kind == prefix if prefix else t.kind in _VISUAL)
    ]
    cells = [(t, thumb) for t in takes if (thumb := _thumb_for(project, t)) is not None]
    if not cells:
        raise BacklotError(f"no {kind or 'image/video'} takes with thumbnails for shot {shot}")
    cols = min(COLS, len(cells))
    rows = (len(cells) + cols - 1) // cols
    width = min(MAX_WIDTH, cols * CELL + (cols + 1) * GAP)
    height = rows * (CELL + LABEL_H) + (rows + 1) * GAP
    sheet = Image.new("RGB", (width, height), (30, 37, 48))
    draw = ImageDraw.Draw(sheet)
    fnt = font(16)
    for i, (take, thumb) in enumerate(cells):
        col, row = i % cols, i // cols
        x0 = GAP + col * (CELL + GAP)
        y0 = GAP + row * (CELL + LABEL_H + GAP)
        with Image.open(thumb) as im:
            im = im.convert("RGB")
            im.thumbnail((CELL, CELL))
            sheet.paste(im, (x0 + (CELL - im.width) // 2, y0 + (CELL - im.height) // 2))
        label = take.take + ({"approved": " ✓", "rejected": " ✗", "stale": " ~"}.get(take.status, ""))
        draw.text((x0 + 4, y0 + CELL + 6), label, font=fnt, fill=(235, 238, 242))
    out = project.renders_dir / "sheets" / f"{shot}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "JPEG", quality=88)
    embed = vault.thumbs_dir(project) / f"sheet-{shot}.jpg"
    embed.parent.mkdir(parents=True, exist_ok=True)
    small = sheet.copy()
    small.thumbnail((EMBED_WIDTH, EMBED_WIDTH * 4))
    small.save(embed, "JPEG", quality=82)
    vault.ensure_shot_note(project, shot)
    body = "!" + vault.thumb_link(project, embed) + "\n\n" + " · ".join(f"{vault.link(project, f'Takes/{t.take}', t.take)} ({t.status})" for t, _ in cells)
    vault.replace_section(vault.shot_note_path(project, shot), SECTION, body)
    return {"shot": shot, "sheet": str(out), "embed": str(embed), "takes": [t.take for t, _ in cells], "size": [width, height]}

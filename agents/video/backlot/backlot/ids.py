"""Identifier validation shared by every command that turns an id into a path."""

from __future__ import annotations

import re

from backlot.errors import BacklotError

TAKE_PREFIXES = ("img", "vid", "vo", "mus", "sfx", "up", "cap")
TAKE_ID_RE = re.compile(r"^(?P<prefix>img|vid|vo|mus|sfx|up|cap)-(?P<seq>\d{3})(?:\.(?P<var>\d+))?$")
SHOT_ID_RE = re.compile(r"^S\d{3}$")


def is_take_id(value: str) -> bool:
    return bool(TAKE_ID_RE.match(value or ""))


def is_shot_id(value: str) -> bool:
    return bool(SHOT_ID_RE.match(value or ""))


def validate_take_id(value: str) -> str:
    if not is_take_id(value):
        raise BacklotError(f"invalid take id {value!r} (expected e.g. img-014 or img-014.2)")
    return value


def validate_shot_id(value: str) -> str:
    if not is_shot_id(value):
        raise BacklotError(f"invalid shot id {value!r} (expected e.g. S010)")
    return value

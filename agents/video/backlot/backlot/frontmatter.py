"""Minimal YAML frontmatter reader/writer for Obsidian notes."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

_DELIM = "---"


class Loader(yaml.SafeLoader):
    """SafeLoader without YAML 1.1 sexagesimal ints, so `16:9` stays a string."""


Loader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:int"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
Loader.add_implicit_resolver(
    "tag:yaml.org,2002:int",
    re.compile(r"""^(?:[-+]?0b[0-1_]+|[-+]?0[0-7_]+|[-+]?(?:0|[1-9][0-9_]*)|[-+]?0x[0-9a-fA-F_]+)$"""),
    list("-+0123456789"),
)


def load_yaml(text: str) -> Any:
    return yaml.load(text, Loader=Loader)


def split(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter dict, body). Missing or malformed frontmatter -> ({}, text)."""
    if not text.startswith(_DELIM):
        return {}, text
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i].strip() == _DELIM:
            raw = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            try:
                data = load_yaml(raw) or {}
            except yaml.YAMLError as exc:
                raise ValueError(f"bad frontmatter: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError("frontmatter is not a mapping")
            return data, body
    return {}, text


def join(data: dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False).rstrip("\n")
    return f"{_DELIM}\n{fm}\n{_DELIM}\n{body}"


def read(path: Path) -> tuple[dict[str, Any], str]:
    return split(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(join(data, body), encoding="utf-8")


def update(path: Path, **changes: Any) -> dict[str, Any]:
    """Merge keys into an existing note's frontmatter, keeping the body untouched."""
    data, body = read(path) if path.exists() else ({}, "\n")
    data.update(changes)
    write(path, data, body)
    return data

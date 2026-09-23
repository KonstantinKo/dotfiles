"""Terse one-line output, colored only on a TTY, or JSON."""

from __future__ import annotations

import json
import sys
from typing import Any

_COLORS = {"green": "32", "red": "31", "yellow": "33", "cyan": "36", "dim": "2"}


class Printer:
    def __init__(self, as_json: bool = False):
        self.as_json = as_json
        self.tty = sys.stdout.isatty()

    def color(self, text: str, name: str) -> str:
        if not self.tty or name not in _COLORS:
            return text
        return f"\033[{_COLORS[name]}m{text}\033[0m"

    def line(self, text: str, data: Any = None, color: str | None = None) -> None:
        if self.as_json:
            payload = data if data is not None else {"message": text}
            print(json.dumps(payload, ensure_ascii=False, default=str))
        else:
            print(self.color(text, color) if color else text)

    def lines(self, rows: list[str], data: Any = None) -> None:
        if self.as_json:
            print(json.dumps(data if data is not None else rows, ensure_ascii=False, default=str))
        else:
            for row in rows:
                print(row)

    def error(self, text: str, data: Any = None) -> None:
        if self.as_json:
            payload = {"error": text}
            if data:
                payload.update(data)
            print(json.dumps(payload, ensure_ascii=False, default=str))
        else:
            print(self.color(f"error: {text}", "red"), file=sys.stderr)

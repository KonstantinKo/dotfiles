"""Exit codes and the error type the CLI turns into one-line failures."""

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_CONFIRM = 3
EXIT_BUDGET = 4


class BacklotError(Exception):
    def __init__(self, message: str, code: int = EXIT_ERROR, data: dict | None = None):
        super().__init__(message)
        self.code = code
        self.data = data or {}

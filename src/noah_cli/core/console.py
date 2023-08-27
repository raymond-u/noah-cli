from enum import Enum
from typing import Any, Callable, TypeVar

from rich import console
from rich.prompt import Confirm, Prompt
from rich.status import Status

TEnum = TypeVar("TEnum", bound=Enum)


class LogLevels(int, Enum):
    """Log levels."""
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4


class Console:
    """A managed console for text output."""
    def __init__(self):
        self.is_empty = True
        self.need_newline = False
        self.log_level = LogLevels.WARNING
        self.stdout = console.Console()
        self.stderr = console.Console(stderr=True)

    def set_log_level(self, verbosity: int):
        if verbosity == 1:
            self.log_level = LogLevels.INFO
        elif verbosity == 2:
            self.log_level = LogLevels.DEBUG
        elif verbosity >= 3:
            self.log_level = LogLevels.TRACE

    def ensure_newline(self):
        if self.need_newline:
            self.need_newline = False
            print()

        self.is_empty = False

    def request_for_newline(self):
        if not self.is_empty:
            self.need_newline = True

    def print(self, *args: Any, **kwargs: Any):
        kwargs["highlight"] = kwargs.get("highlight", False)

        self.ensure_newline()
        self.stdout.print(*args, **kwargs)

    def print_trace(self, *args: Any, **kwargs: Any):
        if self.log_level.value > LogLevels.TRACE.value:
            return

        kwargs["highlight"] = kwargs.get("highlight", False)
        self.stdout.print("[TRACE]", *args, **kwargs)

    def print_debug(self, *args: Any, **kwargs: Any):
        if self.log_level.value > LogLevels.DEBUG.value:
            return

        kwargs["highlight"] = kwargs.get("highlight", False)
        self.stderr.print("[DEBUG]", *args, **kwargs)

    def print_info(self, *args: Any, **kwargs: Any):
        if self.log_level.value > LogLevels.INFO.value:
            return

        kwargs["highlight"] = kwargs.get("highlight", False)
        self.stderr.print("[INFO]", *args, **kwargs)

    def print_warning(self, *args: Any, **kwargs: Any):
        if self.log_level.value > LogLevels.WARNING.value:
            return

        kwargs["highlight"] = kwargs.get("highlight", False)
        self.stderr.print("[bold yellow][WARNING][/bold yellow]", *args, **kwargs)

    def print_error(self, *args: Any, **kwargs: Any):
        if self.log_level.value > LogLevels.ERROR.value:
            return

        kwargs["highlight"] = kwargs.get("highlight", False)
        self.stderr.print("[bold red][ERROR][/bold red]", *args, **kwargs)

    def ask_for_enum(self, prompt: str, enum: type[TEnum], default: TEnum | None = None,
                     *args: Any, **kwargs: Any) -> TEnum:
        self.ensure_newline()

        kwargs["prompt"] = f"[bold]{prompt}[/]"
        kwargs["choices"] = [e.value for e in enum]
        kwargs["default"] = default.value if default else None

        while not (answer := Prompt.ask(*args, **kwargs)):
            ...

        return enum(answer)

    def ask_for_list(self, prompt: str, default: list[str] | None = None, *args: Any, **kwargs: Any) -> list[str]:
        self.ensure_newline()

        kwargs["prompt"] = f"[bold]{prompt}[/] (leave blank to finish)"
        kwargs["default"] = default or None

        if not (answer := Prompt.ask(*args, **kwargs)):
            return []

        answers = [answer]

        while answer := input():
            answers.append(answer)

        return answers

    def ask_for_string(self, prompt: str, default: str | None = None, guard: Callable[[str], bool] = lambda x: bool(x),
                       *args: Any, **kwargs: Any) -> str:
        self.ensure_newline()

        kwargs["prompt"] = f"[bold]{prompt}[/]"
        kwargs["default"] = default or None
        kwargs["show_default"] = bool(default)

        while not guard(answer := Prompt.ask(*args, **kwargs)):
            ...

        return answer

    def confirm(self, prompt: str, default: bool = True, *args: Any, **kwargs: Any) -> bool:
        self.ensure_newline()

        kwargs["prompt"] = f"[bold]{prompt}[/] " + ("[Y/n]" if default else "[y/N]")
        kwargs["default"] = default
        kwargs["show_default"] = False
        kwargs["show_choices"] = False

        return Confirm.ask(*args, **kwargs)

    def status(self, *args: Any, **kwargs: Any) -> Status:
        return self.stdout.status(*args, **kwargs)

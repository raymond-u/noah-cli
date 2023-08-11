from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Sequence, TypeVar

from typer import Exit

from .common import format_command, format_input, format_path, sanitize_string
from ..app.state import console, network_client
from ..models.app import AppPaths, EAddMode
from ..models.data import Entry

TEnum = TypeVar("TEnum", bound=Enum)


def get_app_paths(base_path: str | PathLike[str] | None = None) -> AppPaths:
    """Get the paths used by the app."""
    if not base_path:
        base_path = Path().resolve()

        while True:
            if base_path.joinpath("noah.yaml").is_file():
                break

            if base_path == Path("/"):
                console().print_error(f"Could not find {format_path('noah.yaml')} in the current directory or "
                                      f"any of its parents. Please run {format_command('noah init')} to create one.")
                raise Exit(code=1)

            base_path = base_path.parent

    config_file = Path(base_path) / "noah.yaml"
    analysis_dir = Path(base_path) / "analysis"
    results_dir = Path(base_path) / "results"
    containers_dir = Path(base_path) / "containers"
    data_dir = Path(base_path) / "data"
    workflows_dir = Path(base_path) / "workflows"

    return AppPaths(config_file=config_file, analysis_dir=analysis_dir, results_dir=results_dir,
                    containers_dir=containers_dir, data_dir=data_dir, workflows_dir=workflows_dir)


def digest_common_options(verbosity: int, add_mode: EAddMode | None = None, aspera_key: Path | None = None):
    """Digest common options for commands."""
    console().set_log_level(verbosity)

    if add_mode:
        network_client().set_add_mode(add_mode)
    if aspera_key:
        network_client().set_aspera_key(aspera_key)


def sanitize_input(string: str) -> str:
    """Sanitize user input."""
    if (sanitized := sanitize_string(string)) != string:
        console().print_warning(f"{format_input(string)} has been sanitized to {format_input(sanitized)}.")

    return sanitized


def split_modifiers(string: str | None, modifier_name: str) -> dict[str, str]:
    """Split a string of info modifiers into a dict."""
    if not string:
        return {}

    modifiers = {}

    for modifier in string.split(","):
        modifier = modifier.strip()

        if not modifier:
            continue

        if ":" in modifier:
            key, value = modifier.rsplit(":", 1)
            value = value.strip()

            if not value:
                console().print_error("The value of modifier cannot be empty.")
                raise Exit(code=1)

            modifiers[key] = sanitize_input(value)
        else:
            modifiers[""] = sanitize_input(modifier)

    print_modifiers(modifiers, modifier_name)
    return modifiers


def split_modifiers_into_enum(string: str | None, enum: type[TEnum], modifier_name: str) -> dict[str, TEnum]:
    """Split a string of info modifiers into a dict of enum values."""
    if not string:
        return {}

    modifiers = {}

    for modifier in string.split(","):
        modifier = modifier.strip()

        if not modifier:
            continue

        if ":" in modifier:
            key, value = modifier.rsplit(":", 1)
            value = value.strip()

            if not value:
                console().print_error("The value of modifier cannot be empty.")
                raise Exit(code=1)

            if value in (e.value for e in enum):
                modifiers[key] = enum(value)
            else:
                console().print_error(f"{format_input(value)} is not a valid value.")
                raise Exit(code=1)
        else:
            if modifier in (e.value for e in enum):
                modifiers[""] = enum(modifier)
            else:
                console().print_error(f"{format_input(modifier)} is not a valid value.")
                raise Exit(code=1)

    print_modifiers(modifiers, modifier_name)
    return modifiers


def print_modifiers(modifiers: dict[str, str | Enum], modifier_name: str):
    if modifiers:
        console().print_info(f"Found modifiers for {modifier_name}.")

        for key, value in modifiers.items():
            if key == "":
                console().print_info(f"{format_input('*')}: {format_input(value)}")
            else:
                console().print_info(f"{format_input(key)}: {format_input(value)}")


def print_entries(entries: Sequence[Entry], msg: str):
    """Print a list of entries."""
    console().request_for_newline()

    if len(entries) == 0:
        console().print("Nothing to change.")
    else:
        console().print(f"{len(entries)} entries {msg}:")

        for index, entry in enumerate(entries):
            console().print(f"Project name:    {format_input(entry.project)}")
            console().print(f"Experiment name: {format_input(entry.experiment)}")
            console().print(f"Library type:    {format_input(entry.type)}")
            console().print(f"Pipeline phase:  {format_input(entry.phase)}")
            console().request_for_newline()


def print_skipped(skipped: Sequence[str]):
    """Print a list of skipped items."""
    if len(skipped) != 0:
        console().request_for_newline()
        console().print(f"{len(skipped)} items were omitted:")

        for string in skipped:
            console().print(format_input(string))

        console().request_for_newline()


def confirm_or_quit(changed: bool, no_confirm: bool):
    """Confirm changes before applying."""
    if changed:
        if not no_confirm and not console().confirm("Continue?"):
            raise Exit()
    else:
        raise Exit()

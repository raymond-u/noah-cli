import re
import subprocess
from dataclasses import fields, is_dataclass
from enum import Enum
from glob import glob
from hashlib import file_digest
from importlib import metadata
from os import PathLike
from pathlib import Path
from shutil import which
from typing import Any, Iterator
from urllib.parse import urlparse

from ..models.config import Data
from ..models.data import Entry, ESource, File


def get_app_version() -> str:
    """Get the version of the app."""
    return metadata.version("noah_cli")


def run_shell_command(command: list[str]):
    """Run a shell command."""
    subprocess.run(command, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def program_exists(program: str) -> bool:
    """Check if a program exists in the user's PATH."""
    return which(program) is not None


def format_command(value: str) -> str:
    """Format a shell command for console output."""
    return f"[green]{value}[/green]"


def format_option(value: str) -> str:
    """Format an option for console output."""
    return f"[cyan]{value}[/cyan]"


def format_section(value: str) -> str:
    """Format a command section for console output."""
    return f"[turquoise2]{value}[/turquoise2]"


def format_path(value: str | PathLike[str]) -> str:
    """Format a path for console output."""
    return f"[magenta]{value}[/magenta]"


def format_input(value: str | Enum) -> str:
    """Format user input for console output."""
    if isinstance(value, Enum):
        return f"[cyan]{value.value}[/cyan]"
    else:
        return f"[cyan]{value}[/cyan]"


def nullify_dataclass_fields(obj: Any):
    """Nullify all empty fields in a dataclass."""
    if not is_dataclass(obj):
        return

    for field in fields(obj):
        if not getattr(obj, field.name):
            setattr(obj, field.name, None)


def sanitize_string(string: str) -> str:
    """Sanitize a string for use in a file name."""
    # Convert camelCase to snake_case
    indexes = []
    length = len(string)

    for i in range(length):
        if string[i].islower():
            if i + 1 < length and string[i + 1].isupper():
                indexes.append(i + 1)
        elif string[i].isupper():
            if i + 2 < length and string[i + 1].isupper() and string[i + 2].islower():
                indexes.append(i + 1)

    string = "_".join([string[i:j] for i, j in zip([0] + indexes, indexes + [length])]).lower()

    # Replace invalid characters with underscores and remove consecutive underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", string)
    return re.sub(r"_{2,}", "_", sanitized.strip("_"))


def parse_ssh_path(path: str | PathLike[str]) -> tuple[str, str]:
    """Parse an SSH path into a tuple of host and path."""
    if ":" not in path:
        raise ValueError("invalid SSH path")

    host, remote_path = path.rsplit(":", 1)

    if not host or not remote_path:
        raise ValueError(f"{path} is not a valid SSH path")

    return host, remote_path


def get_file_hash(path: str | PathLike[str]) -> str:
    """Get the MD5 hash of a file."""
    with open(path, "rb") as f:
        return file_digest(f, "md5").hexdigest()


def get_file_directory(base_path: str | PathLike[str], entry: Entry) -> Path:
    """Get the parent directory of a file."""
    return Path(base_path) / entry.name


def get_file_name(file: File) -> str:
    """Get the name of a file."""
    match (source := file.sources[0]).type:
        case ESource.ASPERA | ESource.LOCAL | ESource.SSH:
            return Path(source.value).name
        case _:
            return Path(urlparse(source.value).path).name


def is_empty_dir(path: str | PathLike[str]) -> bool:
    """Check if a directory is empty or only contains dotfiles."""
    return not glob(str(Path(path) / "*"))


def combine_name(prefix: str, name: str) -> str:
    """Combine a prefix and a name."""
    if not name:
        return prefix.lower()

    name = sanitize_string(name)

    if len(name) > 40:
        index = name.rfind("_", 0, 40)

        if index != -1:
            name = name[:index]

    if not name.startswith(prefix.lower()):
        name = f"{prefix.lower()}_{name}"

    return name


def iter_data(data: Data) -> Iterator[Entry]:
    """Iterate over all entries in a Data object."""
    for project in data:
        for experiment in project.experiments:
            for type_ in experiment.types:
                for phase in type_.phases:
                    yield Entry(project=project.project, experiment=experiment.experiment, type=type_.enum,
                                phase=phase.enum, identifier=phase.identifier, files=phase.files)

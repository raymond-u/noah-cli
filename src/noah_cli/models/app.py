from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .data import Entry


class EAddMode(str, Enum):
    """The mode to use when adding local files."""
    COPY = "copy"
    LINK = "link"
    MOVE = "move"


@dataclass
class AppPaths:
    """The collection of files and directories used by the app."""
    config_file: Path

    analysis_dir: Path
    results_dir: Path

    containers_dir: Path
    data_dir: Path
    workflows_dir: Path


@dataclass
class QueryResult:
    """Result of a query to the public database."""
    entries: list[Entry]
    mappings: dict[str, list[str]]

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse


class EType(str, Enum):
    """The type of the sequencing library."""
    CHIP = "chip"
    CHIP_INPUT = "chip-input"
    RNA = "rna"


class EPhase(str, Enum):
    """The phase of the pipeline that the file should be used in."""
    RAW = "raw"


class ESource(str, Enum):
    """The type of source for the file."""
    ASPERA = "aspera"
    FTP = "ftp"
    HTTP = "http"
    LOCAL = "local"
    SSH = "ssh"


@dataclass
class Source:
    """Represent a file source."""
    type: str
    value: str

    @property
    def enum(self) -> ESource:
        return ESource(self.type)


@dataclass
class File:
    """Represent a file."""
    checksum: str | None = None
    sources: list[Source] = field(default_factory=list)


@dataclass
class Phase:
    """Represent files for a pipeline phase."""
    phase: str
    identifier: str | None = None
    files: list[File] = field(default_factory=list)

    @property
    def enum(self) -> EPhase:
        return EPhase(self.phase)


@dataclass
class Type:
    """Represent files for a library type."""
    type: str
    phases: list[Phase]

    def __getitem__(self, item: object) -> Phase | None:
        if not isinstance(item, str):
            raise TypeError(f"expected str, got {type(item).__name__}")

        for phase in self.phases:
            if phase.phase == item:
                return phase

        return None

    @property
    def enum(self) -> EType:
        return EType(self.type)


@dataclass
class Experiment:
    """Represent files for an experiment."""
    experiment: str
    types: list[Type]

    def __getitem__(self, item: object) -> Type | None:
        if not isinstance(item, str):
            raise TypeError(f"expected str, got {type(item).__name__}")

        for type_ in self.types:
            if type_.type == item:
                return type_

        return None


@dataclass
class Project:
    """Represent files for a project."""
    project: str
    experiments: list[Experiment]

    def __getitem__(self, item: object) -> Experiment | None:
        if not isinstance(item, str):
            raise TypeError(f"expected str, got {type(item).__name__}")

        for experiment in self.experiments:
            if experiment.experiment == item:
                return experiment

        return None


@dataclass
class Entry:
    """Represent a single entry in the data."""
    project: str | None = None
    experiment: str | None = None
    type: EType | None = None
    phase: EPhase | None = None
    identifier: str | None = None
    files: list[File] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entry):
            return NotImplemented

        return (self.project == other.project and self.experiment == other.experiment
                and self.type == other.type and self.phase == other.phase)

    def __hash__(self) -> int:
        return hash((self.project, self.experiment, self.type, self.phase))

    @property
    def name(self) -> str:
        if self.project and self.experiment and self.type and self.phase:
            return str(Path(self.project).joinpath(f"{self.experiment}@{self.type.value}", str(self.phase.value)))
        elif self.identifier:
            return self.identifier
        else:
            return ", ".join((Path(urlparse(file.sources[0].value).path).name for file in self.files))

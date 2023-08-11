from dataclasses import dataclass, field

from .container import Container
from .data import Project
from .workflow import Workflow


class Containers(list[Container]):
    """Represent containers in the project."""
    ...


class Data(list[Project]):
    """Represent data in the project."""
    def __getitem__(self, item: object) -> Project | None:
        if isinstance(item, int):
            return super().__getitem__(item)
        if isinstance(item, str):
            for project in self:
                if project.project == item:
                    return project

            return None
        else:
            raise TypeError(f"expected int or str, got {type(item).__name__}")


class Workflows(list[Workflow]):
    """Represent workflows in the project."""
    ...


@dataclass
class Info:
    """Represent information about the project."""
    author: str | None = None
    description: str | None = None
    version: str | None = None


@dataclass
class Config:
    """Represent the configuration file."""
    @dataclass
    class Internal:
        containers: list[Container] | None = None
        data: list[Project] | None = None
        workflows: list[Workflow] | None = None
        info: Info | None = None

    containers: Containers = field(default_factory=Containers)
    data: Data = field(default_factory=Data)
    workflows: Workflows = field(default_factory=Workflows)
    info: Info = field(default_factory=Info)

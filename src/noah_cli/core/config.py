from dataclasses import asdict
from typing import Iterable

from dacite import from_dict
from ordered_set import OrderedSet
from ruamel.yaml import YAML
from typer import Exit

from .console import Console
from ..helpers.common import format_command, format_path, get_app_version, iter_data, nullify_dataclass_fields
from ..models.app import AppPaths
from ..models.config import Config, Containers, Data, Info, Workflows
from ..models.data import Entry, Experiment, Phase, Project, Type


class ConfigManager:
    """Manage the configuration file."""
    def __init__(self, console: Console):
        self.console = console
        self.yaml = YAML()

    def create(self, app_paths: AppPaths) -> Config:
        config = Config()
        self.save(config, app_paths)

        return config

    def load(self, app_paths: AppPaths) -> Config:
        if not app_paths.config_file.is_file():
            self.console.print_error(f"No project file found. Please run {format_command('noah init')} to create one.")
            raise Exit(code=1)

        self.console.print_debug(f"Reading {format_path(app_paths.config_file)}...")

        try:
            data = self.yaml.load(app_paths.config_file)
            config_internal = from_dict(Config.Internal, data)
        except Exception as e:
            self.console.print_error(f"Failed to read {format_path(app_paths.config_file)} ({e}).")
            raise Exit(code=1)

        return Config(containers=Containers(config_internal.containers or []), data=Data(config_internal.data or []),
                      workflows=Workflows(config_internal.workflows or []), info=config_internal.info or Info())

    def save(self, config: Config, app_paths: AppPaths):
        # Update the version number
        config.info.version = get_app_version()

        config_internal = Config.Internal(containers=list(config.containers), data=list(config.data),
                                          workflows=list(config.workflows), info=config.info)
        nullify_dataclass_fields(config_internal)

        self.console.print_debug(f"Writing {format_path(app_paths.config_file)}...")

        try:
            data = asdict(config_internal)
            self.yaml.dump(data, app_paths.config_file)
        except Exception as e:
            self.console.print_error(f"Failed to write {format_path(app_paths.config_file)} ({e}).")
            raise Exit(code=1)

    def add_data(self, config: Config, entries: Iterable[Entry]):
        count = 0

        for entry in entries:
            if project := config.data[entry.project]:
                if experiment := project[entry.experiment]:
                    if type_ := experiment[entry.type]:
                        if type_[entry.phase]:
                            self.console.print_error(f"Entry {format_path(entry.name)} already exists.")
                            raise Exit(code=1)
                        else:
                            count += 1
                            type_.phases.append(
                                Phase(phase=str(entry.phase.value), identifier=entry.identifier, files=entry.files)
                            )
                    else:
                        count += 1
                        experiment.types.append(
                            Type(type=str(entry.type.value), phases=[
                                Phase(phase=str(entry.phase.value), identifier=entry.identifier, files=entry.files)
                            ])
                        )
                else:
                    count += 1
                    project.experiments.append(
                        Experiment(experiment=entry.experiment, types=[
                            Type(type=str(entry.type.value), phases=[
                                Phase(phase=str(entry.phase.value), identifier=entry.identifier, files=entry.files)
                            ])
                        ])
                    )
            else:
                count += 1
                config.data.append(
                    Project(project=entry.project, experiments=[
                        Experiment(experiment=entry.experiment, types=[
                            Type(type=str(entry.type.value), phases=[
                                Phase(phase=str(entry.phase.value), identifier=entry.identifier, files=entry.files)
                            ])
                        ])
                    ])
                )

        self.console.print_debug(f"Added {count} entries.")

    def remove_data(self, config: Config, entries: Iterable[Entry]):
        count = 0

        for entry in entries:
            if project := config.data[entry.project]:
                if experiment := project[entry.experiment]:
                    if type_ := experiment[entry.type]:
                        if phase := type_[entry.phase]:
                            count += 1
                            type_.phases.remove(phase)

                            if len(type_.phases) == 0:
                                experiment.types.remove(type_)
                            if len(experiment.types) == 0:
                                project.experiments.remove(experiment)
                            if len(project.experiments) == 0:
                                config.data.remove(project)

                            continue

            self.console.print_error(f"Entry {format_path(entry.name)} does not exist.")
            raise Exit(code=1)

        self.console.print_debug(f"Removed {count} entries.")

    def find_data(self, config: Config, entries: Iterable[Entry]) -> list[Entry]:
        found = OrderedSet()

        for entry in entries:
            if entry.identifier:
                for config_entry in iter_data(config.data):
                    if config_entry.identifier == entry.identifier:
                        found.add(config_entry)
            elif entry.project:
                if project := config.data[entry.project]:
                    if entry.experiment:
                        if experiment := project[entry.experiment]:
                            if entry.type:
                                if type_ := experiment[entry.type]:
                                    if entry.phase:
                                        if phase := type_[entry.phase]:
                                            found.add(Entry(project=entry.project, experiment=entry.experiment,
                                                            type=entry.type, phase=entry.phase,
                                                            identifier=phase.identifier, files=phase.files))
                                    else:
                                        for phase in type_.phases:
                                            found.add(Entry(project=entry.project, experiment=entry.experiment,
                                                            type=entry.type, phase=phase.enum,
                                                            identifier=phase.identifier, files=phase.files))
                            else:
                                for type_ in experiment.types:
                                    for phase in type_.phases:
                                        found.add(Entry(project=entry.project, experiment=entry.experiment,
                                                        type=type_.enum, phase=phase.enum,
                                                        identifier=phase.identifier, files=phase.files))
                    else:
                        for experiment in project.experiments:
                            for type_ in experiment.types:
                                for phase in type_.phases:
                                    found.add(Entry(project=entry.project, experiment=experiment.experiment,
                                                    type=type_.enum, phase=phase.enum,
                                                    identifier=phase.identifier, files=phase.files))
            else:
                for project in config.data:
                    for experiment in project.experiments:
                        for type_ in experiment.types:
                            for phase in type_.phases:
                                found.add(Entry(project=project.project, experiment=experiment.experiment,
                                                type=type_.enum, phase=phase.enum,
                                                identifier=phase.identifier, files=phase.files))

        self.console.print_debug(f"Found {len(found)} entries that match the given search terms.")
        return list(found)

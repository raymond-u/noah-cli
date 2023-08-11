import shutil
from pathlib import Path
from typing import Iterable

from .console import Console
from .network import NetworkClient
from ..helpers.common import format_path, get_file_directory, get_file_hash, get_file_name, is_empty_dir, iter_data
from ..models.app import AppPaths
from ..models.config import Config
from ..models.data import Entry


class DataManager:
    """Manage data files."""
    def __init__(self, console: Console, client: NetworkClient):
        self.console = console
        self.client = client

    def add_files(self, entries: Iterable[Entry], app_paths: AppPaths):
        count = sum(len(entry.files) for entry in entries)

        for entry in entries:
            self.console.print_debug(f"Fetching files for {format_path(entry.name)}...")
            directory = get_file_directory(app_paths.data_dir, entry)

            for file in entry.files:
                output_path = directory / get_file_name(file)

                with self.console.status(f"Fetching files ({count} left)..."):
                    count -= 1
                    self.client.fetch_file(file, output_path)

    def remove_files(self, entries: Iterable[Entry], app_paths: AppPaths):
        count = sum(len(entry.files) for entry in entries)

        for entry in entries:
            self.console.print_debug(f"Removing files for {format_path(entry.name)}...")
            directory = get_file_directory(app_paths.data_dir, entry)

            with self.console.status(f"Removing files ({count} left)..."):
                count -= len(entry.files)

                if directory.is_dir():
                    shutil.rmtree(directory)

                    # Remove parent directories if empty
                    for parent in directory.parents:
                        if parent == Path(app_paths.data_dir):
                            break

                        if is_empty_dir(parent):
                            shutil.rmtree(parent)

    def check_files(self, config: Config, app_paths: AppPaths, verify_checksum: bool) -> list[Entry]:
        entries = []

        for entry in iter_data(config.data):
            directory = get_file_directory(app_paths.data_dir, entry)

            for file in entry.files:
                output_path = directory / get_file_name(file)

                if not output_path.exists():
                    self.console.print_debug(f"File {format_path(output_path)} is missing.")
                    entries.append(entry)
                    break
                elif verify_checksum and get_file_hash(output_path) != file.checksum:
                    self.console.print_debug(f"File {format_path(output_path)} is corrupted.")
                    entries.append(entry)
                    break

        self.console.print_debug(f"Found {len(entries)} entries whose files are missing or corrupted.")
        return entries

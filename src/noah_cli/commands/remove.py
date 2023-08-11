from pathlib import Path
from typing import Annotated

from ordered_set import OrderedSet
from typer import Argument, Exit, Option

from ..app.state import config_manager, console, data_manager
from ..helpers.app import (confirm_or_quit, digest_common_options, get_app_paths, network_client, print_entries,
                           print_skipped)
from ..helpers.common import format_input, format_path
from ..helpers.database import is_accession_number, is_unsupported_accession_number
from ..models.data import Entry


def main(
        args: Annotated[list[str], Argument(help="Files to remove. Can be a list of directories, or accession numbers.",
                                            show_default=False)],
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0,
        no_confirm: Annotated[bool, Option("--yes", "-y",
                                           help="Do not prompt for confirmation.",
                                           show_default=False)] = False,
):
    """
    Remove data from the project.
    """
    # Parse common options
    digest_common_options(verbosity)

    # Load config file
    app_paths = get_app_paths()
    config = config_manager().load(app_paths)

    # Parse arguments
    if len(args) == 0:
        console().print_error("No arguments provided.")
        raise Exit(code=1)

    directories = OrderedSet[str]()
    accession_numbers = OrderedSet[str]()
    skipped = OrderedSet[str]()

    for arg in args:
        # Add all
        if arg == ".":
            directories = ["."]
            break

        # Parse as a path
        if (path := Path(arg)).exists():
            if path.is_dir():
                try:
                    path = path.resolve().relative_to(app_paths.data_dir)
                    directories.add(str(path))
                    continue
                except ValueError:
                    console().print_warning(f"{format_path(arg)} is not a data directory. Skipping.")
                    skipped.add(arg)
                    continue
            else:
                console().print_warning(f"{format_path(arg)} is not a directory. Skipping.")
                skipped.add(arg)
                continue

        # Try to parse as a path if there is a slash
        if "/" in arg:
            directories.add(arg)
            continue

        # Try to parse as an accession number
        if is_accession_number(arg):
            accession_numbers.add(arg)
            continue
        if is_unsupported_accession_number(arg):
            console().print_warning(f"{format_input(arg)} is not currently supported. Skipping.")
            skipped.add(arg)
            continue

        # If none of the above, try to parse as a project name
        directories.add(arg)

    console().print_trace(f"Directories: {directories}")
    console().print_trace(f"Accession numbers: {accession_numbers}")
    console().print_trace(f"Skipped: {skipped}")

    if directories == ["."]:
        # Use as wildcard
        entries = OrderedSet(config_manager().find_data(config, [Entry()]))
    else:
        # Handle local directory paths
        entries = OrderedSet[Entry]()

        for directory in directories:
            project = None
            experiment = None
            type_ = None
            phase = None

            for index, part in enumerate(Path(directory).parts):
                match index:
                    case 0:
                        project = part
                    case 1:
                        split = part.split("@", 1)
                        experiment = split[0]
                        type_ = split[1] if len(split) > 1 else None
                    case 2:
                        phase = part
                    case _:
                        console().print_warning(f"{format_path(directory)} contains unknown directories. Skipping.")
                        skipped.add(directory)

            entries.add(Entry(project=project, experiment=experiment, type=type_, phase=phase))

        # Fetch metadata for public accession numbers
        info = network_client().get_info_by_accession_number(accession_numbers)

        console().print_trace(f"Non-public data entries: {entries}")
        console().print_trace(f"Public data entries: {info.entries}")

        entries.update(info.entries)
        entries = OrderedSet(config_manager().find_data(config, entries))

    # Print entries and prompt for confirmation
    print_entries(entries, "will be removed")
    print_skipped(skipped)
    confirm_or_quit(len(entries) > 0, no_confirm)

    # Remove files
    data_manager().remove_files(entries, app_paths)

    # Write config file
    config_manager().remove_data(config, entries)
    config_manager().save(config, app_paths)

    console().request_for_newline()
    console().print("Done.")

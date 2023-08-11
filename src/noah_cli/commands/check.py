from typing import Annotated

from typer import Option

from ..app.state import config_manager, console, data_manager
from ..helpers.app import digest_common_options, get_app_paths, print_entries


def main(
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0,
        verify_checksum: Annotated[bool, Option("--verify",
                                                help="Verify checksums when validating files.")] = False
):
    """
    Check if local files are up-to-date.
    """
    # Parse common options
    digest_common_options(verbosity)

    # Load config file
    app_paths = get_app_paths()
    config = config_manager().load(app_paths)

    # Check data files
    if entries := data_manager().check_files(config, app_paths, verify_checksum):
        print_entries(entries, "should be updated")
    else:
        console().request_for_newline()
        console().print("Everything is up-to-date.")

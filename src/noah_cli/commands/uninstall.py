from typing import Annotated

from typer import Option

from ..app.state import config_manager, console, data_manager
from ..helpers.app import digest_common_options, get_app_paths
from ..models.data import Entry


def main(
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0,
):
    """
    Uninstall files for the project.
    """
    # Parse common options
    digest_common_options(verbosity)

    # Load config file
    app_paths = get_app_paths()
    config = config_manager().load(app_paths)

    # Uninstall files
    entries = config_manager().find_data(config, [Entry()])
    data_manager().remove_files(entries, app_paths)

    console().request_for_newline()
    console().print("Done.")

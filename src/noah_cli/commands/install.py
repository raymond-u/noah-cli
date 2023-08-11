from pathlib import Path
from typing import Annotated, Optional

from typer import Option

from ..app.state import config_manager, console, data_manager
from ..helpers.app import digest_common_options, get_app_paths
from ..models.app import EAddMode


def main(
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0,
        add_mode: Annotated[Optional[EAddMode], Option("--add-mode", "-m",
                                                       case_sensitive=False,
                                                       help="The mode to use when adding local files.",
                                                       show_default=False)] = None,
        aspera_key: Annotated[Optional[Path], Option("--aspera-key", "-k",
                                                     help="The path to the Aspera private key file.",
                                                     show_default=False)] = None,
        verify_checksum: Annotated[bool, Option("--verify",
                                                help="Verify checksums when validating files.")] = False
):
    """
    Install files for the project.
    """
    # Parse common options
    digest_common_options(verbosity, add_mode, aspera_key)

    # Load config file
    app_paths = get_app_paths()
    config = config_manager().load(app_paths)

    # Install files
    entries = data_manager().check_files(config, app_paths, verify_checksum)
    data_manager().add_files(entries, app_paths)

    console().request_for_newline()
    console().print("Done.")

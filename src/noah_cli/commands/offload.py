from typing import Annotated

from typer import Option

from . import uninstall


def main(
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0,
):
    """
    Alias for uninstall.
    """
    uninstall.main(verbosity)

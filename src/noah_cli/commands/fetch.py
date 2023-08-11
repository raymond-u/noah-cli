from typing import Annotated

from typer import Option

from . import install


def main(
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0,
):
    """
    Alias for install.
    """
    install.main(verbosity)

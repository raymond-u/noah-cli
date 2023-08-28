from typing import Annotated

from typer import Exit, Option, Typer

from .state import console
from ..commands import add, check, fetch, info, init, install, offload, remove, uninstall
from ..helpers.common import get_app_version

app = Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich"
)

app.command("init")(init.main)
app.command("add")(add.main)
app.command("remove")(remove.main)
app.command("check")(check.main)
app.command("install")(install.main)
app.command("uninstall")(uninstall.main)

app.command("fetch", hidden=True)(fetch.main)
app.command("offload", hidden=True)(offload.main)

app.add_typer(info.app, name="info")


def version_callback(value: bool):
    if value:
        version = get_app_version()
        console().print(f"Noah {version}")
        raise Exit()


@app.callback()
def main(
        version: Annotated[bool, Option("--version", "-v",
                                        callback=version_callback,
                                        help="Show the version of the program and exit.",
                                        is_eager=True)] = False
):
    """
    A project management tool for reproducible, portable, and streamlined bioinformatics analysis.
    """
    ...

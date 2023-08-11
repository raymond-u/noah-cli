from typing import Annotated, Optional

from typer import Argument, Exit, Option, Typer

from ..app.state import config_manager, console
from ..helpers.app import digest_common_options, get_app_paths
from ..helpers.common import format_input, format_section

app = Typer()


@app.callback(rich_help_panel=format_section("Info"))
def main():
    """
    Manage the information about the project.
    """
    ...


@app.command()
def show(
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0
):
    """
    Show the information about the project.
    """
    # Parse common options
    digest_common_options(verbosity)

    # Load config file
    app_paths = get_app_paths()
    config = config_manager().load(app_paths)

    # Print information
    console().request_for_newline()
    console().print(f"Author: {config.info.author or '(None)'}")
    console().print(f"Description: {config.info.description or '(None)'}")


@app.command()
def edit(
        args: Annotated[Optional[list[str]], Argument(help="Fields to edit.",
                                                      show_default=False)] = None,
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0
):
    """
    Edit the information about the project.
    """
    # Parse common options
    digest_common_options(verbosity)

    # Load config file
    app_paths = get_app_paths()
    config = config_manager().load(app_paths)

    # If no arguments are given, default to editing all fields
    if not args:
        args = ["author", "description"]
    else:
        for arg in args:
            if arg.lower() not in ("author", "description"):
                console().print_error(f"Unknown field {format_input(arg)}.")
                raise Exit(code=1)

    for arg in args:
        value = console().ask_for_string(f"Please enter a new value for {arg.lower()}", guard=lambda _: True)
        setattr(config.info, arg.lower(), value or None)

    # Write config file
    config_manager().save(config, app_paths)

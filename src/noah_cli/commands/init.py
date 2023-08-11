from inspect import cleandoc
from pathlib import Path
from typing import Annotated, Optional

from typer import Argument, Exit, Option

from ..app.state import config_manager, console
from ..helpers.app import digest_common_options, get_app_paths, sanitize_input
from ..helpers.common import format_command, format_path, is_empty_dir, program_exists, run_shell_command


def gitignore():
    return cleandoc(
        """
        # Ignore files managed by Noah
        containers
        data
        workflows
        
        # Ignore output
        results
        """
    )


def main(
        name: Annotated[Optional[str], Argument(help="The name of the new project.",
                                                show_default=False)] = None,
        verbosity: Annotated[int, Option("--verbose", "-v",
                                         count=True,
                                         help="Increase verbosity.",
                                         show_default=False)] = 0,
        no_git: Annotated[bool, Option("--no-git", "-G",
                                       help="Do not initialize a Git repository.",
                                       show_default=False)] = False
):
    """
    Create a new project.
    """
    # Parse common options
    digest_common_options(verbosity)

    # Check if it already exists
    if name is None:
        directory = Path()

        if not is_empty_dir(directory):
            console().print_error("Current directory is not empty.")
            raise Exit(code=1)
    else:
        name = sanitize_input(name)
        directory = Path(name)

        if directory.exists():
            if not is_empty_dir(directory):
                console().print_error(f"{format_path(directory)} already exists.")
                raise Exit(code=1)
        else:
            directory.mkdir()

    # Initialize a git repository
    if not no_git and not directory.joinpath(".git").exists():
        if not program_exists("git"):
            console().print_error(f"{format_command('git')} is not installed.")
            raise Exit(code=1)

        try:
            command = ["git", "init"] + ([name] if name else [])
            run_shell_command(command)
        except Exception as e:
            console().print_error(f"Failed to initialize Git repository ({e}).")
            raise Exit(code=1)

        try:
            with open(directory / ".gitignore", "w") as f:
                f.write(gitignore())
        except Exception as e:
            console().print_error(f"Failed to write {format_path(directory / '.gitignore')} ({e}).")
            raise Exit(code=1)

        console().print_debug("Initialized empty Git repository.")

    # Create config file
    app_paths = get_app_paths(directory)
    config_manager().create(app_paths)

    # Create directories
    app_paths.analysis_dir.mkdir()
    app_paths.results_dir.mkdir()
    app_paths.containers_dir.mkdir()
    app_paths.data_dir.mkdir()
    app_paths.workflows_dir.mkdir()

    console().print("Created a new project.")

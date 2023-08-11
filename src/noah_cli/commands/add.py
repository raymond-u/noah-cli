import re
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import urlparse

from ordered_set import OrderedSet
from typer import Argument, Exit, Option

from ..app.state import config_manager, console, data_manager, network_client
from ..helpers.app import (confirm_or_quit, digest_common_options, get_app_paths, print_entries, print_skipped,
                           sanitize_input, split_modifiers, split_modifiers_into_enum)
from ..helpers.common import format_input, format_path
from ..helpers.database import is_accession_number, is_unsupported_accession_number
from ..models.app import EAddMode
from ..models.data import Entry, EPhase, ESource, EType, File, Source


def main(
        args: Annotated[list[str], Argument(help="Files to add. Can be a list of local file paths, "
                                                 "remote file paths, URLs, or accession numbers.",
                                            show_default=False)],
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
        no_confirm: Annotated[bool, Option("--yes", "-y",
                                           help="Do not prompt for confirmation.",
                                           show_default=False)] = False,
        project: Annotated[Optional[str], Option("--project",
                                                 help="Modifiers for project name.",
                                                 show_default=False)] = None,
        experiment: Annotated[Optional[str], Option("--experiment",
                                                    help="Modifiers for experiment name.",
                                                    show_default=False)] = None,
        lib_type: Annotated[Optional[str], Option("--library-type",
                                                  help="Modifiers for library type.",
                                                  show_default=False)] = None,
        phase: Annotated[Optional[str], Option("--pipeline-phase",
                                               help="Modifiers for pipeline phase.",
                                               show_default=False)] = None
):
    """
    Fetch and add data to the project.
    """
    # Parse common options
    digest_common_options(verbosity, add_mode, aspera_key)

    # Load config file
    app_paths = get_app_paths()
    config = config_manager().load(app_paths)

    # Parse project, experiment, lib_type, and phase options
    project_modifiers = split_modifiers(project, "project name")
    experiment_modifiers = split_modifiers(experiment, "experiment name")
    lib_type_modifiers = split_modifiers_into_enum(lib_type, EType, "library type")
    phase_modifiers = split_modifiers_into_enum(phase, EPhase, "pipeline phase")

    # Parse arguments
    if len(args) == 0:
        console().print_error("No arguments provided.")
        raise Exit(code=1)

    local_files = OrderedSet[str]()
    ftp_files = OrderedSet[str]()
    http_files = OrderedSet[str]()
    ssh_files = OrderedSet[str]()
    public_files = OrderedSet[str]()
    skipped = OrderedSet[str]()

    for arg in args:
        # Try to parse as a local file path
        if (path := Path(arg)).exists():
            if path.is_file():
                local_files.add(str(path.resolve()))
                continue
            else:
                console().print_warning(f"{format_path(arg)} is not a file. Skipping.")
                skipped.add(arg)
                continue

        # Check if the file path has a scheme
        result = urlparse(arg)
        match result.scheme:
            case "file":
                local_files.add(result.path)
                continue
            case "ftp":
                ftp_files.add(arg)
                continue
            case "http" | "https":
                http_files.add(arg)
                continue
            case "ssh":
                parsed = urlparse(arg)
                ssh_files.add(f"{parsed.netloc}:{parsed.path}")
                continue
            case "":
                ...
            case _:
                console().print_warning(f"The scheme of {format_input(arg)} is not supported. Skipping.")
                skipped.add(arg)
                continue

        # Parse as a remote path
        if ":" in arg.split("/")[0]:
            ssh_files.add(arg)
            continue

        # Parse as a URL
        if "/" in arg:
            # Use http:// as the default scheme to account for paths pointing to LAN addresses
            console().print_warning(f"{format_input(arg)} is not a valid URL. Assuming HTTP.")
            http_files.add("http://" + arg)
            continue

        # Try to parse as an accession number
        if is_accession_number(arg):
            public_files.add(arg)
            continue
        if is_unsupported_accession_number(arg):
            console().print_warning(f"{format_input(arg)} is not currently supported. Skipping.")
            skipped.add(arg)
            continue

        # If none of the above, skip
        skipped.add(arg)
        console().print_warning(f"{format_input(arg)} cannot be parsed. Skipping.")

    # Check if any remote files have an accession number
    for file in http_files[:]:
        if match := (
                re.search(r"encodeproject\.org/experiments/(ENCSR[0-9]+[A-Z]+)", file, re.IGNORECASE)
                or re.search(r"ncbi\.nlm\.nih\.gov/geo/query/acc\.cgi\?acc=(GS[EM][0-9]+)", file, re.IGNORECASE)
                or re.search(r"ncbi\.nlm\.nih\.gov/sra(?:/|\?term=|/\?term=)([DES]R[PRSX][0-9]+)", file, re.IGNORECASE)
                or re.search(r"ncbi\.nlm\.nih\.gov/Traces/study/?\?acc=([DES]R[PRSX][0-9]+)", file, re.IGNORECASE)
                or re.search(r"trace\.ncbi\.nlm\.nih\.gov/Traces(?:/|/index\.html|/sra)?"
                             r"\?(?:study|view=study&acc)=([DES]RP[0-9]+)", file, re.IGNORECASE)
                or re.search(r"trace\.ncbi\.nlm\.nih\.gov/Traces(?:/|/index\.html|/sra)?"
                             r"\?(?:run|view=run_browser&acc)=([DES]RR[0-9]+)", file, re.IGNORECASE)
        ):
            http_files.remove(file)
            public_files.add(match.group(1))

    console().print_trace(f"Local files: {local_files}")
    console().print_trace(f"FTP files: {ftp_files}")
    console().print_trace(f"HTTP files: {http_files}")
    console().print_trace(f"SSH files: {ssh_files}")
    console().print_trace(f"Public files: {public_files}")
    console().print_trace(f"Skipped files: {skipped}")

    entries = OrderedSet[Entry]()

    # Pair paired-end sequencing files
    for files, type_ in ((local_files, ESource.LOCAL), (ftp_files, ESource.FTP),
                         (http_files, ESource.HTTP), (ssh_files, ESource.SSH)):
        while len(files) != 0 and (pair := files.pop()):
            if match := re.fullmatch(r"(.+)(_r?)([12])(\.fast[aq](?:\.gz)?)", pair, re.IGNORECASE):
                pair_target = match.group(1) + match.group(2) + ("2" if match.group(3) == "1" else "1") + match.group(4)

                if pair_target in files:
                    console().print_debug(f"Pairing {format_path(pair)} with {format_path(pair_target)}.")
                    files.remove(pair_target)
                    entries.add(
                        Entry(phase=EPhase.RAW, files=[
                            File(sources=[
                                Source(type=str(type_.value), value=pair)
                            ])
                            for pair in ((pair, pair_target) if match.group(3) == "1" else (pair_target, pair))
                        ])
                    )
                    continue
                else:
                    console().print_warning(f"{format_path(pair)} seems to be a paired-end sequencing file "
                                            "but its mate cannot be found.")

            entries.add(
                Entry(phase=EPhase.RAW, files=[
                    File(sources=[
                        Source(type=str(type_.value), value=pair)
                    ])
                ])
            )

    # Fetch metadata for public accession numbers
    query_result = network_client().get_info_by_accession_number(public_files)

    console().print_trace(f"Non-public data entries: {entries}")
    console().print_trace(f"Public data entries: {query_result.entries}")

    entries.update(query_result.entries)

    # Update metadata based on modifiers, stop at the first match
    for entry in entries:
        prompted = False

        for attr, modifiers, prompt in (("project", project_modifiers,
                                         lambda: sanitize_input(console().ask_for_string("Project name"))),
                                        ("experiment", experiment_modifiers,
                                         lambda: sanitize_input(console().ask_for_string("Experiment name"))),
                                        ("type", lib_type_modifiers,
                                         lambda: console().ask_for_enum("Library type", EType)),
                                        ("phase", phase_modifiers,
                                         lambda: console().ask_for_enum("Pipeline phase", EPhase))):
            for key, value in modifiers.items():
                # Skip empty modifiers
                if key == "":
                    continue

                # Prioritize identifiers, if present
                if entry.identifier:
                    # Match each accession number that is associated with the identifier
                    if key == entry.identifier or key in query_result.mappings[entry.identifier]:
                        console().print_debug(f"Change {attr} of {format_path(entry.name)} to {format_input(value)}.")
                        setattr(entry, attr, value)
                        break

                # Match each file path
                for path in (path.value for source in entry.files for path in source.sources):
                    if key in path:
                        console().print_debug(f"Change {attr} of {format_path(entry.name)} to {format_input(value)}.")
                        setattr(entry, attr, value)
                        break
            else:
                # If it is still empty, match the wildcard
                if not getattr(entry, attr) and "" in modifiers:
                    value = modifiers[""]
                    console().print_debug(f"Change {attr} of {format_path(entry.name)} to {format_input(value)}.")
                    setattr(entry, attr, value)

                # If the value is still empty, prompt for a value
                if not getattr(entry, attr):
                    if not prompted:
                        console().request_for_newline()
                        console().print(f"Please enter metadata for {format_path(entry.name)}.")
                        prompted = True

                    input_ = prompt()
                    setattr(entry, attr, input_)

    # Print entries and prompt for confirmation
    print_entries(entries, "will be added")
    print_skipped(skipped)
    confirm_or_quit(len(entries) > 0, no_confirm)

    # Add files
    data_manager().add_files(entries, app_paths)

    # Write config file
    config_manager().add_data(config, entries)
    config_manager().save(config, app_paths)

    console().request_for_newline()
    console().print("Done.")

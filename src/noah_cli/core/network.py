import os
import platform
import shutil
from os import PathLike
from pathlib import Path
from typing import Callable, Iterable, TypeVar
from urllib.request import urlretrieve

import requests
from fabric import Connection
from ordered_set import OrderedSet
from pysradb import SRAweb
from typer import Exit

from .console import Console
from ..helpers.common import combine_name, format_path, get_file_hash, parse_ssh_path, program_exists, run_shell_command
from ..helpers.database import get_files_from_srr
from ..models.app import EAddMode, QueryResult
from ..models.data import Entry, EPhase, ESource, EType, File

T = TypeVar("T")


class NetworkClient:
    """A client for downloading files from the internet."""
    def __init__(self, console: Console):
        self.console = console
        self.add_mode = EAddMode.LINK

        match platform.system():
            case "Darwin":
                self.aspera_key = ("/Applications/Aspera/Aspera Connect.app/Contents/"
                                   "Resources/asperaweb_id_dsa.openssh")
            case "Linux":
                self.aspera_key = "~/.aspera/connect/etc/asperaweb_id_dsa.openssh"
            case _:
                self.console.print_error("Unsupported platform.")
                raise Exit(code=1)

    def set_add_mode(self, value: EAddMode):
        self.console.print_info(f"Using {value.value} add mode.")
        self.add_mode = value

    def set_aspera_key(self, value: str | PathLike[str]):
        if Path(value).is_file():
            self.console.print_info(f"Using {format_path(value)} as the path to Aspera key.")
            self.aspera_key = value
        else:
            self.console.print_error(f"{format_path(value)} is not a valid file.")
            raise Exit(code=1)

    def get_info_by_accession_number(self, accession_numbers: Iterable[str]) -> QueryResult:
        """ Get information from a public database by accession numbers."""
        db = SRAweb()

        numbers = OrderedSet(accession_numbers)
        entries = OrderedSet()
        mappings = {}

        def update_mappings(srx: str, number: str):
            if srx in mappings:
                if number not in mappings[srx]:
                    mappings[srx].append(number)
            else:
                mappings[srx] = [number]

        def fetch_info_with_retry(function: Callable[[], T]) -> T:
            try:
                return self.fetch_with_retry(function)
            except Exception as e:
                self.console.print_error(f"Failed to retrieve information for {accession_number} ({e}).")
                raise Exit(code=1)

        while len(numbers) != 0 and (accession_number := numbers.pop().upper()):
            self.console.print_debug(f"Retrieving information for {accession_number}...")
            with self.console.status(f"Retrieving information from public databases ({len(numbers) + 1} left)..."):
                if accession_number.startswith("ENCSR"):
                    url = f"https://www.encodeproject.org/experiments/{accession_number}/?frame=object"

                    def func():
                        response = requests.get(url, headers={"accept": "application/json"})
                        response.raise_for_status()
                        for xref in response.json()["dbxrefs"]:
                            if xref.startswith("GEO:"):
                                numbers.add(xref[4:])

                    fetch_info_with_retry(func)
                elif accession_number.startswith("GSE"):
                    result = fetch_info_with_retry(lambda: db.gse_to_gsm(accession_number)["experiment_accession"])
                    numbers.update(result)
                    list(map(lambda x: update_mappings(x, accession_number), result))
                elif accession_number.startswith("GSM"):
                    result = fetch_info_with_retry(lambda: db.gsm_to_srx(accession_number)["experiment_accession"])
                    numbers.update(result)
                    list(map(lambda x: update_mappings(x, accession_number), result))
                elif accession_number[0] in "DES" and accession_number[1] == "R" and accession_number[2] in "PRSX":
                    result = fetch_info_with_retry(lambda: db.sra_metadata(accession_number))

                    # Generate entries for each record
                    for _, row in result.iterrows():
                        project = combine_name(row["study_accession"], row["study_title"])
                        experiment = combine_name(row["experiment_accession"], row["experiment_title"])

                        match row["library_strategy"]:
                            # Possible values (as per SRA Handbook):
                            # WGA       - Random sequencing of the whole genome following non-pcr amplification
                            # WGS       - Random sequencing of the whole genome
                            # WXS       - Random sequencing of exonic regions selected from the genome
                            # RNA-Seq   - Random sequencing of whole transcriptome
                            # miRNA-Seq - Random sequencing of small miRNAs
                            # WCS       - Random sequencing of a whole chromosome
                            #             or other replicon isolated from a genome
                            # CLONE     - Genomic clone based (hierarchical) sequencing
                            # POOLCLONE - Shotgun of pooled clones (usually BACs and Fosmids)
                            # AMPLICON  - Sequencing of overlapping or distinct PCR or RT-PCR products
                            # CLONEEND  - Clone end (5', 3', or both) sequencing
                            # FINISHING - Sequencing intended to finish (close) gaps in existing coverage
                            # ChIP-Seq  - Direct sequencing of chromatin immunoprecipitates
                            # MNase-Seq - Direct sequencing following MNase digestion
                            # DNase-Hypersensitivity - Sequencing of hypersensitive sites, or segments of
                            #                          open chromatin that are more readily cleaved by DNaseI
                            # Bisulfite-Seq - Sequencing following treatment of DNA with bisulfite
                            #                 to convert cytosine residues to uracil depending on methylation status
                            # Tn-Seq    - Sequencing from transposon insertion sites
                            # EST       - Single pass sequencing of cDNA templates
                            # FL-cDNA   - Full-length sequencing of cDNA templates
                            # CTS       - Concatenated Tag Sequencing
                            # MRE-Seq   - Methylation-Sensitive Restriction Enzyme Sequencing strategy
                            # MeDIP-Seq - Methylated DNA Immunoprecipitation Sequencing strategy
                            # MBD-Seq   - Direct sequencing of methylated fractions sequencing strategy
                            # OTHER     - Library strategy not listed
                            case "ChIP-Seq":
                                type_ = EType.CHIP
                            case "RNA-Seq":
                                type_ = EType.RNA
                            case _:
                                type_ = None

                        phase = EPhase.RAW
                        identifier = row["experiment_accession"]
                        files = get_files_from_srr(row["run_accession"], row["library_layout"] == "PAIRED")

                        entries.add(Entry(project=project, experiment=experiment, type=type_,
                                          phase=phase, identifier=identifier, files=files))

                        # Associate accession numbers with SRX so that they can be used as a search term
                        update_mappings(identifier, row["study_accession"])
                        update_mappings(identifier, row["sample_accession"])
                        update_mappings(identifier, row["run_accession"])
                else:
                    self.console.print_error(f"{accession_number} is not a valid accession number.")
                    raise Exit(code=1)

        return QueryResult(list(entries), mappings)

    def fetch_file(self, file: File, path: str | PathLike[str]):
        """Download a file."""
        if (output_path := Path(path)).exists():
            if output_path.is_file():
                output_path.unlink()
            else:
                shutil.rmtree(output_path)
        else:
            output_path.parent.mkdir(exist_ok=True, parents=True)

        for source in file.sources:
            try:
                match source.type:
                    case ESource.ASPERA:
                        self.fetch_with_aspera(source.value, output_path)
                        break
                    case ESource.FTP:
                        self.fetch_from_ftp(source.value, output_path)
                        break
                    case ESource.HTTP:
                        self.fetch_from_http(source.value, output_path)
                        break
                    case ESource.LOCAL:
                        self.fetch_from_local(source.value, output_path)
                        break
                    case ESource.SSH:
                        self.fetch_over_ssh(source.value, output_path)
                        break
            except Exception as e:
                self.console.print_warning(f"Failed to fetch file from {format_path(source.value)} ({e}).")
        else:
            self.console.print_error(f"Failed to fetch file from any of the sources.")
            raise Exit(code=1)

        if file.checksum:
            if get_file_hash(output_path) != file.checksum:
                self.console.print_error(f"File {format_path(output_path)} failed checksum verification.")
                raise Exit(code=1)
        else:
            file.checksum = get_file_hash(output_path)

    def fetch_with_retry(self, func: Callable[[], T], retries: int = 3) -> T:
        """Fetch a resource with retries."""
        for _ in range(retries):
            try:
                return func()
            except Exception as e:
                self.console.print_warning(f"Network request failed ({e}).")

        raise RuntimeError(f"network request failed after {retries} retries")

    def fetch_with_aspera(self, url: str, path: str | PathLike[str]):
        """Download a file with Aspera Connect."""
        if not program_exists("ascp"):
            raise RuntimeError("Aspera Connect is not installed")

        self.console.print_debug(f"Downloading {url} to {path} via Aspera Connect...")

        command = ["ascp", "-QT", "-k2", "-l300m", "-P33001", "-i", self.aspera_key, url, str(path)]
        self.fetch_with_retry(lambda: run_shell_command(command))

    def fetch_from_ftp(self, url: str, path: str | PathLike[str]):
        """Download a file from an FTP server."""
        self.console.print_debug(f"Downloading {url} to {path} via FTP...")
        self.fetch_with_retry(lambda: urlretrieve(url, path))

    def fetch_from_http(self, url: str, path: str | PathLike[str]):
        """Download a file from an HTTP server."""
        self.console.print_debug(f"Downloading {url} to {path} via HTTP...")
        self.fetch_with_retry(lambda: urlretrieve(url, path))

    def fetch_from_local(self, url: str, path: str | PathLike[str]):
        """Get a file from the local filesystem."""
        def func():
            match self.add_mode:
                case EAddMode.COPY:
                    shutil.copy(url, path)
                case EAddMode.LINK:
                    os.symlink(url, path)
                case EAddMode.MOVE:
                    shutil.move(url, path)

        self.console.print_debug(f"Copying {url} to {path} from local filesystem...")
        self.fetch_with_retry(func)

    def fetch_over_ssh(self, url: str, path: str | PathLike[str]):
        """Download a file over SSH."""
        host, remote_path = parse_ssh_path(url)

        def func():
            password = self.console.ask_for_string(f"Enter password for {host}", default="", guard=lambda _: True)

            with Connection(host, connect_kwargs={"password": password}) as conn:
                conn.get(remote_path, path)

        self.console.print_debug(f"Downloading {url} to {path} via SSH...")
        self.fetch_with_retry(func)

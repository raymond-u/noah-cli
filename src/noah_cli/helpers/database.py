import re

from ..models.data import ESource, File, Source


def is_accession_number(accession_number: str) -> bool:
    """Check if a string is an accession number."""
    # Check if the file path is an ENCODE accession number, a GEO accession number, or an SRA accession number
    if (
            re.fullmatch(r"ENCSR[0-9]+[A-Z]+", accession_number, re.IGNORECASE)
            # SR - An assay (ENCODE)
            or re.fullmatch(r"GS[EM][0-9]+", accession_number, re.IGNORECASE)
            # E - A series (GEO)
            # M - A sample (GEO)
            or re.fullmatch(r"[DES]R[PRSX][0-9]+", accession_number, re.IGNORECASE)
            # P – A project (SRA)
            # R – A run (SRA)
            # S – A sample (SRA)
            # X – An experiment (SRA)
    ):
        return True

    return False


def is_unsupported_accession_number(accession_number: str) -> bool:
    """Check if a string is an unsupported accession number."""
    # Check if the file path is a GSE accession number
    # Check if the file path is an ENCODE accession number, a GEO accession number, or an SRA accession number
    if (
            re.fullmatch(r"ENC(?:AB|BS|DO|FF|GM|LB|PL)[0-9]+[A-Z]+", accession_number, re.IGNORECASE)
            # AB - An antibody lot (ENCODE)
            # BS - A sample (ENCODE)
            # DO - A strain or donor (ENCODE)
            # FF - A file (ENCODE)
            # GM - A genetic modification (ENCODE)
            # LB - A library (ENCODE)
            # PL - A pipeline (ENCODE)
            or re.fullmatch(r"PRJ(?:DB|EB|NA)[0-9]+", accession_number, re.IGNORECASE)
            # DB - DDBJ
            # EB - ENA
            # NA - NCBI
            or re.fullmatch(r"SAM(?:D|EA|N)[0-9]+", accession_number, re.IGNORECASE)
            # D - DDBJ
            # EA - ENA
            # N - NCBI
    ):
        return True

    return False


def get_files_from_srr(srr: str, paired: bool) -> list[File]:
    """Get a list of files from an SRA accession number."""
    if paired:
        aspera_urls = get_aspera_url_from_srr(srr, paired=True)
        ftp_urls = get_ftp_url_from_srr(srr, paired=True)

        return [
            File(
                sources=[
                    Source(type=str(ESource.ASPERA.value), value=aspera_urls[i]),
                    Source(type=str(ESource.FTP.value), value=ftp_urls[i])
                ],
                checksum=None
            ) for i in (0, 1)
        ]
    else:
        aspera_url = get_aspera_url_from_srr(srr, paired=False)
        ftp_url = get_ftp_url_from_srr(srr, paired=False)

        return [
            File(
                sources=[
                    Source(type=str(ESource.ASPERA.value), value=aspera_url),
                    Source(type=str(ESource.FTP.value), value=ftp_url)
                ],
                checksum=None
            )
        ]


def get_aspera_url_from_srr(srr: str, paired: bool) -> str | tuple[str, str]:
    """Get the Aspera URL from an SRA accession number."""
    path = (f"era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/{srr[:6]}/"
            f"{f'{int(srr[9 - len(srr):]):03d}/' if len(srr) > 9 else ''}"
            f"{srr}/{srr}")

    if paired:
        return f"{path}_1.fastq.gz", f"{path}_2.fastq.gz"
    else:
        return f"{path}.fastq.gz"


def get_ftp_url_from_srr(srr: str, paired: bool) -> str | tuple[str, str]:
    """Get the FTP URL from an SRA accession number."""
    path = (f"ftp://ftp.sra.ebi.ac.uk/vol1/fastq/{srr[:6]}/"
            f"{f'{int(srr[9 - len(srr):]):03d}/' if len(srr) > 9 else ''}"
            f"{srr}/{srr}")

    if paired:
        return f"{path}_1.fastq.gz", f"{path}_2.fastq.gz"
    else:
        return f"{path}.fastq.gz"

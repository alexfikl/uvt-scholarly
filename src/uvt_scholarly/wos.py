# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
import pathlib

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import (
    Author,
    Category,
    DocumentType,
    ORCiD,
    Pages,
    Publication,
    ResearcherID,
)

log = make_logger(__name__)

# {{{ Field Tags

# https://support.clarivate.com/ScientificandAcademicResearch/s/article/Web-of-Science-Core-Collection-List-of-field-tags-in-output
WOS_FIELD_TAGS = {
    "AB": "Abstract",
    "AF": "Author Full Name",
    "AR": "Article Number",
    "AU": "Authors",
    "BA": "Book Authors",  # spell: disable
    "BE": "Editors",
    "BF": "Book Authors Full Name",
    "BN": "International Standard Book Number (ISBN)",
    "BP": "Beginning Page",
    "BS": "Book Series Subtitle",
    "C1": "Author Address",
    "CA": "Group Authors",
    "CL": "Conference Location",
    "CR": "Cited References",
    "CT": "Conference Title",
    "CY": "Conference Date",
    "D2": "Book Digital Object Identifier (DOI)",
    "DE": "Author Keywords",
    "DI": "Digital Object Identifier (DOI)",
    "DT": "Document Type",
    "EF": "End of File",
    "EI": "Electronic International Standard Serial Number (eISSN)",
    "EM": "E-mail Address",
    "EP": "Ending Page",
    "ER": "End of Record",
    "FN": "File Name",
    "FU": "Funding Agency and Grant Number",
    "FX": "Funding Text",
    "GA": "Document Delivery Number",
    "GP": "Book Group Authors",
    "HO": "Conference Host",
    "ID": "Keywords Plus®",
    "IS": "Issue",
    "J9": "29-Character Source Abbreviation",
    "JI": "ISO Source Abbreviation",
    "LA": "Language",
    "MA": "Meeting Abstract",
    "NR": "Cited Reference Count",
    "OI": "ORCID Identifier (Open Researcher and Contributor ID)",
    "P2": "Chapter Count (Book Citation Index)",
    "PA": "Publisher Address",
    "PD": "Publication Date",
    "PG": "Page Count",
    "PI": "Publisher City",
    "PM": "PubMed ID",
    "PN": "Part Number",  # spell: disable
    "PT": "Publication Type (J=Journal; B=Book; S=Series; P=Patent)",
    "PU": "Publisher",
    "PY": "Year Published",
    "RI": "ResearcherID Number",
    "RP": "Reprint Address",
    "SC": "Research Areas",
    "SE": "Book Series Title",
    "SI": "Special Issue",
    "SN": "International Standard Serial Number (ISSN)",
    "SO": "Publication Name",
    "SP": "Conference Sponsors",
    "SU": "Supplement",
    "TC": "Web of Science Core Collection Times Cited Count",
    "TI": "Document Title",
    "U1": "Usage Count (Last 180 Days)",
    "U2": "Usage Count (Since 2013)",
    "UT": "Accession Number",
    "VL": "Volume",
    "VR": "Version Number",
    "WC": "Web of Science Categories",
    "Z9": "Total Times Cited Count",
}


# }}}

# {{{ publication type


@enum.unique
class PublicationType(enum.Enum):
    Book = enum.auto()
    Conference = enum.auto()
    Journal = enum.auto()
    Patent = enum.auto()
    Preprint = enum.auto()
    Series = enum.auto()


PUBLICATION_TYPE = {
    "B": PublicationType.Book,
    "J": PublicationType.Journal,
    "P": PublicationType.Patent,
    "S": PublicationType.Series,
    # NOTE: Not mentioned in documentation?
    "C": PublicationType.Conference,
}

# }}}

# {{{ document type

# https://support.clarivate.com/ScientificandAcademicResearch/s/article/Web-of-Science-Core-Collection-Document-Type-Descriptions
DOCUMENT_TYPE = {
    "Art Exhibit Review": DocumentType.Review,
    "Article": DocumentType.Article,
    "Bibliography": DocumentType.Other,
    "Biographical-Item": DocumentType.Other,
    "Book Chapter": DocumentType.BookChapter,
    "Book Review": DocumentType.Review,
    "Book": DocumentType.Book,
    "Correction": DocumentType.Other,
    "Dance Performance Review": DocumentType.Review,
    "Data Paper": DocumentType.Dataset,
    "Database Review": DocumentType.Review,
    "Early Access": DocumentType.Article,
    "Editorial Material": DocumentType.Other,
    "Excerpt": DocumentType.Other,
    "Expression of Concern": DocumentType.Other,
    "Fiction, Creative Prose": DocumentType.Other,
    "Film Review": DocumentType.Review,
    "Hardware Review": DocumentType.Review,
    "Item Withdrawal": DocumentType.Other,
    "Letter": DocumentType.Other,
    "Meeting Abstract": DocumentType.Report,
    "Meeting Summary": DocumentType.Report,
    "Meeting": DocumentType.Other,
    "Music Performance Review": DocumentType.Review,
    "Music Score Review": DocumentType.Review,
    "Music Score": DocumentType.Other,
    "News Item": DocumentType.Other,
    "Poetry": DocumentType.Other,
    "Proceedings Paper": DocumentType.ProceedingsPaper,
    "Publication with Expression of Concern": DocumentType.Other,
    "Record Review": DocumentType.Review,
    "Reprint": DocumentType.Article,
    "Retracted Publication": DocumentType.Article,
    "Retraction": DocumentType.Other,
    "Review": DocumentType.Review,
    "Script": DocumentType.Other,
    "Software Review": DocumentType.Review,
    "TV Review, Radio Review": DocumentType.Review,
    "Theater Review": DocumentType.Review,
    "Withdrawn Publication": DocumentType.Article,
    # NOTE: These are no longer used
    "Abstract of Published Item": DocumentType.Other,
    "Chronology": DocumentType.Review,
    "Discussion": DocumentType.Report,
    "Item About an Individual": DocumentType.Review,
    "Note": DocumentType.Other,
    "TV Review, Radio Review, Video Review": DocumentType.Review,
}

# }}}

# {{{ import csv

CSV_REQUIRED_COLUMNS = {
    "AF",  # Authors
    "DI",  # DOI
    "DT",  # Document Type
    "EI",  # eISSN
    "IS",  # Issue
    "PY",  # Year
    "SN",  # ISSN
    "SO",  # Journal Name
    "TC",  # Web of Science Total Cited Count
    "TI",  # Document Title
    "VL",  # Volume
    "BP",  # Beginning Page
    "EP",  # Ending Page
    "PG",  # Page Count
    "UT",  # Accession Number
    "WC",  # Web of Science Categories
}


def parse_researcher_ids(text: str) -> dict[tuple[str, str], ResearcherID]:
    result = {}
    for value in text.split(";"):
        if "/" not in value:
            continue

        name, rid = value.split("/")
        last_name, first_name = name.split(",")
        key = last_name.strip(), first_name.strip()

        result[key] = ResearcherID.from_string(rid)

    return result


def parse_orcids(text: str) -> dict[tuple[str, str], ORCiD]:
    result = {}
    for value in text.split(";"):
        if "/" not in value:
            continue

        name, oid = value.split("/")
        last_name, first_name = name.split(",")
        key = last_name.strip(), first_name.strip()

        result[key] = ORCiD.from_string(oid)

    return result


def parse_wos_authors(
    text: str,
    *,
    researcherid: str | None = None,
    orcid: str | None = None,
) -> tuple[Author, ...]:
    from uvt_scholarly.publication import Author

    researcherids = parse_researcher_ids(researcherid) if researcherid else {}
    orcids = parse_orcids(orcid) if orcid else {}

    result = []
    for author in text.split(";"):
        last_name, first_name = author.split(",")
        first_name = first_name.strip()
        last_name = last_name.strip()

        result.append(
            Author(
                first_name=first_name,
                last_name=last_name,
                affiliations=(),
                researcherid=researcherids.get((last_name, first_name)),
                orcid=orcids.get((last_name, first_name)),
            )
        )

    return tuple(result)


def parse_pages(start: str, end: str, count: str) -> Pages:
    start = start.strip()
    end = end.strip()
    count = count.strip()

    if not count:
        if start.isdigit() and end.isdigit():
            icount = int(end) - int(start) + 1
        else:
            icount = None
    else:
        icount = int(count) if count.isdigit() else None

    return Pages(start=start, end=end if end else None, count=icount)


def parse_wos_categories(text: str) -> tuple[Category, ...]:
    def from_string(cat: str) -> Category:
        if "," in cat:
            name, field = cat.split(",", maxsplit=1)
            field = field.strip()
        else:
            name = cat
            field = None

        return Category(name.strip(), field)

    return tuple(from_string(cat.strip()) for cat in text.split(";"))


def read_from_csv(
    filename: pathlib.Path,
    *,
    encoding: str = "utf-8",
    delimiter: str = "\t",
) -> tuple[Publication, ...]:
    import csv

    from uvt_scholarly.publication import DOI, ISSN, Journal

    with open(filename, encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("csv files does not have column names")

        columns = {name.strip() for name in reader.fieldnames}
        if missing := CSV_REQUIRED_COLUMNS - columns:
            raise ValueError(f"Web of Science export missing columns: {missing}")

        result = []
        for i, row in enumerate(reader):
            eissn = row.get("EI", "").strip()
            dtype = row.get("DT", "").strip()
            if dtype not in DOCUMENT_TYPE:
                log.warning(
                    "Document %d does not have a known document type: '%s'.", i, dtype
                )

            publication = Publication(
                authors=parse_wos_authors(row["AU"]),
                title=row["TI"].strip(),
                journal=Journal(row["SO"].strip()),
                year=int(row["PY"].strip()),
                volume=row["VL"].strip(),
                issue=row["IS"].strip().upper(),
                pages=parse_pages(row["BP"], row["EP"], row["PG"]),
                dtype=DOCUMENT_TYPE.get(dtype, DocumentType.Other),
                doi=DOI.from_string(row["DI"].strip()),
                issn=ISSN.from_string(row["IS"].strip()),
                eissn=ISSN.from_string(eissn) if eissn else None,
                categories=parse_wos_categories(row["WC"]),
                citations=(),
                identifier=row["UT"],
            )

            result.append(publication)

    return tuple(result)


# }}}

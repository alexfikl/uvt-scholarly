# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import (
    DOI,
    ISSN,
    Author,
    Category,
    CitedPublication,
    DocumentType,
    ORCiD,
    Pages,
    Publication,
    ResearcherID,
)

if TYPE_CHECKING:
    import pathlib

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


def parse_doi(text: str) -> DOI | None:
    text = text.strip()
    if not text:
        return None

    doi = DOI.from_string(text)
    if not doi.is_valid:
        raise ValueError(f"DOI is not valid: {doi}")

    return doi


def parse_issn(text: str) -> ISSN | None:
    text = text.strip()
    if not text:
        return None

    issn = ISSN.from_string(text)
    if not issn.is_valid:
        raise ValueError(f"ISSN is not valid: '{issn}'")

    return issn


def parse_rids(text: str, *, sep: str = ";") -> dict[tuple[str, str], ResearcherID]:
    result = {}
    for value in text.split(sep):
        if "/" not in value:
            continue

        name, rid = value.split("/")
        last_name, first_name = [part.strip() for part in name.split(",")]

        # NOTE: we use a (last_name, initial) tuple to disambiguate authors here.
        # There seem to be plenty of typos and mismatches between the AF field
        # and the RI / OI fields for author names, so it's not clear if we can do
        # any better without getting false negatives..
        result[last_name, first_name[0]] = ResearcherID.from_string(rid)

    return result


def parse_orcids(text: str, *, sep: str = ";") -> dict[tuple[str, str], ORCiD]:
    result = {}
    for value in text.split(sep):
        if "/" not in value:
            continue

        name, oid = value.split("/")
        last_name, first_name = [part.strip() for part in name.split(",")]

        result[last_name, first_name[0]] = ORCiD.from_string(oid)

    return result


def parse_wos_authors(
    text: str,
    *,
    author_separator: str = ";",
    id_separator: str = ";",
    researcherid: str | None = None,
    orcid: str | None = None,
) -> tuple[Author, ...]:
    from uvt_scholarly.publication import Author

    researcherids = parse_rids(researcherid, sep=id_separator) if researcherid else {}
    orcids = parse_orcids(orcid, sep=id_separator) if orcid else {}

    result = []
    for author in text.replace("\n", " ").split(author_separator):
        last_name, first_name = author.split(",")
        first_name = first_name.strip()
        last_name = last_name.strip()

        result.append(
            Author(
                first_name=first_name,
                last_name=last_name,
                affiliations=(),
                researcherid=researcherids.get((last_name, first_name[0])),
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


def parse_wos_citations(text: str, sep: str = ";") -> dict[DOI, CitedPublication]:
    text = text.strip()
    if not text:
        return {}

    def clean_doi_text(text: str) -> str:
        # NOTE: some DOIs seem to have escaped characters (mainly _)
        text = text.replace("\\", "").replace("DOI", "")

        # NOTE: some entries seem to have multiple DOIs [..., ...], but all examples
        # found this far just show duplicates, so we choose the last one.
        if "[" in text:
            *_, text = text.split(",")
            text = text.strip(" ]")

        return text.strip()

    result = {}
    for citation in text.split(sep):
        parts = [part.strip(" .") for part in citation.split(",")]
        if len(parts) < 4:
            log.debug("Cannot parse citation (unexpected parts): '%s'.", citation)
            continue

        author, year, journal = parts[0], parts[1], parts[2]
        if not year.isdigit():
            log.debug("Cannot parse citation (year is not an int): '%s'.", citation)
            continue

        if "DOI" not in citation:
            log.debug("Cannot parse citation (DOI not found): '%s'.", citation)
            continue

        _, doitext = citation.split("DOI", maxsplit=1)
        if "arXiv" in doitext:
            log.debug("Cannot parse citation (DOI not found): '%s'.", citation)
            continue

        try:
            doi = DOI.from_string(clean_doi_text(doitext))
            is_valid = doi.is_valid
        except ValueError:
            is_valid = False

        if not is_valid:
            log.debug("Cannot parse citation (DOI is not valid): '%s'", citation)
            continue

        author = author.strip()
        if " " in author:
            last_name, _ = author.split(" ", maxsplit=1)
        elif "." in author:
            # NOTE: found an author like "Chandra.S", which seems to have been
            # shortened from "Subrahmanyan Chandrasekhar, F. R. S.". Not sure
            # what that's about, but we just split a bit of it..
            last_name, _ = author.split(".", maxsplit=1)
        else:
            last_name = author

        pub = CitedPublication(
            first_author=last_name,
            journal=" ".join(f"{part}.".title() for part in journal.split()),
            year=int(year),
            doi=doi,
        )

        result[doi] = pub

    return result


def read_from_csv(
    filename: pathlib.Path,
    *,
    encoding: str = "utf-8",
    delimiter: str = "\t",
    include_citations: bool = False,
) -> tuple[Publication, ...]:
    if not filename.exists():
        raise FileNotFoundError(filename)

    import csv

    from uvt_scholarly.publication import Journal

    with open(filename, encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("csv files does not have column names")

        columns = {name.strip() for name in reader.fieldnames}
        if missing := CSV_REQUIRED_COLUMNS - columns:
            raise ValueError(f"Web of Science export missing columns: {missing}")

        from titlecase import titlecase

        result = []
        for i, row in enumerate(reader):
            dtypes = [dtype.strip() for dtype in row.get("DT", "").split(";")]

            if any(dtype not in DOCUMENT_TYPE for dtype in dtypes):
                log.warning(
                    "Document %d does not have a known document type: '%s'.", i, dtypes
                )

            try:
                pub = Publication(
                    authors=parse_wos_authors(
                        row["AU"],
                        researcherid=row.get("RI"),
                        orcid=row.get("OI"),
                    ),
                    title=titlecase(row["TI"].strip()),
                    journal=Journal(titlecase(row["SO"].strip())),
                    year=int(row["PY"].strip()),
                    volume=row["VL"].strip(),
                    issue=row["IS"].strip().upper(),
                    pages=parse_pages(row["BP"], row["EP"], row["PG"]),
                    dtype=DOCUMENT_TYPE.get(dtypes[0], DocumentType.Other),
                    doi=parse_doi(row.get("DI", "")),
                    issn=parse_issn(row.get("SN", "")),
                    eissn=parse_issn(row.get("EI", "")),
                    categories=parse_wos_categories(row["WC"]),
                    identifier=row["UT"],
                    cited_by_count=int(row["TC"]),
                    cited_by=(),
                    citations=(
                        parse_wos_citations(row.get("CR", ""))
                        if include_citations
                        else {}
                    ),
                )
            except Exception as exc:
                log.error("Failed to parse entry on row %d.", i, exc_info=exc)
                continue

            result.append(pub)

    return tuple(result)


# }}}


# {{{ import BibTeX


def parse_bib_pages(pages: str) -> Pages:
    if "-" not in pages:
        return Pages(pages.strip().upper(), None, None)

    start, end = [p.strip() for p in pages.split("-") if p]
    if start.isdigit() and end.isdigit():  # noqa: SIM108
        count = int(end) - int(start) + 1
    else:
        count = None

    return Pages(start, end, count)


def read_from_bib(
    filename: pathlib.Path,
    *,
    encoding: str = "utf-8",
    include_citations: bool = False,
) -> tuple[Publication, ...]:
    if not filename.exists():
        raise FileNotFoundError(filename)

    from bibtexparser.bparser import BibTexParser

    parser = BibTexParser(
        common_strings=True,
        ignore_nonstandard_types=False,
        homogenize_fields=False,
        interpolate_strings=True,
    )

    with open(filename, encoding=encoding) as fd:
        entries = parser.parse(fd.read(), partial=True).entries

    from titlecase import titlecase

    from uvt_scholarly.publication import Journal

    def clean(text: str) -> str:
        return text.replace("\\", "").replace("\n", " ").strip()

    result = []
    for entry in entries:
        authors = parse_wos_authors(
            clean(entry["author"]),
            researcherid=entry.get("researcherid-numbers", ""),
            orcid=entry.get("orcid-numbers", ""),
            author_separator=" and ",
            id_separator="\n",
        )
        issue = entry.get("number", entry.get("issue", "")).strip()
        journal = clean(entry.get("journal", entry.get("booktitle", "")))

        try:
            pub = Publication(
                authors=authors,
                title=titlecase(clean(entry["title"])),
                journal=Journal(titlecase(clean(journal))),
                year=int(entry["year"].strip()),
                volume=entry.get("volume", "").strip(),
                issue=issue,
                pages=parse_bib_pages(entry.get("pages", "")),
                dtype=DOCUMENT_TYPE.get(entry["type"].strip(), DocumentType.Other),
                doi=parse_doi(entry.get("doi", "")),
                issn=parse_issn(entry.get("issn", "")),
                eissn=parse_issn(entry.get("eissn", "")),
                categories=parse_wos_categories(
                    clean(entry.get("web-of-science-categories", ""))
                ),
                identifier=entry["ID"],
                cited_by_count=int(entry["times-cited"]),
                cited_by=(),
                citations=(
                    parse_wos_citations(entry.get("cited-references", ""), sep="\n")
                    if include_citations
                    else {}
                ),
            )
        except Exception as exc:
            log.error("Failed to parse entry with ID '%s'.", entry["ID"], exc_info=exc)
            continue

        result.append(pub)

    return tuple(result)


# }}}

# {{{ read_pubs


def read_pubs(
    filename: pathlib.Path,
    *,
    encoding: str = "utf-8",
    include_citations: bool = False,
) -> tuple[Publication, ...]:
    if filename.suffix.lower() in {".txt", ".csv", ".tsv"}:
        return read_from_csv(
            filename, encoding=encoding, include_citations=include_citations
        )
    elif filename.suffix.lower() in {".bib"}:
        return read_from_bib(
            filename, encoding=encoding, include_citations=include_citations
        )
    else:
        raise ValueError(
            f"unknown file format: '{filename}' (expected .csv, .tsv, .bib)"
        )


# }}}

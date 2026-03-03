# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from uvt_scholarly.export.common import POSITION_NAME, Position
from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import DocumentType, Publication

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

log = make_logger(__name__)

# {{{ utils

RECENT_YEAR_CUTOFF = 5
"""The span over which the publication is considered."""


def filter_csv_format_authors(pub: Publication) -> str:
    return ", ".join(f"{au.first_name[0]}. {au.last_name}" for au in pub.authors)


def filter_csv_format_volume(pub: Publication) -> str:
    parts = []
    if pub.volume:
        parts.append(f"vol. {pub.volume}")

    if pub.issue:
        parts.append(f"nr. {pub.issue}")

    if pages := str(pub.pages):
        parts.append(f"pp. {pages}".replace("--", "-"))

    return ", ".join(parts)


# }}}


# {{{ category


@enum.unique
class Category(enum.IntEnum):
    AA = 4
    A = 3
    B = 2
    C = 1
    D = 0


CATEGORY_POINTS = {
    Category.AA: 12,
    Category.A: 8,
    Category.B: 4,
    Category.C: 2,
    Category.D: 1,
}


# }}}

# {{{ criteria


@dataclass(frozen=True)
class Criteria:
    position: Position
    min_perspective_b: dict[Category, float]
    min_perspective_c: dict[Category, float]
    min_perspective_d: float
    min_total: float

    @property
    def position_name(self) -> str:
        return POSITION_NAME[self.position]


MIN_CRITERIA_FOR_POSITION = {
    # academic
    Position.Professor: Criteria(
        Position.Professor,
        {Category.A: 24, Category.B: 40, Category.D: 56},
        {Category.B: 40, Category.D: 120},
        60,
        236,
    ),
    Position.AssociateProfessor: Criteria(
        Position.AssociateProfessor,
        {Category.B: 16, Category.D: 32},
        {Category.B: 12, Category.D: 48},
        36,
        116,
    ),
    Position.AssistantProfessor: Criteria(
        Position.AssistantProfessor,
        {Category.D: 12},
        {Category.D: 10},
        4,
        26,
    ),
    Position.Assistant: Criteria(
        Position.Assistant,
        {Category.D: 2},
        {Category.D: 0},
        0,
        2,
    ),
    # research
    Position.SeniorResearcher: Criteria(
        Position.SeniorResearcher,
        {Category.A: 24, Category.B: 40, Category.D: 56},
        {Category.B: 40, Category.D: 120},
        60,
        236,
    ),
    Position.Researcher: Criteria(
        Position.Researcher,
        {Category.B: 16, Category.D: 32},
        {Category.B: 12, Category.D: 48},
        36,
        116,
    ),
    Position.JuniorResearcher: Criteria(
        Position.JuniorResearcher,
        {Category.D: 12},
        {Category.D: 10},
        4,
        26,
    ),
}

# }}}

# {{{ Candidate


@dataclass(frozen=True)
class Candidate:
    qualname: str
    publications: Sequence[Publication]
    conferences: Sequence[Publication]
    books: Sequence[Publication]
    score_b: float
    score_c: float
    score_d: float
    score_total: float
    hirsch: dict[str, int]


def sortedpubs(pubs: Sequence[Publication]) -> tuple[Publication, ...]:
    return tuple(sorted(pubs, key=lambda p: p.year, reverse=True))


def make_candidate(
    name: str,
    pubs: Sequence[Publication],
    *,
    position: Position = Position.Professor,
) -> Candidate:
    from datetime import datetime

    most_recent_year = datetime.now().year - RECENT_YEAR_CUTOFF

    publications = []
    conferences = []
    books = []

    def update_citations(pub: Publication) -> Publication:
        cited_by = []
        for cite in pub.cited_by:
            if cite.year < most_recent_year:
                continue

            cited_by.append(cite)

        return replace(
            pub,
            cited_by=sortedpubs(cited_by),
            cited_by_count=len(cited_by),
        )

    for pub in pubs:
        if pub.year < most_recent_year:
            continue

        if pub.dtype in {DocumentType.Book, DocumentType.BookChapter}:
            books.append(update_citations(pub))
        elif pub.dtype == DocumentType.ProceedingsPaper:
            conferences.append(update_citations(pub))
        elif pub.dtype in {DocumentType.Article, DocumentType.Review}:
            publications.append(update_citations(pub))
        else:
            log.warning(
                "Publication has unknown type '%s': '%s'", pub.dtype.name, pub.title
            )

    return Candidate(
        qualname=name,
        publications=sortedpubs(publications),
        conferences=sortedpubs(conferences),
        books=sortedpubs(books),
        score_b=0.0,
        score_c=0.0,
        score_d=0.0,
        score_total=0.0,
        hirsch={},
    )


# }}}


# {{{ export_publications_csv

PUBLICATION_FIELD_NAMES = (
    "Nr. crt.",
    "Titlu",
    "Autori",
    "Revista",
    "Vol., nr., pg.",
    "An",
    "Categorie forum",  # spell: disable
    "Nr. autori",
    "Punctaj P",
    "Număr citări",
    "Punctaj citări",
    "Punctaj citări",
)

CONFERENCE_FIELD_NAMES = (
    "Nr. crt.",
    "Titlu",
    "Autori",
    "Conferință",
    "Vol., nr., pg.",
    "An",
    "Categorie forum",  # spell: disable
    "Nr. autori",
    "Volum Workshop",
    "Punctaj P",
    "Număr citări",
    "Punctaj citări",
    "Punctaj citări",
)

CITATION_FIELD_NAMES = (
    "Nr. Crt.",
    "Titlu",
    "Autori",
    "Forum (Revistă, Conferință)",
    "Vol., nr., pg.",
    "An",
    "Categorie forum",  # spell: disable
    "Punctaj P",
)


def export_publications_csv(
    filename: pathlib.Path,
    candidate_name: str,
    pubs: Sequence[Publication],
    *,
    position: Position = Position.Professor,
    encoding: str = "utf-8",
    dialect: str = "excel",
    overwrite: bool = False,
) -> None:
    if not overwrite and filename.exists():
        raise FileExistsError(filename)

    import csv

    candidate = make_candidate(candidate_name, pubs, position=position)

    with open(filename, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            PUBLICATION_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        for i, pub in enumerate(candidate.publications):
            writer.writerow(
                dict(
                    zip(
                        PUBLICATION_FIELD_NAMES,
                        [
                            str(i + 1),
                            pub.title,
                            filter_csv_format_authors(pub),
                            pub.journal.name,
                            filter_csv_format_volume(pub),
                            str(pub.year),
                            "N/A",
                            str(len(pub.authors)),
                            "N/A",
                            str(len(pub.cited_by)),
                            "N/A",
                            "N/A",
                        ],
                        strict=True,
                    )
                )
            )

    citesfile = filename.with_stem(f"{filename.stem}.confs")
    with open(citesfile, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            CONFERENCE_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        for i, pub in enumerate(candidate.conferences):
            writer.writerow(
                dict(
                    zip(
                        CONFERENCE_FIELD_NAMES,
                        [
                            str(i),
                            pub.title,
                            filter_csv_format_authors(pub),
                            pub.journal.name,
                            filter_csv_format_volume(pub),
                            str(pub.year),
                            "N/A",
                            str(len(pub.authors)),
                            "N/A",
                            "N/A",
                            str(len(pub.cited_by)),
                            "N/A",
                            "N/A",
                        ],
                        strict=True,
                    )
                )
            )

    confsfile = filename.with_stem(f"{filename.stem}.cites")
    with open(confsfile, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            CITATION_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        for i, pub in enumerate(candidate.publications):
            if not pub.cited_by:
                continue

            writer.writerow(
                dict(
                    zip(
                        CITATION_FIELD_NAMES,
                        [
                            str(i + 1),
                            pub.title,
                            filter_csv_format_authors(pub),
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        strict=True,
                    )
                )
            )

            for j, cited_by in enumerate(pub.cited_by):
                writer.writerow(
                    dict(
                        zip(
                            CITATION_FIELD_NAMES,
                            [
                                f"{i + 1}.{j + 1}",
                                cited_by.title,
                                filter_csv_format_authors(cited_by),
                                cited_by.journal.name,
                                filter_csv_format_volume(cited_by),
                                str(cited_by.year),
                                "N/A",
                                "N/A",
                            ],
                            strict=True,
                        )
                    )
                )


# }}}

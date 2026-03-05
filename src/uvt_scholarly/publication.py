# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from uvt_scholarly.identifiers import DOI, ISSN, ORCiD, ResearcherID

log = make_logger(__name__)

# NOTE: This stuff will mostly match the Web of Science and Scopus data models,
# since we are just importing data from there. For now, it pretends it's slightly
# independent..

# {{{ Author


@dataclass(frozen=True, slots=True)
class Author:
    first_name: str
    """First name of the author. This can contain multiple first names and initials,
    as necessary.
    """
    last_name: str
    """Last name of the author. This can contain additional parts as well, e.g.
    `von Neumann`.
    """

    affiliations: tuple[str, ...] = ()
    """A list of affiliations for the author. This is generally only meant for
    a particular publication, not a general list over time.
    """
    researcherid: ResearcherID | None = None
    """The [ResearcherID](https://en.wikipedia.org/wiki/ResearcherID) for the author."""
    orcid: ORCiD | None = None
    """The [ORCiD](https://orcid.org/) for the author."""


# }}}

# {{{ Journal


@enum.unique
class ScoreType(enum.Enum):
    """Supported types of Journal scores."""

    AIS = enum.auto()
    """Article Influence Score."""
    JIF = enum.auto()
    """Journal Impact Factor."""
    RIF = enum.auto()
    """Relative Impact Factor."""
    RIS = enum.auto()
    """Relative Influence Score."""


SCORE_FULL_NAME: dict[ScoreType, str] = {
    ScoreType.AIS: "Article Influence Score",
    ScoreType.JIF: "Journal Impact Factor",
    ScoreType.RIF: "Relative Impact Factor",
    ScoreType.RIS: "Relative Influence Score",
}
"""A mapping from journal scores to their full names."""


@dataclass(frozen=True, slots=True)
class Journal:
    """A basic description of a journal."""

    name: str
    """The name of the journal."""

    scores: Mapping[ScoreType, float] = field(default_factory=dict)
    """A mapping of known scores for this journal."""
    quartile: Mapping[ScoreType, str] = field(default_factory=dict)
    """A mapping of known quartiles for each score, as available."""

    def __str__(self) -> str:
        return self.name


# }}}


# {{{ Category


@dataclass(frozen=True, slots=True)
class Category:
    """A category for a publication."""

    name: str
    """The main name of the category, e.g. `Mathematics`."""
    field: str | None
    """A sub-category or sub-field in the main category, e.g. `Applied`."""

    def __str__(self) -> str:
        return f"{self.name}, {self.field}" if self.field else self.name

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"


# }}}

# {{{ Pages


@dataclass(frozen=True, slots=True)
class Pages:
    """Page range for a publication."""

    start: str
    """The starting page identifier. This is generally a numerical value, but
    more modern online-only journals can use different identifiers."""
    end: str | None
    """The ending page identifier. This can be missing for some journals."""
    count: int | None
    """A total page count. If all values are numeric, this should correspond to
    just `end - start + 1`.
    """

    def __str__(self) -> str:
        return f"{self.start}-{self.end}" if self.end else self.start


# }}}

# {{{ Publication


@enum.unique
class DocumentType(enum.Enum):
    """A enumeration of supported document types."""

    Article = enum.auto()
    """A standard journal article."""
    Book = enum.auto()
    """A standard book."""
    BookChapter = enum.auto()
    """A chapter from a book."""
    Dataset = enum.auto()
    """A published dataset."""
    Other = enum.auto()
    """An unknown or unsupported type of document."""
    ProceedingsPaper = enum.auto()
    """A published paper in conference proceedings."""
    Review = enum.auto()
    """A review paper."""
    Report = enum.auto()
    """A technical report."""


@dataclass(frozen=True, slots=True)
class CitedPublication:
    """A short publication metadata for cited references."""

    first_author: str
    """The last name of the first author."""
    journal: str
    """The (usually abbreviated) journal name."""
    year: int
    """The year of the publication."""
    doi: DOI
    """The Digital Object Identifier (DOI) for this publication."""


@dataclass(frozen=True, slots=True)
class Publication:
    authors: tuple[Author, ...]
    """A list of authors for the current publication."""
    title: str
    """The main title of the current publication."""
    journal: Journal
    """The journal in which it was published."""
    year: int
    """The year in which it was published."""
    volume: str
    """The volume in which it was published. This is usually a numerical value,
    but can also be written as Roman numerals or other identifiers.
    """
    issue: str
    """The issue in which it was published. This is usually a numerical value,
    but it can be some other identifier or even something like ``"Summer"`` for
    various periodicals.
    """
    pages: Pages
    """Page range in the issue."""
    doi: DOI | None
    """A Digital Object Identifier (DOI) for the publication."""

    issn: ISSN | None
    """An International Standard Serial Number (ISSN) for the Journal or publishing
    house that published this publication, if available.
    """
    eissn: ISSN | None
    """An electronic ISSN, if available."""

    dtype: DocumentType
    """A generic document type for the publication."""
    categories: tuple[Category, ...]
    """A list of categories this publication can be classified in. This generally
    depends heavily on the source of the metadata (e.g. Web of Science categories).
    """
    identifier: str
    """A unique identifier for the publication the repository from which it
    was obtained (e.g. a Web of Science Accession Number).
    """

    cited_by_count: int
    """A total number of citations for this publication. This value is generally
    exported from a repository and does not necessarily match [citations][].
    """
    cited_by: tuple[Publication, ...]
    """A list of publications that have cited this publication."""

    citations: dict[DOI, CitedPublication]
    """A list of publications cited by this publication."""


# }}}

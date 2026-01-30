# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cached_property

import httpx

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


# {{{ ResearcherID


@dataclass(frozen=True)
class ResearcherID:
    """A parsed `ResearcherID <https://en.wikipedia.org/wiki/ResearcherID>`__."""

    parts: tuple[str, str, str]
    """The three parts of the ResearcherID, which generally has the form
    ``X[XX]-NNNN-NNNN``, which an ASCII letter as the first part and two 4-digit
    numeric identifiers.
    """

    def __str__(self) -> str:
        return "-".join(self.parts)

    @staticmethod
    def from_string(rid: str) -> ResearcherID:
        """Convert some text into a :class:`ResearcherID` instance."""

        if "-" not in rid:
            raise ValueError(
                f"no dash in ResearcherID (format X[XX]-NNNN-NNNN): {rid!r}"
            )

        parts = [part.strip().upper() for part in rid.upper().split("-")]
        if len(parts) != 3:
            raise ValueError(
                f"incorrect parts in ResearcherID (format X[XX]-NNNN-NNNN): {rid!r}"
            )

        if not (len(parts[0]) >= 1 and len(parts[1]) == 4 and len(parts[2]) == 4):
            raise ValueError(
                f"incorrect part size in ResearcherID (format X[XX]-NNNN-NNNN): {rid!r}"
            )

        return ResearcherID((parts[0], parts[1], parts[2]))

    @property
    def year(self) -> int:
        """The year the ResearcherID was registered. This is only the last 4 digits
        of the identifier.
        """
        return int(self.parts[-1])

    @cached_property
    def is_valid(self) -> bool:
        """*True* if the :class:`ResearcherID` is valid.

        Note that there is no standardized format for the ResearcherID, so this
        validation should be taken with a grain of salt. It mainly checks that
        values found in the wild are considered valid.
        """

        if not (
            len(self.parts[0]) >= 1
            and len(self.parts[1]) == 4
            and len(self.parts[2]) == 4
        ):
            return False

        if not all("A" <= ch <= "Z" for ch in self.parts[0]):
            return False

        if not (self.parts[1].isdigit() and self.parts[2].isdigit()):
            return False

        from datetime import datetime

        # NOTE: the last part of the ResearcherID should represent the year. Given
        # that it started in 2008, we do not expect to see earlier values there.
        year = int(self.parts[2])
        return 2008 <= year < datetime.now().year + 1


# }}}

# {{{ ORCiD


@dataclass(frozen=True)
class ORCiD:
    """A parsed `ORCiD <https://en.wikipedia.org/wiki/ORCID>`__."""

    parts: tuple[str, str, str, str]
    """The four parts of the ORCiD, which generally has the form
    ``NNNN-NNNN-NNNN-NNNN``.
    """

    def __str__(self) -> str:
        return "-".join(self.parts)

    @staticmethod
    def from_string(orcid: str) -> ORCiD:
        """Convert some text into an :class:`ORCiD` instance."""

        if "-" not in orcid:
            raise ValueError(
                f"no dash in ORCiD (format NNNN-NNNN-NNNN-NNNN): {orcid!r}"
            )

        parts = [part.strip().upper() for part in orcid.split("-")]
        if len(parts) != 4:
            raise ValueError(
                f"incorrect parts in ORCiD (format NNNN-NNNN-NNNN-NNNN): {orcid!r}"
            )

        if any(len(part) != 4 for part in parts):
            raise ValueError(
                f"incorrect part sizes in ORCiD (format NNNN-NNNN-NNNN-NNNN): {orcid!r}"
            )

        return ORCiD((parts[0], parts[1], parts[2], parts[3]))

    @cached_property
    def is_valid(self) -> bool:
        """*True* if the :class:`ORCiD` is valid."""

        if any(len(part) != 4 for part in self.parts):
            return False

        if not (
            self.parts[0].isdigit()
            and self.parts[1].isdigit()
            and self.parts[2].isdigit()
            and self.parts[3][:-1].isdigit()
        ):
            return False

        check = self.parts[3][-1].upper()
        if not (check.isdigit() or check == "X"):
            return False

        total = 0
        digits = "".join(self.parts)
        for ch in digits[:-1]:
            total = 2 * (total + int(ch))

        remainder = total % 11
        result = (12 - remainder) % 11
        expected = "X" if result == 10 else str(result)

        return check == expected


# }}}

# {{{ Author


@dataclass(frozen=True)
class Author:
    first_name: str
    """First name of the author. This can contain multiple first names and initials,
    as necessary.
    """
    last_name: str
    """Last name of the author. This can contain additional parts as well, e.g.
    ``von Neumann``.
    """

    affiliations: tuple[str, ...] = ()
    """A list of affiliations for the author. This is generally only meant for
    a particular publication, not a general list over time.
    """
    researcherid: ResearcherID | None = None
    """The ResearcherID for the author."""
    orcid: ORCiD | None = None
    """The ORCiD for the author."""


# }}}

# {{{ Journal


@enum.unique
class Score(enum.Enum):
    """Supported types of Journal scores."""

    JournalImpactFactor = enum.auto()
    ArticleInfluenceScore = enum.auto()
    RelativeInfluenceScore = enum.auto()
    RelativeImpactFactor = enum.auto()


SCORE_TO_ACRONYM = {
    Score.JournalImpactFactor: "JIF",
    Score.ArticleInfluenceScore: "AIS",
    Score.RelativeInfluenceScore: "RIS",
    Score.RelativeImpactFactor: "RIF",
}
"""A mapping from journal scores to commonly used acronyms."""


@dataclass(frozen=True)
class Journal:
    """A basic description of a journal."""

    name: str
    """The name of the journal."""

    scores: Mapping[Score, float] = field(init=False, default_factory=dict)
    """A mapping of known scores for this journal."""
    quartile: Mapping[Score, str] = field(init=False, default_factory=dict)
    """A mapping of known quartiles for each score, as available."""


# }}}

# {{{ DOI

DOI_RESOLVER = "https://doi.org"


def _lowercase_ascii(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


@dataclass(frozen=True)
class DOI:
    """A parsed `Digital Object Identifier <https://en.wikipedia.org/wiki/Digital_object_identifier>__`."""

    namespace: str
    """The namespace for the identifier. This is usually ``10`` for scientific
    publications."""
    registrant: str
    """The registrant for this identifier. There is no official list of all
    registrants, but some information can be obtained, e.g., from Crossref by
    querying ``https://api.crossref.org/prefixes/10.1038``.
    """
    item: str
    """The unique identifier for this item."""

    def __str__(self) -> str:
        return f"{self.namespace}.{self.registrant}/{self.item}"

    def display(self) -> str:
        """A display string for the DOI (recommended by the DOI Foundation)."""
        return f"doi:{self}"

    @property
    def url(self) -> str:
        """A URL for the DOI using a supported resolver."""
        from urllib.parse import quote

        suffix = quote(self.item, safe="")
        return f"{DOI_RESOLVER}/{self.namespace}.{self.registrant}/{suffix}"

    def __hash__(self) -> int:
        return hash((self.namespace, self.registrant, _lowercase_ascii(self.item)))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        if self is other:
            return True

        # NOTE: according to the DOI Handook, Section 3.4.4, two DOIs are considered
        # equivalent is the codepoints are the same, except ASCII letters, which
        # are case-insensitive.
        return (
            self.namespace == other.namespace
            and self.registrant == other.registrant
            and _lowercase_ascii(self.item) == _lowercase_ascii(other.item)
        )

    @staticmethod
    def from_string(doi: str) -> DOI:
        """Convert some text into a :class:`DOI` instance."""

        if "/" not in doi:
            raise ValueError(f"DOI has a form 'prefix/suffix': {doi!r}")

        prefix, suffix = doi.split("/", maxsplit=1)
        if "." not in prefix:
            raise ValueError(f"DOI prefix must have a form '10.NNNN': {doi!r}")

        namespace, registrant = prefix.split(".")
        if not (namespace == "10" and len(registrant) == 4 and registrant.isdigit()):
            raise ValueError(f"DOI prefix must have a form '10.NNNN': {doi!r}")

        # NOTE: according to the DOI Handbook, ASCII letters are case-insensitive
        # in a DOI, so we just lowercase them to begin with.
        return DOI(namespace, registrant, _lowercase_ascii(suffix))

    @cached_property
    def is_valid(self) -> bool:
        """*True* if the DOI is valid.

        Note that this just checks the general format of the DOI, e.g. size,
        allowed characters, etc. The only official way to verify if a DOI is valid
        is to resolve it. This can be done using :meth:`resolve`, which effectively
        checks if :attr:`url` is redirects successfully.
        """

        if self.namespace != "10":
            return False

        if len(self.registrant) != 4 or not self.registrant.isdigit():
            return False

        if not self.item:
            return False

        for ch in self.item:
            if ch.isspace():
                return False

            # also reject ASCII control sequences
            if ord(ch) < 32 or ord(ch) == 127:
                return False

        # NOTE: this just validates the form of the DOI. To truly know if a DOI
        # is valid, we have to resolve it through doi.org or something.
        return True

    def resolve(self, client: httpx.Client | None = None) -> bool:
        """
        :arg client: a client used for the HTTP request. This function automatically
            creates a client if none is provided. However, if checking many DOIs
            at once, it is recommended to create a client, so that requests can be
            handled more efficiently.

        :returns: *True* if the current DOI redirects correctly.
        """
        # TODO: we should cache this result and just return it on the next call

        if not self.is_valid:
            return False

        try:
            if client:
                if not client.follow_redirects:
                    raise ValueError(
                        "'resolve' requires a client with follow_redirects=True"
                    )

                response = client.head(self.url)
            else:
                with httpx.Client(follow_redirects=True, timeout=5.0) as c:
                    response = c.head(self.url)

            return response.status_code == 200
        except httpx.HTTPError:
            return False


# }}}

# {{{ ISSN


@dataclass(frozen=True)
class ISSN:
    """A parsed `International Standard Serial Number <https://en.wikipedia.org/wiki/ISSN>`__."""

    parts: tuple[str, str]
    """The two parts of the ISSN, which generally has the form ``NNNN-NNNN``."""

    def __str__(self) -> str:
        return f"{self.parts[0]}-{self.parts[1]}"

    @staticmethod
    def from_string(issn: str) -> ISSN:
        """Convert some text into an :class:`ISSN` instance."""

        if "-" not in issn:
            raise ValueError(f"ISSN missing dash (expected NNNN-NNNC): {issn!r}")

        if len(issn) != 9:
            raise ValueError(f"invalid ISSN length (expected NNNN-NNNC): {issn!r}")

        part0, part1 = issn.split("-", maxsplit=1)
        if len(part0) != 4 or len(part1) != 4:
            raise ValueError(f"invalid ISSN part size (expected NNNN-NNNC): {issn!r}")

        # NOTE: we let the user check if this is a valid ISSN otherwise, since
        # they might want to just construct some for fun and games
        return ISSN((part0, part1))

    @cached_property
    def is_valid(self) -> bool:
        """*True* if the ISSN is valid."""

        issn = f"{self.parts[0]}{self.parts[1]}"
        if len(issn) != 8:
            return False

        # NOTE: verify the "check" digit in the ISSN:
        #   https://en.wikipedia.org/wiki/ISSN#Code_format

        total = 0
        for i in range(7):
            if not issn[i].isdigit():
                return False

            total += int(issn[i]) * (8 - i)

        check = 11 - (total % 11)
        if check == 11:
            expected = "0"
        elif check == 10:
            expected = "X"
        else:
            expected = str(check)

        return issn[-1] == expected


# }}}


# {{{ Category


@dataclass(frozen=True)
class Category:
    """A category for a publication."""

    name: str
    """The main name of the category, e.g. Mathematics."""
    field: str | None
    """A sub-category or sub-field in the main category."""

    def __str__(self) -> str:
        return f"{self.name}, {self.field}" if self.field else self.name


# }}}

# {{{ Pages


@dataclass(frozen=True)
class Pages:
    """Page range for a publication."""

    start: str
    """The starting page identifier. This is generally a numerical value, but
    more modern online-only journals can use different identifiers."""
    end: str | None
    """The ending page identifier. This can be missing for some journals."""
    count: int | None
    """A total page count. If all values are numeric, this should correspond to
    just ``end - start``.
    """

    def __str__(self) -> str:
        return f"{self.start}-{self.end}" if self.end else self.start


# }}}

# {{{ Publication


@enum.unique
class DocumentType(enum.Enum):
    """A enumeration of supported document types."""

    Article = enum.auto()
    Book = enum.auto()
    BookChapter = enum.auto()
    Dataset = enum.auto()
    Other = enum.auto()
    ProceedingsPaper = enum.auto()
    Review = enum.auto()
    Report = enum.auto()


@dataclass(frozen=True)
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
    doi: DOI
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
    """A unique identifier for the publication the the repository from which it
    was obtained (e.g. a Web of Science Accession Number).
    """

    citations: tuple[Publication, ...]
    """A list of publications that have cited this publication."""


# }}}

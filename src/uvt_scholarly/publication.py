# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field

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
        """Convert some text into :class:`ResearcherID` instance."""

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

    @property
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
    parts: tuple[str, str, str, str]

    def __str__(self) -> str:
        return "-".join(self.parts)

    @staticmethod
    def from_string(orcid: str) -> ORCiD:
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

    @property
    def is_valid(self) -> bool:
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
    last_name: str

    affiliations: tuple[str, ...] = ()
    researcherid: ResearcherID | None = None
    orcid: ORCiD | None = None


# }}}

# {{{ Journal


@enum.unique
class Score(enum.Enum):
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


@dataclass(frozen=True)
class Journal:
    name: str
    scores: Mapping[Score, float] = field(init=False, default_factory=dict)
    quartile: Mapping[Score, str] = field(init=False, default_factory=dict)


# }}}

# {{{ DOI

DOI_RESOLVER = "https://doi.org"


def _lowercase_ascii(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


@dataclass(frozen=True)
class DOI:
    namespace: str
    registrant: str
    item: str

    def __str__(self) -> str:
        return f"{self.namespace}.{self.registrant}/{self.item}"

    def display(self) -> str:
        return f"doi:{self}"

    @property
    def url(self) -> str:
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

    @property
    def is_valid(self) -> bool:
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
    parts: tuple[str, str]

    def __str__(self) -> str:
        return f"{self.parts[0]}-{self.parts[1]}"

    @staticmethod
    def from_string(issn: str) -> ISSN:
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

    @property
    def is_valid(self) -> bool:
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
    name: str
    field: str | None

    def __str__(self) -> str:
        return f"{self.name}, {self.field}" if self.field else self.name


# }}}

# {{{ Pages


@dataclass(frozen=True)
class Pages:
    start: str
    end: str | None
    count: int | None

    def __str__(self) -> str:
        return f"{self.start}-{self.end}" if self.end else self.start


# }}}

# {{{ Publication


@enum.unique
class DocumentType(enum.Enum):
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

    issn: ISSN
    """An International Standard Serial Number (ISSN) for the Journal or publishing
    house that published this publication.
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

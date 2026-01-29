# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass

import httpx

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


# {{{ Author


@dataclass(frozen=True)
class Author:
    first_name: str
    last_name: str

    affiliations: tuple[str, ...] = ()
    researcherid: str | None = None
    orcid: str | None = None


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
    scores: Mapping[Score, float]
    quartile: Mapping[Score, str]


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

# {{{ Publication


@dataclass(frozen=True)
class Publication:
    authors: tuple[Author, ...]
    title: str
    journal: Journal
    year: int
    volume: str
    issue: str
    dtype: str
    doi: DOI
    issn: ISSN
    eissn: ISSN
    categories: tuple[str, ...]

    citations: tuple[Publication, ...]


# }}}

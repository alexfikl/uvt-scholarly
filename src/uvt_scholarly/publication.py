# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


@enum.unique
class Score(enum.Enum):
    JournalImpactFactor = enum.auto()
    ArticleInfluenceScore = enum.auto()
    RelativeInfluenceScore = enum.auto()
    RelativeImpactFactor = enum.auto()


@dataclass(frozen=True)
class Author:
    first_name: str
    last_name: str
    affiliations: tuple[str, ...]


@dataclass(frozen=True)
class Journal:
    name: str
    scores: dict[Score, float]
    quartile: dict[Score, str]


@dataclass(frozen=True)
class DOI:
    namespace: str
    registrant: str
    item: str

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

        return DOI(namespace, registrant, suffix)

    def __str__(self) -> str:
        return f"{self.namespace}.{self.registrant}/{self.item}"


@dataclass(frozen=True)
class ISSN:
    parts: tuple[str, str]

    def __str__(self) -> str:
        return f"{self.parts[0]}-{self.parts[1]}"

    @staticmethod
    def from_string(issn: str) -> ISSN:
        if "-" not in issn:
            raise ValueError(f"ISSN has a form NNNN-NNNC: {issn!r}")

        if len(issn) != 9:
            raise ValueError(f"ISSN has a form NNNN-NNNC (length 9): {issn!r}")

        # NOTE: we let the user check if this is a valid ISSN otherwise, since
        # they might want to just construct some for fun and games
        part0, part1 = issn.split("-")
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


@dataclass(frozen=True)
class Publication:
    authors: tuple[Author, ...]
    title: str
    journal: Journal
    year: int
    volume: str
    number: str
    dtype: str
    doi: DOI
    issn: ISSN
    eissn: ISSN
    categories: tuple[str, ...]

    citations: tuple[Publication, ...]

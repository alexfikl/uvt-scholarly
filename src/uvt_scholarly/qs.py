# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

log = make_logger(__name__)


# {{{ University


@enum.unique
class UniversityRanking(enum.Enum):
    """Ranking bucket of a university."""

    Top20 = enum.auto()
    Top100 = enum.auto()
    Top200 = enum.auto()
    Top500 = enum.auto()
    Above500 = enum.auto()


UNIVERSITY_RANKING_ID = {
    "top20": UniversityRanking.Top20,
    "top100": UniversityRanking.Top100,
    "top200": UniversityRanking.Top200,
    "top500": UniversityRanking.Top500,
    "above500": UniversityRanking.Above500,
}


@enum.unique
class UniversityStatus(enum.Enum):
    Public = enum.auto()
    Private = enum.auto()
    Profit = enum.auto()
    Unknown = enum.auto()


@dataclass(frozen=True, slots=True)
class University:
    name: str
    rank: int
    score: float
    region: str
    status: UniversityStatus

    @property
    def ranking(self) -> UniversityRanking:
        if self.rank <= 20:
            return UniversityRanking.Top20
        elif self.rank < 100:
            return UniversityRanking.Top100
        elif self.rank < 200:
            return UniversityRanking.Top200
        elif self.rank < 500:
            return UniversityRanking.Top500
        else:
            return UniversityRanking.Above500


# }}}


# {{{ parse_qs_ranking


def parse_qs_ranking(filename: pathlib.Path) -> Sequence[University]:
    import openpyxl

    wb = openpyxl.load_workbook(filename, read_only=True)
    if wb is None:
        raise ValueError(f"could not load workbook from file: '{filename}'")

    sheetname = "Sheet1"  # spell: disable
    if sheetname not in wb.sheetnames:
        raise ValueError(f"expected a sheet called '{sheetname}' in file: '{filename}'")
    ws = wb[sheetname]

    result = []
    for row in ws.iter_rows(min_row=4, max_col=29, values_only=True):
        if not row[0]:
            break

        # NOTE: the rank is only accurate for the first 500-ish university.
        # For the rest, they have things like `701-710` or `1401+`. We keep a
        # number for comparison.
        rank = row[1]
        if isinstance(rank, str):
            if "-" in rank:
                rank = rank.split("-")[0]
            if "+" in rank:
                rank = rank.replace("+", "")

        # NOTE: lower ranking universities no longer have an overall score.
        try:
            score = float(row[28])
        except ValueError:
            score = 0.0

        text = row[9]
        if text is None:
            status = UniversityStatus.Unknown
        else:
            text = text.strip().lower()
            if text == "public":
                status = UniversityStatus.Public
            elif text == "private not for profit":
                status = UniversityStatus.Private
            elif text == "private for profit":
                status = UniversityStatus.Profit
            else:
                raise ValueError(f"unknown university status: {text}")

        result.append(
            University(
                name=row[3].strip(),
                rank=int(rank),
                score=score,
                region=row[5].strip(),
                status=status,
            )
        )

        print(result[-1].name, result[-1].score)

    return tuple(result)


# }}}

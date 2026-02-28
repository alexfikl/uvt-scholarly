# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from uvt_scholarly.export.common import POSITION_NAME, Position
from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from uvt_scholarly.publication import Publication

log = make_logger(__name__)

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
    score_b: float
    score_c: float
    score_d: float
    score_total: float
    hirsch: dict[str, int]


# }}}

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass

from uvt_scholarly.export.common import POSITION_NAME, Position
from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


# {{{ criteria


@enum.unique
class Category(enum.IntEnum):
    S = 4
    A = 3
    B = 2
    C = 1
    D = 0


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


# }}}

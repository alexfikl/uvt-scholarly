# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


# {{{ position


@enum.unique
class Position(enum.Enum):
    Professor = enum.auto()
    AssociateProfessor = enum.auto()
    AssistantProfessor = enum.auto()
    Assistant = enum.auto()

    SeniorResearcher = enum.auto()
    Researcher = enum.auto()
    JuniorResearcher = enum.auto()


POSITION_NAME = {
    # academic
    Position.Professor: "Profesor Universitar",  # spell: disable
    Position.AssociateProfessor: "Conferențiar",
    Position.AssistantProfessor: "Lector",
    Position.Assistant: "Asistent Universitar",
    # research
    Position.SeniorResearcher: "Cercetător Științific I",
    Position.Researcher: "Cercetător Științific II",
    Position.JuniorResearcher: "Cercetător Științific III",
}

POSITION_SHORT_NAME = {
    Position.Professor: "Prof. Dr.",
    Position.AssociateProfessor: "Conf. Dr.",
    Position.AssistantProfessor: "Lect. Dr.",
    Position.Assistant: "Ass.",
    # research
    Position.SeniorResearcher: "C.S. I",
    Position.Researcher: "C.S. II",
    Position.JuniorResearcher: "C.S. III",
}

ID_TO_POSITION = {
    "prof": Position.Professor,
    "conf": Position.AssociateProfessor,
    "lect": Position.AssistantProfessor,
    "assi": Position.Assistant,
    "cs1": Position.SeniorResearcher,
    "cs2": Position.Researcher,
    "cs3": Position.JuniorResearcher,
}

# }}}

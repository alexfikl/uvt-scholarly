# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    import pathlib

log = make_logger(__name__)

CORE_COLLECTION_NAMES = {
    "ICORE2026",
    "CORE2023",
    "CORE2021",
    "CORE2020",
}

CORE_COLLECTION_URL = "https://portal.core.edu.au/conf-ranks/?search=&by=all&source={source}&sort=atitle&page=1&do=Export"


EXTRA_CORE_CLASSIFICATIONS = {
    "CSE": "Computer Systems Engineering",
}


def get_url_for_collection(collection: str) -> str:
    if collection not in CORE_COLLECTION_NAMES:
        raise ValueError(f"unknown CORE collection: '{collection}'")

    return CORE_COLLECTION_URL.format(source=collection)


# {{{ rank

# NOTE: https://drive.google.com/file/d/1DQixeK53tlq_jh6IspIHroiwu1pmM6-y/edit


@enum.unique
class Rank(enum.Enum):
    S = enum.auto()
    """The ``A*`` ranking in the CORE collection."""
    A = enum.auto()
    """The ``A`` ranking in the CORE collection."""
    B = enum.auto()
    """The ``B`` ranking in the CORE collection."""
    C = enum.auto()
    """The ``C`` ranking in the CORE collection."""
    D = enum.auto()
    """The ``D`` ranking in the CORE collection."""
    Unranked = enum.auto()
    """An unranked conference in the CORE collection."""

    National = enum.auto()
    """A national conference (unranked) in the CORE collection."""
    Published = enum.auto()
    """A conference with proceedings published in a journal."""
    Multiconference = enum.auto()
    """An umbrella event with multiple conferences."""


RANK_TO_NAME = {
    Rank.S: "A*",
    Rank.A: "A",
    Rank.B: "B",
    Rank.C: "C",
    Rank.D: "D",
    Rank.Unranked: "Unranked",
    # Non-ranking values
    Rank.National: "National",
    Rank.Published: "Published",
    Rank.Multiconference: "Multiconference",
}
"""A mapping from the :class:`Rank` enumeration to an appropriate display string."""

CORE_NAME_TO_RANK = {name: rank for rank, name in RANK_TO_NAME.items()}
"""A mapping from the CORE rank to the :class:`Rank` enumeration."""

# }}}

# {{{ conference


@dataclass(frozen=True, slots=True)
class Conference:
    name: str
    """The full name of the conference, as it appears in the CORE collection."""
    acronym: str
    """The acronym of the conference, as it appears in the CORE collection."""
    source: str
    """The name of the collection the conference classification is from."""
    rank: Rank
    """The rank of the journal in the CORE collection."""
    primary_fields: tuple[str, ...]
    """The code for the primary Field of Research of this conference. Use
    :func:`get_primary_field_name` to get a display name for this code.
    """

    identifier: int
    """A unique identifier of the conference in the collection."""


def get_primary_field_name(code: str) -> str:
    """A display name for the primary field code of a conference."""
    from uvt_scholarly.anzsrc import ANZSRC_CLASSIFICATIONS

    if (result := ANZSRC_CLASSIFICATIONS.get(code)) is not None:
        return result

    if (result := EXTRA_CORE_CLASSIFICATIONS.get(code)) is not None:
        return result

    raise ValueError(f"unknown field of research for classification: {code!r}")


# }}}

# {{{ parse_core_csv

CORE_FIELD_NAMES = (
    "Identifier",
    "Title",
    "Acronym",
    "Source",
    "Rank",
    # "Note",
    "DBLP",
    "Primary Field",
    # NOTE: it seems like in the exported CSV, they store additional
    # fields instead of the comments / average rating in the last columns
    "Field2",
    "Field3",
)


def parse_core_csv(
    filename: pathlib.Path,
    *,
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> tuple[Conference, ...]:
    import csv

    with open(filename, encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter, fieldnames=CORE_FIELD_NAMES)

        from uvt_scholarly.utils import ParsingError

        result = []
        for row in reader:
            acronym = row["Acronym"].strip()
            source = row["Source"].strip().upper()
            if source not in CORE_COLLECTION_NAMES:
                raise ParsingError(
                    f"conference '{acronym}' in an unknown collection: {source!r}"
                )

            rank = row["Rank"].replace("-", "")
            if rank not in CORE_NAME_TO_RANK:
                lank = rank.lower()
                if lank.startswith("unranked"):
                    rank = "Unranked"
                elif lank.startswith("national") or lank.startswith("regional"):
                    rank = "National"
                elif lank.startswith("journal"):
                    rank = "Published"
                elif lank.startswith("australasian"):
                    # NOTE: from the description in the documentation, these
                    # tags have a rank sometimes, but otherwise they're in the
                    # "National" category.
                    if " " in lank:
                        _, rank = rank.split(" ", maxsplit=1)
                    else:
                        rank = "National"
                elif lank in {"tbr", "new"}:  # "to be ranked"
                    rank = "Unranked"
                elif "review" in lank:
                    # NOTE: some conferences seem to have the rank "B (needs review)"
                    # so we just try and be optimistic and remove the review
                    rank, _ = rank.split(" ", maxsplit=1)
                else:
                    raise ParsingError(
                        f"conference '{acronym}' has an unknown rank: {rank!r}"
                    )

            primary_fields: list[str] = [
                str(field)
                for field in [row["Primary Field"], row["Field2"], row["Field3"]]
                if field
            ]

            conf = Conference(
                name=row["Title"].strip(),
                acronym=acronym,
                source=source,
                rank=CORE_NAME_TO_RANK[rank],
                primary_fields=tuple(primary_fields),
                identifier=int(row["Identifier"]),
            )

            result.append(conf)

    return tuple(result)


# }}}

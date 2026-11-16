# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

log = make_logger(__name__)

# {{{ Grant


@dataclass(frozen=True, slots=True)
class Grant:
    """A grant that an author was part of."""

    name: str
    """The full name of the grant (this can contain an acronym)."""
    identifier: str
    """A unique identifier for the grant that can be used to locate it in the
    funder's database.
    """
    funder: str
    """The full name of the funder for this grant."""
    budget: str | None
    """The approximate available budget for the grant."""
    period: tuple[int, int]
    """The period that the author was part of this grant."""
    position: str
    """The position of the author in the grant."""
    url: str | None
    """A URL for the project or a link to the funder's page for this grant."""


# }}}


# {{{ read_grants


def read_grants(filename: pathlib.Path) -> Sequence[Grant]:
    if not filename.exists():
        raise FileNotFoundError(filename)

    import tomllib

    with open(filename, "rb") as fp:
        data = tomllib.load(fp)

    if "grants" not in data:
        raise KeyError(f"key 'grants' not found in file: {filename}")

    def parse_period(period: Sequence[int]) -> tuple[int, int]:
        if not isinstance(period, list) or len(period) != 2:
            raise KeyError(f"'period' is not a two-tuple: {period!r}")

        return int(period[0]), int(period[1])

    grants = []
    for i, d in enumerate(data["grants"]):
        if "name" not in d:
            log.error("Grant '%d' has no name. Skipping...", i)
            continue

        name = d["name"].strip()
        try:
            grants.append(
                Grant(
                    name=name,
                    identifier=d["identifier"].strip(),
                    funder=d["funder"].strip(),
                    budget=budget.strip() if (budget := d.get("budget")) else None,
                    position=d["position"].strip(),
                    period=parse_period(d["period"]),
                    url=url.strip() if (url := d.get("url")) else None,
                )
            )
        except KeyError as exc:
            log.error("Failed to read grant %d: '%s'.", i, name, exc_info=exc)
            continue

    return tuple(grants)


# }}}

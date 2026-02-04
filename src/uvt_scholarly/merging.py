# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

    from uvt_scholarly.publication import Publication

log = make_logger(__name__)


# {{{ add_cited_by


def add_cited_by(
    pubs: Sequence[Publication],
    citations: Sequence[Publication],
) -> tuple[Publication, ...]:
    raise NotImplementedError


# }}}


# {{{ add_scores


def add_scores(
    pubs: Sequence[Publication],
    dbfile: pathlib.Path,
    *,
    scores: set[str] | None = None,
) -> tuple[Publication, ...]:
    raise NotImplementedError


# }}}

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import Publication, Score

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence


log = make_logger(__name__)


# {{{ add_cited_by


def add_cited_by(
    pubs: Sequence[Publication],
    citations: Sequence[Publication],
) -> tuple[Publication, ...]:
    raise NotImplementedError


# }}}


# {{{ add_scores


def _add_ris_scores(
    pubs: Sequence[Publication],
    dbfile: pathlib.Path,
    *,
    past: int = 5,
) -> tuple[Publication, ...]:
    from uvt_scholarly.uefiscdi.ris import DB

    result = []

    with DB(dbfile) as db:
        for pub in pubs:
            if Score.RIS in pub.journal.scores:
                continue

            issn = pub.issn or pub.eissn
            assert issn is not None

            score = db.max_score_by_issn(issn, past=past)
            if score is not None:
                scores = {**pub.journal.scores, Score.RIS: score}
                new_pub = replace(pub, journal=replace(pub.journal, scores=scores))
            else:
                log.warning(
                    "Cannot find RIS score for journal '%s' with ISSN '%s'.",
                    pub.journal.name,
                    issn,
                )

                new_pub = replace(pub)

            result.append(new_pub)

    return tuple(result)


def _add_rif_scores(
    pubs: Sequence[Publication],
    dbfile: pathlib.Path,
    *,
    past: int = 5,
) -> tuple[Publication, ...]:
    from uvt_scholarly.uefiscdi.rif import DB

    result = []

    with DB(dbfile) as db:
        for pub in pubs:
            if Score.RIF in pub.journal.scores:
                continue

            issn = pub.issn or pub.eissn
            assert issn is not None

            score = db.max_score_by_issn(issn, past=past)
            if score is not None:
                scores = {**pub.journal.scores, Score.RIF: score}
                new_pub = replace(pub, journal=replace(pub.journal, scores=scores))
            else:
                new_pub = replace(pub)

            result.append(new_pub)

    return tuple(result)


def add_scores(
    pubs: tuple[Publication, ...],
    dbfile: pathlib.Path,
    *,
    past: int = 5,
    scores: set[Score] | None = None,
) -> tuple[Publication, ...]:
    if not dbfile.exists():
        raise FileNotFoundError(dbfile)

    if scores is None:
        return pubs

    if Score.RIS in scores:
        pubs = _add_ris_scores(pubs, dbfile, past=past)

    if Score.RIF in scores:
        pubs = _add_rif_scores(pubs, dbfile, past=past)

    return pubs


# }}}

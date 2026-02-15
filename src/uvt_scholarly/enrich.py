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
    """Fill out the *cited_by* entry of a
    [Publication][uvt_scholarly.publication.Publication].

    This function matches the given *citations* to their respective *pubs*
    based on the DOI. The *citations* must have the
    [Publication.citations][uvt_scholarly.publication.Publication.citations]
    field filled in (e.g. by passing in *include_citations* to
    [read_from_csv][uvt_scholarly.wos.read_from_csv]).

    Publications in *pubs* that do not have a DOI are ignored and will not be
    returned.
    """
    doi_to_pub = {pub.doi: pub for pub in pubs if pub.doi is not None}

    # FIXME: the citations are no longer needed after this. remove them?
    for cite in citations:
        for doi in cite.citations:
            if (pub := doi_to_pub.get(doi)) is not None:
                doi_to_pub[doi] = replace(pub, cited_by=(*pub.cited_by, cite))

    return tuple(pub for pub in doi_to_pub.values())


# }}}


# {{{ add_scores


def add_scores(
    pubs: tuple[Publication, ...],
    dbfile: pathlib.Path,
    *,
    past: int = 5,
    scores: set[Score] | None = None,
) -> tuple[Publication, ...]:
    """Fill in the scores for each publication.

    Publications that do not have known scores in the database are left as is.
    The score added to each publication will be the maximum over the past *past*
    years. This function cannot add just the score from a specific year.

    Parameters:
        past: The past number of years over which the score is taken.
        scores: A list of scores to add. If left empty, no scores are added and the
            publication list is returned as is.
    """
    if not dbfile.exists():
        raise FileNotFoundError(dbfile)

    if scores is None:
        return pubs

    if isinstance(scores, Score):
        scores = {scores}

    for score in scores:
        if score == Score.RIS:
            from uvt_scholarly.uefiscdi.ris import (
                RelativeInfluenceScoreDatabase as Database,
            )
        elif score == Score.RIF:
            from uvt_scholarly.uefiscdi.rif import (
                RelativeImpactFactorDatabase as Database,
            )
        elif score == Score.AIS:
            from uvt_scholarly.uefiscdi.ais import (
                ArticleInfluenceScoreDatabase as Database,
            )
        else:
            raise ValueError(f"unsupported score type: {score}")

        with Database(dbfile) as db:
            result = []
            for pub in pubs:
                if score in pub.journal.scores:
                    result.append(pub)
                    continue

                issn = pub.issn or pub.eissn
                if issn is None:
                    log.error(
                        "Publication has no ISSN: '%s'.",
                        pub.doi if pub.doi else pub.title,
                    )
                    result.append(pub)
                    continue

                value = db.max_score_by_issn(issn, past=past)
                if value is not None:
                    new_scores = {**pub.journal.scores, score: value}
                    new_pub = replace(
                        pub, journal=replace(pub.journal, scores=new_scores)
                    )
                else:
                    log.warning(
                        "Cannot find %s score for journal '%s' with ISSN '%s'.",
                        score.name,
                        pub.journal.name,
                        issn,
                    )

                    new_pub = replace(pub)

                result.append(new_pub)

    return tuple(result)


# }}}

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
DATADIR = pathlib.Path(__file__).parent / "data"
TMPDIR = pathlib.Path(tempfile.gettempdir())


# {{{ test_add_cited_by


def test_add_cited_by() -> None:
    from uvt_scholarly.wos import read_from_csv

    publications = read_from_csv(DATADIR / "savedrecs.txt")
    citations = read_from_csv(
        DATADIR / "savedrecs_cited_by.txt", include_citations=True
    )

    from uvt_scholarly.enrich import add_cited_by

    pubs = add_cited_by(publications, citations)
    assert len(pubs) == len(publications)

    for pub in pubs:
        assert pub.cited_by_count == len(pub.cited_by)


# }}}


# {{{ test_add_scores


def test_add_scores() -> None:
    from uvt_scholarly.uefiscdi.ris import store_relative_influence_score

    year = 2025
    filename = TMPDIR / f"uvt-scholarly-test-ris-{year}.sqlite"
    if filename.exists():
        filename.unlink()

    store_relative_influence_score(filename, years={2025})

    from uvt_scholarly.wos import read_from_csv

    publications = read_from_csv(DATADIR / "savedrecs.txt")

    from uvt_scholarly.enrich import add_scores
    from uvt_scholarly.publication import DocumentType, Score

    publications = add_scores(publications, filename, scores={Score.RIS})

    for pub in publications:
        if pub.dtype != DocumentType.Article:
            continue

        assert Score.RIS in pub.journal.scores
        log.info("%-40s Score %.3f", pub.journal.name, pub.journal.scores[Score.RIS])


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import pytest

from uvt_scholarly.logging import make_logger
from uvt_scholarly.uefiscdi import UEFISCDI_DATABASE_URL, download_file
from uvt_scholarly.utils import block_timer

log = make_logger(__name__)
DATADIR = pathlib.Path(__file__).parent / "data"
TMPDIR = pathlib.Path(tempfile.gettempdir())

# {{{ test_parse_relative_influence_score

# NOTE: extracted from the Excel files by going to the last row.
# NOTE: some duplicates were removed as well, so it's not exactly the same.
EXPECTED_RIS_ENTRIES_PER_YEAR = {
    2020: 11484,
    2021: 12203,
    2022: 13656,
    2023: 13651,
    2024: 21846,
    2025: 22247,
}


@pytest.mark.parametrize("year", [2020, 2021, 2022, 2023, 2024, 2025])
def test_parse_relative_influence_score(year: int) -> None:
    from uvt_scholarly.publication import Score
    from uvt_scholarly.uefiscdi.ris import parse_relative_influence_score

    url = UEFISCDI_DATABASE_URL[year][Score.RIS]
    filename = TMPDIR / f"uvt-scholarly-test-ris-{year}.xlsx"

    with block_timer(f"download-ris-{year}"):
        download_file(url, filename)

    with block_timer(f"parse-ris-{year}"):
        scores = parse_relative_influence_score(filename, year)

    nscores = len(scores)
    assert nscores == EXPECTED_RIS_ENTRIES_PER_YEAR[year]


def test_ris_database() -> None:
    from uvt_scholarly.publication import Score

    year = 2025
    url = UEFISCDI_DATABASE_URL[year][Score.RIS]

    filename = TMPDIR / f"uvt-scholarly-test-ris-{year}.xlsx"
    download_file(url, filename)

    from uvt_scholarly.uefiscdi.ris import DB, parse_relative_influence_score

    dbfile = TMPDIR / f"uvt-scholarly-test-ris-{year}.sqlite"
    with DB(dbfile) as db:
        scores = parse_relative_influence_score(filename, year)
        db.insert(year, scores)

    with DB(dbfile) as db:
        search_issn = "2054-4251"
        search_result = None

        for score in scores:
            if search_issn in {score.issns, score.eissns}:
                search_result = score
                break

        assert search_result is not None
        log.info(
            "Found by iteration: '%s' ISSN '%s'.",
            search_result.journal,
            search_result.issn,
        )

        db_result = db.find_by_issn(search_issn)
        assert search_result == db_result

        # NOTE scores seem to have 3-4 digits max, but they're floating point
        # numbers, so we compare them with abs for safety.
        db_score = db.max_score_by_issn(search_issn)
        assert db_score is not None
        assert abs(db_score - search_result.score) < 1.0e-14

        # NOTE: it's hard to find an unused ISSN that is also valid
        db_result = db.find_by_issn("1234-5679")
        assert db_result is None

        score = db.max_score_by_issn("1234-5679")
        assert score is None

        with pytest.raises(ValueError, match="valid ISSN"):
            db_result = db.find_by_issn("1234-567X")

    # NOTE: we unlink the file so that the test can run again next time. Otherwise
    # it would crash when trying to add duplicate entries to the existing database
    dbfile.unlink()


# }}}


# {{{ test_parse_relative_impact_factor

EXPECTED_RIF_ENTRIES_PER_YEAR = {
    2020: 12144,
    2021: 12276,
    2022: 12464,
    2023: 13651,
    2024: 21846,
    2025: 22247,
}


@pytest.mark.parametrize("year", [2020, 2021, 2022, 2023, 2024, 2025])
def test_parse_relative_impact_factor(year: int) -> None:
    from uvt_scholarly.publication import Score
    from uvt_scholarly.uefiscdi.rif import parse_relative_impact_factor

    url = UEFISCDI_DATABASE_URL[year][Score.RIF]
    filename = TMPDIR / f"uvt-scholarly-test-rif-{year}.xlsx"

    with block_timer(f"download-rif-{year}"):
        download_file(url, filename)

    with block_timer(f"parse-rif-{year}"):
        scores = parse_relative_impact_factor(filename, year)

    nscores = len(scores)
    assert nscores == EXPECTED_RIF_ENTRIES_PER_YEAR[year]


# }}}

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import pytest

from uvt_scholarly.logging import make_logger
from uvt_scholarly.utils import block_timer

log = make_logger(__name__)
DATADIR = pathlib.Path(__file__).parent / "data"
TMPDIR = pathlib.Path(tempfile.gettempdir())

# {{{ test_parse_relative_influence_score

# NOTE: extracted from the Excel files by going to the last row
EXPECTED_ENTRIES_PER_YEAR = {
    2025: 22249,
    2024: 21848,
    2023: 13651,
    2022: 13658,
    2021: 12205,
}


@pytest.mark.parametrize("year", [2021, 2022, 2023, 2024, 2025])
def test_parse_relative_influence_score(year: int) -> None:
    from uvt_scholarly.uefiscdi import (
        UEFISCDI_DATABASE_URL,
        Score,
        download_file,
        parse_relative_influence_score,
    )

    url = UEFISCDI_DATABASE_URL[year][Score.RIS]
    filename = TMPDIR / f"uvt-scholarly-test-ris-{year}.xlsx"

    with block_timer(f"download-ris-{year}"):
        download_file(url, filename)

    with block_timer(f"parse-ris-{year}"):
        scores = parse_relative_influence_score(filename, year)

    nscores = len(scores)
    assert nscores == EXPECTED_ENTRIES_PER_YEAR[year]


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

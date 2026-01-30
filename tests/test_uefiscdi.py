# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
DATADIR = pathlib.Path(__file__).parent / "data"


# {{{ test_parse_relative_influence_score


@pytest.mark.parametrize("year", [2024])
def test_parse_relative_influence_score(year: int) -> None:
    from uvt_scholarly.uefiscdi import (
        UEFISCDI_DATABASE_URL,
        Score,
        download_file,
        parse_relative_influence_score,
    )

    url = UEFISCDI_DATABASE_URL[year][Score.RIS]
    with tempfile.NamedTemporaryFile(prefix="uvt-scholarly-test-", suffix=".xlsx") as f:
        filename = pathlib.Path(f.name)

        download_file(url, filename)
        scores = parse_relative_influence_score(filename, year)
        print(scores[0])
        assert scores


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

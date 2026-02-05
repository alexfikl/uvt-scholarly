# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
TMPDIR = pathlib.Path(tempfile.gettempdir())


# {{{ test_parse_core_csv

EXPECTED_CORE_CONFERENCES_PER_COLLECTION = {
    "ICORE2026": 987,
    "CORE2023": 956,
    "CORE2021": 955,
    "CORE2020": 882,
}


@pytest.mark.parametrize(
    "collection", ["ICORE2026", "CORE2023", "CORE2021", "CORE2020"]
)
def test_parse_core_csv(collection: str) -> None:
    from uvt_scholarly.core import get_url_for_collection, parse_core_csv
    from uvt_scholarly.utils import download_file

    year = int(collection[-4:])
    filename = TMPDIR / f"uvt-scholarly-test-core-{year}.xlsx"
    download_file(get_url_for_collection(collection), filename)

    conferences = parse_core_csv(filename)
    assert len(conferences) == EXPECTED_CORE_CONFERENCES_PER_COLLECTION[collection]


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

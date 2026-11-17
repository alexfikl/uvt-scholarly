# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import httpx2
import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
TMPDIR = pathlib.Path(tempfile.gettempdir())


# {{{ test_parse_sense_classification


@pytest.mark.xfail(raises=httpx2.ReadTimeout)
def test_parse_sense_classification() -> None:
    pytest.importorskip("openpyxl")

    from uvt_scholarly.sense import SENSE_URL, parse_sense_classification
    from uvt_scholarly.utils import download_file

    filename = TMPDIR / "uvt-scholarly-test-sense.xlsx"
    download_file(SENSE_URL, filename)
    result = parse_sense_classification(filename)

    assert len(result) == 1421


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

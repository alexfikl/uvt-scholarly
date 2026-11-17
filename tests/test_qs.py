# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import pathlib
import tempfile

import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
TMPDIR = pathlib.Path(tempfile.gettempdir())


# {{{ test_parse_qs_ranking


def test_parse_qs_ranking() -> None:
    pytest.importorskip("openpyxl")

    from uvt_scholarly.qs import parse_qs_ranking

    filename = os.environ.get("UVT_SCHOLARLY_QS_XLSX")
    if filename is None:
        pytest.skip("Test needs 'UVT_SCHOLARLY_QS_XLSX' for QS rankings")

    filename = pathlib.Path(filename)
    assert filename.exists()

    result = parse_qs_ranking(filename)
    assert len(result) == 1504


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import httpx
import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
TMPDIR = pathlib.Path(tempfile.gettempdir())


# {{{ test_parse_research_classification


@pytest.mark.xfail(raises=httpx.ReadTimeout)
def test_parse_research_classification() -> None:
    pytest.importorskip("openpyxl")

    from uvt_scholarly.anzsrc import ANZSRC_FOR_URL, parse_research_classification
    from uvt_scholarly.utils import download_file

    filename = TMPDIR / "uvt-scholarly-test-anzsrc.xlsx"
    download_file(ANZSRC_FOR_URL, filename)
    cls = parse_research_classification(filename)

    # TODO: what to check in here?
    assert 30 in cls
    assert cls[30] == "Agricultural, Veterinary and Food Sciences"

    # NOTE: this is here to easily generate the ANZSRC_CLASSIFICATIONS map
    # for code, name in cls.items():
    #     print(f'{code}: "{name}",')


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

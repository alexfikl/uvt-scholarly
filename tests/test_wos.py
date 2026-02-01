# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib

import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
DATADIR = pathlib.Path(__file__).parent / "data"


# {{{ test_read_from_csv


def test_read_from_csv() -> None:
    from uvt_scholarly.wos import read_from_csv

    publications = read_from_csv(DATADIR / "savedrecs.txt")
    assert publications

    for pub in publications:
        log.info("%s", pub)
        assert not pub.citations


# }}}


# {{{ test_read_from_bib


def test_read_from_bib() -> None:
    from uvt_scholarly.wos import read_from_bib

    publications = read_from_bib(DATADIR / "savedrecs.bib")
    assert publications

    for pub in publications:
        log.info("%s", pub)
        assert not pub.citations


# }}}

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

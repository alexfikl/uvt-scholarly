# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import tempfile

import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)
TMPDIR = pathlib.Path(tempfile.gettempdir())

# {{{ test_parse_beall_publishers


def test_parse_beall_publishers() -> None:
    from uvt_scholarly.predatory import parse_beall_publishers

    result = parse_beall_publishers()

    # FIXME: didn't count that this is the number on the website, but this is
    # just meant to check if anything changes.. which is not great as a unit test
    assert len(result) == 1356


# }}}


# {{{ test_parse_beall_journals


def test_parse_beall_journals() -> None:
    from uvt_scholarly.predatory import parse_beall_journals

    result = parse_beall_journals()

    # FIXME: also didn't check if this is correct on the website
    assert len(result) == 1525


# }}}

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

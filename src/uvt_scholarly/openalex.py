# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    from uvt_scholarly.publication import Publication

log = make_logger(__name__)


# {{{ download_publications


def download_publications(authorid: str) -> tuple[Publication, ...]:
    return ()


# }}}


# {{{ write_publications

# }}}


# {{{ read_publications

# }}}

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from uvt_scholarly.publication import Publication

log = make_logger(__name__)


def add_cited_by(pubs: Sequence[Publication], citations: Sequence[Publication]):
    pass

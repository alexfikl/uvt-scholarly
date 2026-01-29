# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import Publication

log = make_logger(__name__)

CSV_REQUIRED_COLUMNS = {
    "AF",  # Authors
    "DI",  # DOI
    "DT",  # Document Type
    "EI",  # eISSN
    "IS",  # Issue
    "PY",  # Year
    "SN",  # ISSN
    "SO",  # Journal Name
    "TC",  # Web of Science Total Cited Count
    "TI",  # Document Title
    "VL",  # Volume
    "WC",  # Web of Science Categories
}


def read_from_csv(filename: pathlib.Path) -> tuple[Publication, ...]:
    return ()

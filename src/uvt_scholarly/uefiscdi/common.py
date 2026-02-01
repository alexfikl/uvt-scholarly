# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
import pathlib

import httpx

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import Score

log = make_logger(__name__)


# {{{ URLS

# NOTE: This mostly has the last 5 years, since those are required for UEFISCDI,
# CNATDCU, or university competitions and accreditations.
UEFISCDI_DATABASE_URL = {
    2025: {
        Score.AIS: "https://uefiscdi.gov.ro/resource-865528-AIS.JCR2024.iunie2025.xlsx",
        Score.RIS: "https://uefiscdi.gov.ro/resource-865521-RIS.2024.iunie-2025.xlsx",
        Score.RIF: "https://uefiscdi.gov.ro/resource-865599-RIF.iunie2025.xlsx",
    },
    2024: {
        Score.AIS: "https://uefiscdi.gov.ro/resource-861731-AIS.JCR2023.iunie2024.xlsx",
        Score.RIS: "https://uefiscdi.gov.ro/resource-861773-RIS.2023iunie2024.xlsx",
        Score.RIF: "https://uefiscdi.gov.ro/resource-861735-FIR.2023iunie2024.xlsx",
    },
    2023: {
        Score.AIS: "https://uefiscdi.gov.ro/resource-863884-ais_2022.xlsx",
        Score.RIS: "https://uefiscdi.gov.ro/resource-863882-ris_2022.xlsx",
        Score.RIF: "https://uefiscdi.gov.ro/resource-863887-rif_2022.xlsx",
    },
    2022: {
        Score.AIS: "https://uefiscdi.gov.ro/resource-862108-ais.2021.xlsx",
        Score.RIS: "https://uefiscdi.gov.ro/resource-862102-ris.2021.xlsx",
        Score.RIF: "https://uefiscdi.gov.ro/resource-862155-rif.2021.xlsx",
    },
    2021: {
        Score.AIS: "https://uefiscdi.gov.ro/resource-820980-ais.2020.xlsx",
        Score.RIS: "https://uefiscdi.gov.ro/resource-820984-sri.2020.xlsx",
        Score.RIF: "https://uefiscdi.gov.ro/resource-820987-rif.2020.xlsx",
    },
    2020: {
        Score.AIS: "https://uefiscdi.gov.ro/resource-821312-ais2019-iunie2020-.valori.cuartile.xlsx",
        Score.RIS: "https://uefiscdi.gov.ro/resource-829001-sri.2019.xlsx",
        Score.RIF: "https://uefiscdi.gov.ro/resource-829003-rif.2019.xlsx",
    },
    2019: {
        Score.AIS: "https://uefiscdi.gov.ro/resource-828068",
        Score.RIS: "https://uefiscdi.gov.ro/resource-828022",
        Score.RIF: "https://uefiscdi.gov.ro/resource-828027",
    },
}
"""A mapping of database identifiers to URLs containing the databases themselves."""

UEFISCDI_DEFAULT_VERSION = max(UEFISCDI_DATABASE_URL)
"""Default version used for databases."""

UEFISCDI_DEFAULT_PASSWORD = "uefiscdi"  # noqa: S105
"""Default password used in several UEFISCDI documents."""

UEFISCDI_LATEST_YEAR = max(UEFISCDI_DATABASE_URL)
"""The latest year supported by the library."""


def download_file(url: str, filename: pathlib.Path, *, force: bool = False) -> None:
    if not force and filename.exists():
        return

    # TODO: allow passing a httpx.Client
    with open(filename, "wb") as f, httpx.stream("GET", url) as response:
        response.raise_for_status()

        for chunk in response.iter_bytes():
            f.write(chunk)


# }}}


class ParsingError(Exception):
    """Exception raised while parsing a score file."""


@enum.unique
class Index(enum.Enum):
    AHCI = enum.auto()
    ESCI = enum.auto()
    SCIE = enum.auto()
    SSCI = enum.auto()


INDEX_DISPLAY_NAME = {
    Index.AHCI: "Arts Humanities Citation Index",
    Index.ESCI: "Emerging Sources Citation Index",
    Index.SCIE: "Science Citation Index Expanded",
    Index.SSCI: "Social Sciences Citation Index",
}
"""A mapping of citation indexes (as they appear in the UEFISCDI databases) to their
full names.
"""

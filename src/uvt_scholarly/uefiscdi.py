# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import ISSN, Score

if TYPE_CHECKING:
    from openpyxl.cell import ReadOnlyCell


log = make_logger(__name__)


# {{{ URLS

# NOTE: This mostly has the last 5 years, since those are required for UEFISCDI
# competitions.
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


def download_file(url: str, filename: pathlib.Path) -> None:
    # TODO: allow passing a httpx.Client
    with open(filename, "wb") as f, httpx.stream("GET", url) as response:
        response.raise_for_status()

        for chunk in response.iter_bytes():
            f.write(chunk)


# }}}

# {{{ Index


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

# }}}


# {{{ parse_relative_influence_score


class ParsingError(Exception):
    """Exception raised while parsing a score file."""


def to_float(value: str, default: float = 0.0) -> float:
    if value.strip().upper() in {"", "N/A"}:
        return default

    return float(value)


@dataclass(frozen=True)
class RelativeInfluenceScore:
    journal: str
    issn: ISSN | None
    eissn: ISSN | None
    score: float | None

    @staticmethod
    def from_strings(
        journal: str,
        issn: str = "",
        eissn: str = "",
        score: str = "N/A",
    ) -> RelativeInfluenceScore:
        issn = issn.strip().upper()
        if issn == "N/A":
            issn = ""

        eissn = eissn.strip().upper()
        if eissn == "N/A":
            eissn = ""

        return RelativeInfluenceScore(
            journal=journal.strip(),
            issn=ISSN.from_string(issn) if issn else None,
            eissn=ISSN.from_string(eissn) if eissn else None,
            score=to_float(score.strip()),
        )


class RelativeInfluenceScoreParser:
    @property
    def skip_header(self) -> bool:
        return True

    def parse_row(  # noqa: PLR6301
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeInfluenceScore | None:
        if len(row) != 4:
            raise ValueError(f"unexpected number of columns: {len(row)} (expected 4)")

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[3].value).strip()

        if not score:
            # NOTE: better way to figure out that we reached the end?
            return None

        return RelativeInfluenceScore.from_strings(journal, issn, eissn, score)

    def parse(self, filename: pathlib.Path) -> tuple[RelativeInfluenceScore, ...]:
        result = []

        import openpyxl

        wb = openpyxl.load_workbook(filename, read_only=True)
        if wb is None:
            raise ValueError(f"could not load workbook from file: '{filename}'")

        rows = wb.active.rows
        if self.skip_header:
            _ = next(rows)

        result = []
        for row in rows:
            score = self.parse_row(row)
            if score is None:
                break

            result.append(score)

        return tuple(result)


class RelativeInfluenceScore2025Parser(RelativeInfluenceScoreParser):
    @property
    def skip_header(self) -> bool:
        return True

    def parse_row(  # noqa: PLR6301
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeInfluenceScore | None:
        if len(row) != 5:
            raise ValueError(f"unexpected number of columns: {len(row)} (expected 5)")

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[4].value).strip()

        if not score:
            return None

        return RelativeInfluenceScore.from_strings(journal, issn, eissn, score)


def parse_relative_influence_score(
    filename: pathlib.Path, version: int
) -> tuple[RelativeInfluenceScore, ...]:
    if not filename.exists():
        raise FileNotFoundError(filename)

    if version == 2025:
        parser = RelativeInfluenceScore2025Parser()
    else:
        parser = RelativeInfluenceScoreParser()

    try:
        return parser.parse(filename)
    except Exception as exc:
        raise ParsingError() from exc


# }}}

# {{{


RIS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ris_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    journal_name TEXT NOT NULL,
    issn TEXT NULL,
    eissn TEXT NULL,
    score REAL NULL,
    UNIQUE(year, issn, eissn)
);
"""

RIS_INDEX = """
CREATE INDEX IF NOT EXISTS ris_scores_index
    ON ris_scores (issn, eissn, year);
"""


def write_relative_influence_score(
    filename: pathlib.Path,
    ris: tuple[RelativeInfluenceScore, ...],
    year: int,
) -> None:
    pass


# }}}

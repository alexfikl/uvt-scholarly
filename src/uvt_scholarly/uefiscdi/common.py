# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import ISSN, Score
from uvt_scholarly.utils import UVT_SCHOLARLY_CACHE_DIR

if TYPE_CHECKING:
    import pathlib

    from openpyxl.cell import ReadOnlyCell

log = make_logger(__name__)

UEFISCDI_CACHE_DIRNAME = "uefiscdi-cache"

UEFISCDI_CACHE_DIR = UVT_SCHOLARLY_CACHE_DIR / UEFISCDI_CACHE_DIRNAME

UEFISCDI_DB_FILE = UVT_SCHOLARLY_CACHE_DIR / "uefiscdi.sqlite"

# {{{ misc


EMPTY_SCORE = {"", "N/A"}


def to_float(value: str, default: float = 0.0) -> float:
    value = value.strip().upper()
    if value in EMPTY_SCORE:
        return default

    return float(value)


# NOTE:
#   - "0" appears in RIS/2023
#   - "****-****" appears in RIS/2021
EMPTY_ISSN = {"0", "N/A", "****-****"}


def normalize_issn(issn: str) -> ISSN | None:
    issn = issn.strip().upper()
    if issn in EMPTY_ISSN:
        return None

    return ISSN.from_string(issn)


def is_valid_issn(text: str | ISSN) -> bool:
    if isinstance(text, str):
        try:
            text = ISSN.from_string(text)
        except ValueError:
            return False

    return text.is_valid


# }}}


# {{{ URLs

# NOTE: This mostly has the last 5-ish years, since those are required for UEFISCDI,
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
}
"""A mapping of database identifiers to URLs containing the databases themselves."""

UEFISCDI_DEFAULT_VERSION = max(UEFISCDI_DATABASE_URL)
"""Default version used for databases."""

UEFISCDI_DEFAULT_PASSWORD = "uefiscdi"  # noqa: S105
"""Default password used in several UEFISCDI documents."""

UEFISCDI_LATEST_YEAR = max(UEFISCDI_DATABASE_URL)
"""The latest year supported by the library."""


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


# {{{ Score


@dataclass(frozen=True, slots=True)
class Score(ABC):
    journal: str
    issn: ISSN | None
    eissn: ISSN | None
    score: float

    def __hash__(self) -> int:
        return hash((self.issn, self.eissn))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return self.issn == other.issn and self.eissn == other.eissn

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def issns(self) -> str | None:
        return str(self.issn) if self.issn else None

    @property
    def eissns(self) -> str | None:
        return str(self.eissn) if self.eissn else None

    @property
    def is_valid(self) -> bool:
        if self.issn and not self.issn.is_valid:
            return False

        if self.eissn and not self.eissn.is_valid:
            return False

        if not self.journal:
            return False

        if self.score < 0.0:  # noqa: SIM103
            return False

        return True


ScoreT = TypeVar("ScoreT", bound=Score)

# }}}

# {{{ XLSXParser


class XLSXParser(Generic[ScoreT], ABC):
    @property
    def skip_header(self) -> bool:
        return True

    @abstractmethod
    def parse_row(self, row: tuple[ReadOnlyCell, ...]) -> ScoreT | None:
        pass

    def parse(self, filename: pathlib.Path) -> tuple[ScoreT, ...]:
        result = []

        import openpyxl

        # NOTE:
        # - data_only: required because some files have formulas that we do
        #   not want to evaluate (or can't; the ones found were invalid)
        # - read_only: we are not going to be modifying these files.
        wb = openpyxl.load_workbook(filename, data_only=True, read_only=True)
        if wb is None:
            raise ValueError(f"could not load workbook from file: '{filename}'")

        rows = wb.active.rows
        if self.skip_header:
            _ = next(rows)

        from uvt_scholarly.utils import ParsingError

        result = {}
        for row in rows:
            score = self.parse_row(row)

            if score is None:
                break

            if not score.is_valid:
                breakpoint()
                raise ParsingError(f"score on row {row[0].row} is not valid")

            if score in result:
                other = result[score]
                issn = score.issn or score.eissn
                log.warning(
                    "Journal '%s' (%s %.3f) with ISSN '%s' already exists: "
                    "'%s' (%s %.3f).",
                    score.journal,
                    score.name,
                    score.score,
                    issn,
                    other.journal,
                    score.name,
                    other.score,
                )

                # NOTE: this is probably not a great idea, but we're trying to
                # be generous and use the bigger score.
                if result[score].score < score.score:
                    result[score] = score

                continue

            result[score] = score

        return tuple(result.values())


# }}}

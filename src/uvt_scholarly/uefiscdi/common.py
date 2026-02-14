# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import ISSN, Score
from uvt_scholarly.utils import UVT_SCHOLARLY_CACHE_DIR

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence
    from types import TracebackType

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
#   - "N/A" seems to be the common value
#   - "0" appears in RIS/2023
#   - "****-****" appears in RIS/2021
EMPTY_ISSN = {"0", "N/A", "****-****"}


def normalize_issn(issn: str) -> ISSN | None:
    """A helper function to normalize ISSNs from UEFISCDI documents."""

    issn = issn.strip().upper()
    if issn in EMPTY_ISSN:
        return None

    return ISSN.from_string(issn)


def is_valid_issn(text: str | ISSN) -> bool:
    """Check if the given text is a valid ISSN."""
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


# {{{ Edition


@enum.unique
class Edition(enum.Enum):
    """The citation index to which a given score belongs to.

    Many relative scores are generally computed per field of research. These
    are the citation indices used by the UEFISCDI (by way of Web of Science).
    """

    AHCI = enum.auto()
    """Arts Humanities Citation Index."""
    ESCI = enum.auto()
    """Emerging Sources Citation Index."""
    SCIE = enum.auto()
    """Science Citation Index Expanded."""
    SSCI = enum.auto()
    """Social Sciences Citation Index."""


EDITION_DISPLAY_NAME = {
    Edition.AHCI: "Arts Humanities Citation Index",
    Edition.ESCI: "Emerging Sources Citation Index",
    Edition.SCIE: "Science Citation Index Expanded",
    Edition.SSCI: "Social Sciences Citation Index",
}
"""A mapping of citation indices (as they appear in the UEFISCDI databases) to their
full names.
"""

# }}}


# {{{ Score


@dataclass(frozen=True, eq=False, slots=True)
class Score(ABC):
    """A base class for parsed scores from UEFISCDI documents."""

    journal: str
    """The journal this score is for."""
    issn: ISSN | None
    """The ISSN of the journal, if any."""
    eissn: ISSN | None
    """The eISSN of the journal, if any."""
    score: float
    """The score of the journal. This value can also be zero if no score is given."""

    def __hash__(self) -> int:
        return hash((self.issn, self.eissn))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return self.issn == other.issn and self.eissn == other.eissn

    @property
    @abstractmethod
    def name(self) -> str:
        """An identifier name for the score, e.g. RIS."""

    @property
    def issns(self) -> str | None:
        """A string variant of the ISSN."""
        return str(self.issn) if self.issn else None

    @property
    def eissns(self) -> str | None:
        """A string variant of the eISSN."""
        return str(self.eissn) if self.eissn else None

    @property
    def is_valid(self) -> bool:
        """Checks if the score is valid.

        In general, the score is valid if it has a non-empty journal name, valid
        ISSN and eISSN and the value of the numerical score is positive. Subclasses
        can check additional requirements.
        """
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
"""An invariant [typing.TypeVar][] for [Score][]."""

# }}}

# {{{ XLSXParser


class XLSXParser(Generic[ScoreT], ABC):
    """A parser / reader for XLSX score files from the UEFISCDI."""

    @property
    def skip_header(self) -> bool:
        """If *True*, the first row in the file is skipped."""
        return True

    @property
    @abstractmethod
    def ncolumns(self) -> int:
        """Number of columns in the parsed file."""

    @abstractmethod
    def parse_row(self, row: tuple[ReadOnlyCell, ...]) -> ScoreT | None:
        """Parse a row from the file and return the [Score][]."""

    def parse(self, filename: pathlib.Path) -> tuple[ScoreT, ...]:
        """Read an UEFISCDI XLSX file and return the valid scores.

        Raises:
            uvt_scholarly.utils.ParsingError: if any of the scores are not valid.
                Note that all the scores from [UEFISCDI_DATABASE_URL][] are
                known to parse correctly.
        """
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
            if len(row) != self.ncolumns:
                raise ParsingError(
                    f"unexpected number of columns on row {row[0].row}: "
                    f"{len(row)} (expected {self.ncolumns})"
                )

            score = self.parse_row(row)

            if score is None:
                break

            if not score.is_valid:
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
                if other.score < score.score:
                    result[score] = score

                continue

            result[score] = score

        return tuple(result.values())


# }}}


# {{{ Database


def astuple(score: Score) -> tuple[str | None, ...]:
    result = []
    for f in fields(score):  # ty: ignore[invalid-argument-type]
        field = getattr(score, f.name)

        result.append(str(field) if field is not None else None)

    return tuple(result)


class Database(Generic[ScoreT]):
    """A context manager that can be used to add scores to a [sqlite3][] database.

    This class will handle creating the database from a given schema and an
    index for efficient searching.
    """

    name: ClassVar[str]
    """The name of the database."""
    schema: ClassVar[str]
    """A schema for the database. Note that the database name should match [name][]."""
    index: ClassVar[str]
    """An statement used to create an index for the database. Note that the
    database and index names should match [name][].
    """

    filename: pathlib.Path
    """The file containing the database."""

    conn: sqlite3.Connection | None

    def __init__(self, filename: pathlib.Path) -> None:
        self.filename = filename
        self.conn = None

    def init(self) -> None:
        self.conn = conn = sqlite3.connect(self.filename)

        # NOTE: this should only be executed on creation, but it's not a problem
        conn.execute(self.schema)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")

    def __enter__(self) -> Database:
        self.init()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.conn:
            # NOTE: we only create the index on exist so that the database
            # already contains all the rows. This should be more efficient.
            self.conn.execute(self.index)

            self.conn.commit()
            self.conn.close()

        self.conn = None

    def insert(self, year: int, rif: Sequence[ScoreT]) -> None:
        if self.conn is None:
            raise ValueError(f"not connected to database '{self.filename}'")

        if not rif:
            return

        columns = ", ".join(f.name for f in fields(rif[0]))
        values = ", ".join("?" for _ in fields(rif[0]))

        self.conn.executemany(
            f"""
            INSERT INTO {self.name} (year, {columns})
            VALUES (?, {values})
            """,  # noqa: S608
            ((year, *astuple(r)) for r in rif),
        )

    def find_by_issn_impl(self, text: ISSN, year: int) -> ScoreT | None:
        raise NotImplementedError(f"{type(self)} does not implement 'find_by_issn'")

    def find_by_issn(self, text: str | ISSN, year: int) -> ScoreT | None:
        if self.conn is None:
            raise ValueError(f"not connected to database '{self.filename}'")

        if not is_valid_issn(text):
            raise ValueError(f"not a valid ISSN: '{text}'")

        if year not in UEFISCDI_DATABASE_URL:
            raise ValueError(f"unsupported year: '{year}'")

        return self.find_by_issn_impl(
            text if isinstance(text, ISSN) else ISSN.from_string(text), year
        )

    def max_score_by_issn(self, text: str | ISSN, past: int = 5) -> float | None:
        if self.conn is None:
            raise ValueError(f"not connected to database '{self.filename}'")

        if not is_valid_issn(text):
            raise ValueError(f"not a valid ISSN: '{text}'")

        result = self.conn.execute(
            f"""
            SELECT MAX(score)
            FROM {self.name}
            WHERE (issn = ? OR eissn = ?) AND year >= ?
            """,  # noqa: S608
            (str(text), str(text), UEFISCDI_LATEST_YEAR - past),
        )

        row = result.fetchone()
        return row[0]


# }}}

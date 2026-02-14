# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import ISSN
from uvt_scholarly.uefiscdi.common import (
    UEFISCDI_CACHE_DIRNAME,
    UEFISCDI_DATABASE_URL,
    Database,
    Score,
    XLSXParser,
    normalize_issn,
    to_float,
)

if TYPE_CHECKING:
    import pathlib

    from openpyxl.cell import ReadOnlyCell


log = make_logger(__name__)

# {{{ parse_relative_impact_factor

# NOTE: these seem to be the same as the RIS values
RIF_INCORRECT_ISSN = {
    # eISSN: African Entomology (this is even wrong on their website..)
    "2254-8854": "2224-8854",
    # eISSN: Radical Philosophy
    "0030-211X": "0300-211X",
    # eISSN: World Journal for Pediatric and Congenital Heart Surgery
    "2150-0136": "2150-136X",
    # eISSN: International Journal for Lesson and Learning Studies
    "2016-8261": "2046-8261",
    # eISSN: Journal of Wound Care
    "2062-2916": "2052-2916",
    # eISSN: Journal of Intellectual Capital
    "758-7468": "1758-7468",
    # eISSN: Proceedings of the Institution of Mechanical Engineers Part B
    "2041-1975": "2041-2975",
    # eISSN: Sociology of Race and Ethnicity
    "2332-6505": "2332-6506",
    # eISSN: Current Topics in Medicinal Chemistry
    "1873-5294": "1873-4294",
    # ISSN: Invasive Plant Science and Management
    "1929-7291": "1939-7291",
}


@dataclass(frozen=True, eq=False, slots=True)
class RelativeImpactFactor(Score):
    @property
    def name(self) -> str:
        return "RIF"

    @staticmethod
    def from_strings(
        journal: str,
        issn: str,
        eissn: str,
        score: str,
    ) -> RelativeImpactFactor:
        issn = issn.strip().upper()
        eissn = eissn.strip().upper()

        return RelativeImpactFactor(
            journal=journal.strip(),
            issn=normalize_issn(RIF_INCORRECT_ISSN.get(issn, issn)),
            eissn=normalize_issn(RIF_INCORRECT_ISSN.get(eissn, eissn)),
            score=to_float(score),
        )


class RelativeImpactFactorPraser(XLSXParser[RelativeImpactFactor]):
    @property
    def ncolumns(self) -> int:
        return 4

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeImpactFactor | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[3].value).strip()

        return RelativeImpactFactor.from_strings(journal, issn, eissn, score)


class RelativeImpactFactor2025Parser(RelativeImpactFactorPraser):
    @property
    def ncolumns(self) -> int:
        return 5

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeImpactFactor | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[4].value).strip()

        return RelativeImpactFactor.from_strings(journal, issn, eissn, score)


class RelativeImpactFactor2020Parser(RelativeImpactFactorPraser):
    @property
    def ncolumns(self) -> int:
        return 3

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeImpactFactor | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        score = str(row[2].value).strip()

        return RelativeImpactFactor.from_strings(journal, issn, "N/A", score)


def parse_relative_impact_factor(
    filename: pathlib.Path, version: int
) -> tuple[RelativeImpactFactor, ...]:
    if not filename.exists():
        raise FileNotFoundError(filename)

    if version not in UEFISCDI_DATABASE_URL:
        raise ValueError(f"unsupported database version: {version}")

    if version == 2025:
        parser = RelativeImpactFactor2025Parser()
    elif version == 2020:
        parser = RelativeImpactFactor2020Parser()
    else:
        parser = RelativeImpactFactorPraser()

    from uvt_scholarly.utils import ParsingError

    try:
        return parser.parse(filename)
    except Exception as exc:
        raise ParsingError() from exc


# }}}

# {{{ store_relative_impact_factor


class RelativeImpactFactorDatabase(Database[RelativeImpactFactor]):
    name: ClassVar[str] = "relative_impact_factors"
    schema: ClassVar[str] = f"""
        CREATE TABLE IF NOT EXISTS {name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            journal TEXT NOT NULL,
            issn TEXT NULL,
            eissn TEXT NULL,
            score REAL NOT NULL,
            UNIQUE(year, issn, eissn)
        );
    """
    index: ClassVar[str] = f"""
        CREATE INDEX IF NOT EXISTS {name}_index
            ON {name} (year, issn, eissn);
    """

    def find_by_issn_impl(self, text: ISSN, year: int) -> RelativeImpactFactor | None:
        assert self.conn is not None
        result = self.conn.execute(
            f"""
            SELECT journal, issn, eissn, score
            FROM {self.name}
            WHERE (issn = ? OR eissn = ?) AND year = ?
            """,  # noqa: S608
            (str(text), str(text), year),
        )

        for journal, issn, eissn, score in result.fetchall():
            return RelativeImpactFactor(
                journal=journal,
                issn=ISSN.from_string(issn) if issn else None,
                eissn=ISSN.from_string(eissn) if eissn else None,
                score=score,
            )

        return None


def store_relative_impact_factor(
    filename: pathlib.Path,
    *,
    years: set[int] | None = None,
    force: bool = False,
) -> None:
    if years is None:
        years = set(UEFISCDI_DATABASE_URL)

    if unknown := years - set(UEFISCDI_DATABASE_URL):
        raise ValueError(f"unsupported years: {unknown}")

    dirname = filename.parent / UEFISCDI_CACHE_DIRNAME
    if not dirname.exists():
        dirname.mkdir(parents=True)

    from uvt_scholarly.publication import Score
    from uvt_scholarly.utils import download_file

    with RelativeImpactFactorDatabase(filename) as db:
        for i, year in enumerate(years):
            url = UEFISCDI_DATABASE_URL[year][Score.RIF]

            xlsxfile = dirname / f"uvt-scholarly-rif-{year}.xlsx"
            download_file(url, xlsxfile, force=force)

            log.info("Processing RIF scores for %d: '%s'.", year, xlsxfile)
            scores = parse_relative_impact_factor(xlsxfile, year)

            log.info("Inserting %d RIF scores for %d into database.", len(scores), year)
            db.insert(year, scores)

            if i != len(years) - 1:
                log.info("")


# }}}

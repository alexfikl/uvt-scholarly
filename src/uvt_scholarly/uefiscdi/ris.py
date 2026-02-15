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

# {{{ parse_relative_influence_score

# NOTE: some of these are incorrect in multiple years
RIS_INCORRECT_ISSN = {
    # eISSN: World Journal for Pediatric and Congenital Heart Surgery
    "2150-0136": "2150-136X",
    # eISSN: Journal of Intellectual Capital
    "758-7468": "1758-7468",
    # eISSN: Current Topics in Medicinal Chemistry
    "1873-5294": "1873-4294",
    # eISSN: International Journal for Lesson and Learning Studies
    "2016-8261": "2046-8261",
    # eISSN: Journal of Wound Care
    "2062-2916": "2052-2916",
    # eISSN: Proceedings of the Institution of Mechanical Engineers Part B
    "2041-1975": "2041-2975",
    # eISSN: Radical Philosophy
    "0030-211X": "0300-211X",
    # eISSN: Sociology of Race and Ethnicity
    "2332-6505": "2332-6506",
    # eISSN: African Entomology (this is even wrong on their website..)
    "2254-8854": "2224-8854",
    # ISSN: Invasive Plant Science and Management
    "1929-7291": "1939-7291",
}

# NOTE: the names should match (case senstitive) the UEFISCDI documents
# NOTE: only add cases which lack both ISSN and eISSN. It seems like most of the
# other missing ISSNs are just because ISSN == eISSN or there is only one anyway
RIS_MISSING_ISSN = {
    # https://journals.sagepub.com/home/IYA
    "Infancia y Aprendizaje": "0210-3702",
}

RIS_MISSING_EISSN = {
    # https://journals.sagepub.com/home/IYA
    "Infancia y Aprendizaje": "1578-4126",
}


@dataclass(frozen=True, eq=False, slots=True)
class RelativeInfluenceScore(Score):
    """The RIF for a given publication."""

    @property
    def name(self) -> str:
        return "RIS"

    @staticmethod
    def from_strings(
        journal: str,
        issn: str,
        eissn: str,
        score: str,
    ) -> RelativeInfluenceScore:
        """Convert the given data into an [RelativeInfluenceScore][].

        The given data is normalized and cleaned up, as appropriate. This function
        can raise if the data is incorrect (e.g. a non-numeric *score*).
        """
        from uvt_scholarly.uefiscdi.common import EMPTY_ISSN

        journal = journal.strip()
        issn = issn.strip().upper()
        eissn = eissn.strip().upper()

        if issn in EMPTY_ISSN:
            issn = RIS_MISSING_ISSN.get(journal, issn)

        if eissn in EMPTY_ISSN:
            eissn = RIS_MISSING_EISSN.get(journal, eissn)

        return RelativeInfluenceScore(
            journal=journal,
            issn=normalize_issn(RIS_INCORRECT_ISSN.get(issn, issn)),
            eissn=normalize_issn(RIS_INCORRECT_ISSN.get(eissn, eissn)),
            score=to_float(score),
        )


class RelativeInfluenceScoreParser(XLSXParser[RelativeInfluenceScore]):
    @property
    def ncolumns(self) -> int:
        return 4

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[3].value).strip()

        return RelativeInfluenceScore.from_strings(journal, issn, eissn, score)


class RelativeInfluenceScore2025Parser(RelativeInfluenceScoreParser):
    @property
    def ncolumns(self) -> int:
        return 5

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[4].value).strip()

        return RelativeInfluenceScore.from_strings(journal, issn, eissn, score)


class RelativeInfluenceScore2020Parser(RelativeInfluenceScoreParser):
    @property
    def ncolumns(self) -> int:
        return 3

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> RelativeInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        score = str(row[2].value).strip()

        return RelativeInfluenceScore.from_strings(journal, issn, "N/A", score)


def parse_relative_influence_score(
    filename: pathlib.Path, version: int
) -> tuple[RelativeInfluenceScore, ...]:
    """Read RIS scores from the given *file*.

    Parameters:
        version: the year the list in *filename* was published.

    Raises:
        uvt_scholarly.utils.ParsingError: if entries in the file are not valid.
    """
    if not filename.exists():
        raise FileNotFoundError(filename)

    if version not in UEFISCDI_DATABASE_URL:
        raise ValueError(f"unsupported database version: {version}")

    if version == 2025:
        parser = RelativeInfluenceScore2025Parser()
    elif version == 2020:
        parser = RelativeInfluenceScore2020Parser()
    else:
        parser = RelativeInfluenceScoreParser()

    from uvt_scholarly.utils import ParsingError

    try:
        return parser.parse(filename)
    except Exception as exc:
        raise ParsingError() from exc


# }}}

# {{{ store_relative_influence_score


RIS_SCHEMA = """
"""

RIS_INDEX = """
"""


class RelativeInfluenceScoreDatabase(Database[RelativeInfluenceScore]):
    name: ClassVar[str] = "relative_influence_scores"
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

    def find_by_issn_impl(self, text: ISSN, year: int) -> RelativeInfluenceScore | None:
        assert self.conn is not None
        result = self.conn.execute(
            """
            SELECT journal, issn, eissn, score
            FROM relative_influence_scores
            WHERE (issn = ? OR eissn = ?) AND year = ?
            """,
            (str(text), str(text), year),
        )

        for journal, issn, eissn, score in result.fetchall():
            return RelativeInfluenceScore(
                journal=journal,
                issn=ISSN.from_string(issn) if issn else None,
                eissn=ISSN.from_string(eissn) if eissn else None,
                score=score,
            )

        return None


def store_relative_influence_score(
    filename: pathlib.Path,
    *,
    years: int | set[int] | None = None,
    force: bool = False,
) -> None:
    """Download RIS scores for the given *years* and store them in *filename*.

    Parameters:
        years: A list of years for which to download the RIS scores. By default,
            all the years in
            [uvt_scholarly.uefiscdi.UEFISCDI_DATABASE_URL][] are downloaded.
        force: If *True*, all documents are re-downloaded (even if cached).

    Raises:
        uvt_scholarly.utils.ParsingError: if any of the documents fail to parse.
        uvt_scholarly.utils.DownloadError: if any of the documents do now download.
    """
    if years is None:
        years = set(UEFISCDI_DATABASE_URL)

    if isinstance(years, int):
        years = {years}

    if unknown := years - set(UEFISCDI_DATABASE_URL):
        raise ValueError(f"unsupported years: {unknown}")

    dirname = filename.parent / UEFISCDI_CACHE_DIRNAME
    if not dirname.exists():
        dirname.mkdir(parents=True)

    from uvt_scholarly.publication import Score
    from uvt_scholarly.utils import download_file

    with RelativeInfluenceScoreDatabase(filename) as db:
        for i, year in enumerate(years):
            url = UEFISCDI_DATABASE_URL[year][Score.RIS]

            xlsxfile = dirname / f"uvt-scholarly-ris-{year}.xlsx"
            download_file(url, xlsxfile, force=force)

            log.info("Processing RIS scores for %d: '%s'.", year, xlsxfile)
            scores = parse_relative_influence_score(xlsxfile, year)

            log.info("Inserting %d RIF scores for %d into database.", len(scores), year)
            db.insert(year, scores)

            if i != len(years) - 1:
                log.info("")


# }}}

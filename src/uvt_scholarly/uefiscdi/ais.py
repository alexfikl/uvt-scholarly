# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from uvt_scholarly.identifiers import ISSN
from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import JournalCategory, Quartile
from uvt_scholarly.uefiscdi.common import (
    UEFISCDI_CACHE_DIRNAME,
    UEFISCDI_DATABASE_URL,
    UEFISCDI_DEFAULT_PASSWORD,
    CitationIndex,
    Database,
    Score,
    XLSXParser,
    normalize_issn,
    to_float,
    to_int,
    to_quartile,
)

if TYPE_CHECKING:
    from openpyxl.cell import ReadOnlyCell

    from uvt_scholarly.export.cs import Category

log = make_logger(__name__)


# {{{ parse_article_influence_score

KNOWN_YEARS_WITH_QUARTILES = frozenset({2020, 2021, 2022, 2023})

# NOTE: these seem to be the same across all the UEFISCDI databases?
AIS_INCORRECT_ISSN = {
    # eISSN: World Journal for Pediatric and Congenital Heart Surgery
    "2150-0136": "2150-136X",
    # eISSN: African Entomology (this is even wrong on their website..)
    "2254-8854": "2224-8854",
    # eISSN: Radical Philosophy
    "0030-211X": "0300-211X",
    # eISSN: Journal of Wound Care
    "2062-2916": "2052-2916",
    # eISSN: International Journal for Lesson and Learning Studies
    "2016-8261": "2046-8261",
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

# NOTE: seems to only be used in the 2021 version
AIS_EXTRA_CITATION_INDEX_NAMES = {
    "SCIENCE": "SCIE",
    "SOCIAL SCIENCES": "SSCI",
}


@dataclass(frozen=True, eq=False, slots=True)
class ArticleInfluenceScore(Score):
    """The AIS for a given journal."""

    citation_index: CitationIndex
    """The citation index this score is a part of."""
    journal_category: JournalCategory
    """The category the journal is part of (scores are relative to the category)."""

    quartile: Quartile
    """The quartile the journal belongs to, in its category."""
    position: int
    """The position of the journal in its quartile."""

    category: Category | None
    """A category based on the quartile used by the CS exporter."""

    def __hash__(self) -> int:
        return hash((self.issn, self.eissn, self.journal_category, self.citation_index))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return (
            self.issn == other.issn
            and self.eissn == other.eissn
            and self.citation_index == other.citation_index
            and self.journal_category == other.journal_category
        )

    @property
    def name(self) -> str:
        return f"AIS[{self.citation_index.name}]"

    @staticmethod
    def from_strings(
        journal: str,
        issn: str,
        eissn: str,
        journal_category: str,
        citation_index: str,
        score: str,
        quartile: int | str | Quartile,
        position: int | str,
    ) -> ArticleInfluenceScore:
        """Convert the given data into an [ArticleInfluenceScore][].

        The given data is normalized and cleaned up, as appropriate. This function
        can raise if the data is incorrect (e.g. a non-numeric *score*).
        """
        from uvt_scholarly.wos import parse_wos_categories

        issn = issn.strip().upper()
        eissn = eissn.strip().upper()

        # NOTE: some entries have "AHCI, SSCI" or something. Not quite sure why..
        if "," in citation_index:
            citation_index, _ = citation_index.split(",", maxsplit=1)
        citation_index = citation_index.strip().upper()

        return ArticleInfluenceScore(
            journal=journal.strip(),
            issn=normalize_issn(AIS_INCORRECT_ISSN.get(issn, issn)),
            eissn=normalize_issn(AIS_INCORRECT_ISSN.get(eissn, eissn)),
            score=to_float(score),
            citation_index=CitationIndex[citation_index],
            journal_category=parse_wos_categories(journal_category)[0],
            quartile=to_quartile(quartile),
            position=to_int(position),
            category=None,
        )


class ArticleInfluenceScoreParser(XLSXParser[ArticleInfluenceScore]):
    def __init__(self) -> None:
        # NOTE: these are only used by versions that have a quartile and do not
        # have a position inside that quartile
        self.position: int = 0
        self.quartile: Quartile = Quartile.Q1

    @property
    def ncolumns(self) -> int:
        return 6

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        journal_category = str(row[3].value).strip()
        citation_index = str(row[4].value).strip()
        score = str(row[5].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, journal_category, citation_index, score, "N/A", "N/A"
        )


class ArticleInfluenceScore2023Parser(ArticleInfluenceScoreParser):
    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        # NOTE: column is `CATEGORY - INDEX` in this version of the file
        journal_category, citation_index = (
            str(row[3].value).strip().rsplit("-", maxsplit=1)
        )
        score = str(row[4].value).strip()
        quartile = to_quartile(str(row[5].value))

        if self.quartile != quartile:
            self.position = 0
        self.position += 1

        return ArticleInfluenceScore.from_strings(
            journal,
            issn,
            eissn,
            journal_category,
            citation_index,
            score,
            quartile,
            self.position,
        )


class ArticleInfluenceScore2022Parser(ArticleInfluenceScoreParser):
    @property
    def ncolumns(self) -> int:
        return 7

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[3].value).strip()
        citation_index = str(row[4].value).strip()
        # NOTE: column is `CATEGORY - INDEX` in this version of the file
        journal_category, _ = str(row[5].value).strip().rsplit("-", maxsplit=1)
        quartile = to_quartile(str(row[6].value))

        if self.quartile != quartile:
            self.position = 0
        self.position += 1

        return ArticleInfluenceScore.from_strings(
            journal,
            issn,
            eissn,
            journal_category,
            citation_index,
            score,
            quartile,
            self.position,
        )


class ArticleInfluenceScore2021Parser(ArticleInfluenceScoreParser):
    @property
    def ncolumns(self) -> int:
        return 7

    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[3].value).strip()
        citation_index = str(row[4].value).strip()
        journal_category = str(row[5].value).strip()
        quartile = to_quartile(str(row[6].value))

        if self.quartile != quartile:
            self.position = 0
        self.position += 1

        return ArticleInfluenceScore.from_strings(
            journal,
            issn,
            eissn,
            journal_category,
            AIS_EXTRA_CITATION_INDEX_NAMES.get(citation_index, citation_index),
            score,
            quartile,
            self.position,
        )


class ArticleInfluenceScore2020Parser(ArticleInfluenceScoreParser):
    def parse_row(
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        assert len(row) == self.ncolumns
        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        score = str(row[2].value).strip()
        citation_index = str(row[3].value).strip()
        journal_category = str(row[4].value).strip()
        quartile = to_quartile(str(row[5].value))

        if self.quartile != quartile:
            self.position = 0
        self.position += 1

        return ArticleInfluenceScore.from_strings(
            journal,
            issn,
            "N/A",
            journal_category,
            citation_index,
            score,
            quartile,
            self.position,
        )


def _decrypt_file(filename: pathlib.Path, password: str) -> pathlib.Path:
    import tempfile

    import msoffcrypto

    try:
        with tempfile.NamedTemporaryFile(suffix=filename.suffix, delete=False) as outf:
            with open(filename, "rb") as f:
                msfile = msoffcrypto.OfficeFile(f)
                msfile.load_key(password=password)
                msfile.decrypt(outf)

            return pathlib.Path(outf.name)
    except msoffcrypto.exceptions.DecryptionError:
        return filename


def parse_article_influence_score(
    filename: pathlib.Path, version: int
) -> tuple[ArticleInfluenceScore, ...]:
    """Read AIS scores from the given *file*.

    Parameters:
        version: the year the list in *filename* was published.

    Raises:
        uvt_scholarly.utils.ParsingError: if entries in the file are not valid.
    """
    if not filename.exists():
        raise FileNotFoundError(filename)

    if version not in UEFISCDI_DATABASE_URL:
        raise ValueError(f"unsupported database version: {version}")

    if version == 2023:
        parser = ArticleInfluenceScore2023Parser()
    elif version == 2022:
        parser = ArticleInfluenceScore2022Parser()
    elif version == 2021:
        parser = ArticleInfluenceScore2021Parser()
    elif version == 2020:
        parser = ArticleInfluenceScore2020Parser()
    else:
        parser = ArticleInfluenceScoreParser()

    from uvt_scholarly.utils import ParsingError

    decrypted_filename = _decrypt_file(filename, UEFISCDI_DEFAULT_PASSWORD)
    try:
        return parser.parse(decrypted_filename)
    except Exception as exc:
        raise ParsingError() from exc


# }}}


# {{{ store_article_influence_score


class ArticleInfluenceScoreDatabase(Database):
    name: ClassVar[str] = "article_influence_scores"
    schema: ClassVar[str] = f"""
        CREATE TABLE IF NOT EXISTS {name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            journal TEXT NOT NULL,
            issn TEXT NULL,
            eissn TEXT NULL,
            citation_index TEXT NOT NULL,
            journal_category TEXT NOT NULL,
            score REAL NOT NULL,
            quartile INTEGER NOT NULL,
            position INTEGER NOT NULL,
            category INTEGER NULL,
            UNIQUE(year, issn, eissn, citation_index, journal_category)
        );
    """
    index: ClassVar[str] = f"""
        CREATE INDEX IF NOT EXISTS {name}_index
            ON {name} (year, issn, eissn, citation_index, journal_category);
    """

    def find_by_issn_impl(self, text: ISSN, year: int) -> ArticleInfluenceScore | None:
        assert self.conn is not None
        result = self.conn.execute(
            f"""
            SELECT journal, issn, eissn, journal_category, citation_index, score, quartile, position
            FROM {self.name}
            WHERE (issn = ? OR eissn = ?) AND year = ?
            """,  # noqa: E501,S608
            (str(text), str(text), year),
        )

        from uvt_scholarly.export.cs import Category
        from uvt_scholarly.wos import parse_wos_categories

        for (
            journal,
            issn,
            eissn,
            journal_category,
            citation_index,
            score,
            quartile,
            position,
            category,
        ) in result.fetchall():
            return ArticleInfluenceScore(
                journal=journal,
                issn=ISSN.from_string(issn) if issn else None,
                eissn=ISSN.from_string(eissn) if eissn else None,
                citation_index=CitationIndex[citation_index],
                journal_category=parse_wos_categories(journal_category)[0],
                score=score,
                quartile=Quartile[quartile],
                position=position,
                category=Category[category],
            )

        return None


def store_article_influence_score(
    filename: pathlib.Path,
    *,
    years: set[int] | None = None,
    a_star_percentage: int = 20,
    force: bool = False,
) -> None:
    """Download AIS scores for the given *years* and store them in *filename*.

    Parameters:
        years: A list of years for which to download the AIS scores. By default,
            all the years in
            [uvt_scholarly.uefiscdi.UEFISCDI_DATABASE_URL][] are downloaded.
        a_star_percentage: Percentage used in determining categories for the
            Computer Science department.
        force: If *True*, all documents are re-downloaded (even if cached).

    Raises:
        uvt_scholarly.utils.ParsingError: if any of the documents fail to parse.
        uvt_scholarly.utils.DownloadError: if any of the documents do now download.
    """
    if years is None:
        years = set(UEFISCDI_DATABASE_URL)

    if unknown := years - set(UEFISCDI_DATABASE_URL):
        raise ValueError(f"unsupported years: {unknown}")

    dirname = filename.parent / UEFISCDI_CACHE_DIRNAME
    if not dirname.exists():
        dirname.mkdir(parents=True)

    from uvt_scholarly.publication import ScoreType
    from uvt_scholarly.utils import download_file

    with ArticleInfluenceScoreDatabase(filename) as db:
        for i, year in enumerate(years):
            url = UEFISCDI_DATABASE_URL[year][ScoreType.AIS]

            xlsxfile = dirname / f"uvt-scholarly-AIS-{year}.xlsx"
            download_file(url, xlsxfile, force=force)

            log.info("Processing AIS scores for %d: '%s'.", year, xlsxfile)
            scores = parse_article_influence_score(xlsxfile, year)

            if year in KNOWN_YEARS_WITH_QUARTILES:
                from uvt_scholarly.export.cs import recategorize_article_influence_score

                scores = recategorize_article_influence_score(
                    scores, a_star_percentage=a_star_percentage
                )

            log.info("Inserting %d AIS scores for %d into database.", len(scores), year)
            db.insert(year, scores)

            if i != len(years) - 1:
                log.info("")


# }}}

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import ISSN, Category
from uvt_scholarly.uefiscdi.common import (
    UEFISCDI_CACHE_DIRNAME,
    UEFISCDI_DATABASE_URL,
    UEFISCDI_DEFAULT_PASSWORD,
    Database,
    Edition,
    Score,
    XLSXParser,
    normalize_issn,
    to_float,
)

if TYPE_CHECKING:
    from openpyxl.cell import ReadOnlyCell

log = make_logger(__name__)


# {{{ parse_article_influence_score

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
AIS_EDITION_NAMES = {
    "SCIENCE": "SCIE",
    "SOCIAL SCIENCES": "SSCI",
}


@dataclass(frozen=True, eq=False, slots=True)
class ArticleInfluenceScore(Score):
    edition: Edition
    category: Category

    def __hash__(self) -> int:
        return hash((self.issn, self.eissn, self.category, self.edition))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return (
            self.issn == other.issn
            and self.eissn == other.eissn
            and self.edition == other.edition
        )

    @property
    def name(self) -> str:
        return f"AIS[{self.edition.name}]"

    @staticmethod
    def from_strings(
        journal: str,
        issn: str,
        eissn: str,
        category: str,
        edition: str,
        score: str,
    ) -> ArticleInfluenceScore:
        from uvt_scholarly.wos import parse_wos_categories

        issn = issn.strip().upper()
        eissn = eissn.strip().upper()

        # NOTE: some entries have "AHCI, SSCI" or something. Not quite sure why..
        if "," in edition:
            edition, _ = edition.split(",", maxsplit=1)

        return ArticleInfluenceScore(
            journal=journal.strip(),
            issn=normalize_issn(AIS_INCORRECT_ISSN.get(issn, issn)),
            eissn=normalize_issn(AIS_INCORRECT_ISSN.get(eissn, eissn)),
            score=to_float(score),
            edition=Edition[edition.strip().upper()],
            category=parse_wos_categories(category)[0],
        )


class ArticleInfluenceScoreParser(XLSXParser[ArticleInfluenceScore]):
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
        category = str(row[3].value).strip()
        edition = str(row[4].value).strip()
        score = str(row[5].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, category, edition, score
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
        # NOTE: column is `CATEGORY - EDITION` in this version of the file
        category, edition = str(row[3].value).strip().rsplit("-", maxsplit=1)
        score = str(row[4].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, category, edition, score
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
        edition = str(row[4].value).strip()
        # NOTE: column is `CATEGORY - EDITION` in this version of the file
        category, _ = str(row[5].value).strip().rsplit("-", maxsplit=1)

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, category, edition, score
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
        edition = str(row[4].value).strip()
        category = str(row[5].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal,
            issn,
            eissn,
            category,
            AIS_EDITION_NAMES.get(edition, edition),
            score,
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
        edition = str(row[3].value).strip()
        category = str(row[4].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, "N/A", category, edition, score
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
    if not filename.exists():
        raise FileNotFoundError(filename)

    if version not in UEFISCDI_DATABASE_URL:
        raise ValueError(f"unsupported database version: {version}")

    decrypted_filename = _decrypt_file(filename, UEFISCDI_DEFAULT_PASSWORD)
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
            edition TEXT NOT NULL,
            category TEXT NOT NULL,
            score REAL NOT NULL,
            UNIQUE(year, issn, eissn, edition, category)
        );
    """
    index: ClassVar[str] = f"""
        CREATE INDEX IF NOT EXISTS {name}_index
            ON {name} (year, issn, eissn, edition, category);
    """

    def find_by_issn_impl(self, text: ISSN, year: int) -> ArticleInfluenceScore | None:
        assert self.conn is not None
        result = self.conn.execute(
            f"""
            SELECT journal, issn, eissn, category, edition, score
            FROM {self.name}
            WHERE (issn = ? OR eissn = ?) AND year = ?
            """,  # noqa: S608
            (str(text), str(text), year),
        )

        from uvt_scholarly.wos import parse_wos_categories

        for journal, issn, eissn, category, edition, score in result.fetchall():
            return ArticleInfluenceScore(
                journal=journal,
                issn=ISSN.from_string(issn) if issn else None,
                eissn=ISSN.from_string(eissn) if eissn else None,
                edition=Edition[edition],
                category=parse_wos_categories(category)[0],
                score=score,
            )

        return None


def store_article_influence_score(
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

    with ArticleInfluenceScoreDatabase(filename) as db:
        for i, year in enumerate(years):
            url = UEFISCDI_DATABASE_URL[year][Score.AIS]

            xlsxfile = dirname / f"uvt-scholarly-AIS-{year}.xlsx"
            download_file(url, xlsxfile, force=force)

            log.info("Processing AIS scores for %d: '%s'.", year, xlsxfile)
            scores = parse_article_influence_score(xlsxfile, year)

            log.info("Inserting %d AIS scores for %d into database.", len(scores), year)
            db.insert(year, scores)

            if i != len(years) - 1:
                log.info("")


# }}}

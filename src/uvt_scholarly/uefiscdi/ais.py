# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger
from uvt_scholarly.uefiscdi.common import (
    UEFISCDI_DATABASE_URL,
    UEFISCDI_DEFAULT_PASSWORD,
    Index,
    Score,
    XLSXParser,
    normalize_issn,
    to_float,
)

if TYPE_CHECKING:
    from openpyxl.cell import ReadOnlyCell

    from uvt_scholarly.publication import Category

log = make_logger(__name__)


# {{{ parse_article_influence_score

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
AIS_INDEX_NAMES = {
    "SCIENCE": "SCIE",
    "SOCIAL SCIENCES": "SSCI",
}


@dataclass(frozen=True, slots=True)
class ArticleInfluenceScore(Score):
    index: Index
    category: tuple[Category, ...]

    def __hash__(self) -> int:
        return hash((self.issn, self.eissn, self.category, self.index))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return (
            self.issn == other.issn
            and self.eissn == other.eissn
            and self.index == other.index
        )

    @property
    def name(self) -> str:
        return f"AIS[{self.index.name}]"

    @staticmethod
    def from_strings(
        journal: str,
        issn: str,
        eissn: str,
        category: str,
        index: str,
        score: str,
    ) -> ArticleInfluenceScore:
        from uvt_scholarly.wos import parse_wos_categories

        issn = issn.strip().upper()
        eissn = eissn.strip().upper()

        # NOTE: some entries have "AHCI, SSCI" or something. Not quite sure why..
        if "," in index:
            index, _ = index.split(",", maxsplit=1)

        return ArticleInfluenceScore(
            journal=journal.strip(),
            issn=normalize_issn(AIS_INCORRECT_ISSN.get(issn, issn)),
            eissn=normalize_issn(AIS_INCORRECT_ISSN.get(eissn, eissn)),
            score=to_float(score),
            index=Index[index.strip().upper()],
            category=parse_wos_categories(category),
        )


class ArticleInfluenceScoreParser(XLSXParser[ArticleInfluenceScore]):
    def parse_row(  # noqa: PLR6301
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        if len(row) != 6:
            raise ValueError(f"unexpected number of columns: {len(row)} (expected 6)")

        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        category = str(row[3].value).strip()
        index = str(row[4].value).strip()
        score = str(row[5].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, category, index, score
        )


class ArticleInfluenceScore2023Parser(ArticleInfluenceScoreParser):
    def parse_row(  # noqa: PLR6301
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        if len(row) != 6:
            raise ValueError(f"unexpected number of columns: {len(row)} (expected 6)")

        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        # NOTE: column is `CATEGORY - INDEX` in this version of the file
        category, index = str(row[3].value).strip().rsplit("-", maxsplit=1)
        score = str(row[4].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, category, index, score
        )


class ArticleInfluenceScore2022Parser(ArticleInfluenceScoreParser):
    def parse_row(  # noqa: PLR6301
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        if len(row) != 7:
            raise ValueError(f"unexpected number of columns: {len(row)} (expected 7)")

        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[3].value).strip()
        index = str(row[4].value).strip()
        # NOTE: column is `CATEGORY - INDEX` in this version of the file
        category, _ = str(row[5].value).strip().rsplit("-", maxsplit=1)

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, category, index, score
        )


class ArticleInfluenceScore2021Parser(ArticleInfluenceScoreParser):
    def parse_row(  # noqa: PLR6301
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        if len(row) != 7:
            raise ValueError(f"unexpected number of columns: {len(row)} (expected 7)")

        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        eissn = str(row[2].value).strip()
        score = str(row[3].value).strip()
        index = str(row[4].value).strip()
        category = str(row[5].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, eissn, category, AIS_INDEX_NAMES.get(index, index), score
        )


class ArticleInfluenceScore2020Parser(ArticleInfluenceScoreParser):
    def parse_row(  # noqa: PLR6301
        self,
        row: tuple[ReadOnlyCell, ...],
    ) -> ArticleInfluenceScore | None:
        from openpyxl.cell.read_only import EmptyCell

        if len(row) != 6:
            raise ValueError(f"unexpected number of columns: {len(row)} (expected 6)")

        if isinstance(row[-1], EmptyCell):
            return None

        journal = str(row[0].value).strip()
        issn = str(row[1].value).strip()
        score = str(row[2].value).strip()
        index = str(row[3].value).strip()
        category = str(row[4].value).strip()

        return ArticleInfluenceScore.from_strings(
            journal, issn, "N/A", category, index, score
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

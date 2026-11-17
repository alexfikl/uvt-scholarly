# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

    from uvt_scholarly.identifiers import ISBN13

log = make_logger(__name__)

SENSE_URL = "https://sense.nl/wp-content/uploads/2021/03/WASS-SENSE_book_publishers_list_2020.xlsx"


# {{{ parse_sense_classification


@enum.unique
class PublisherCategory(enum.IntEnum):
    """SENSE category of a book publisher."""

    A = enum.auto()
    B = enum.auto()
    C = enum.auto()
    D = enum.auto()
    E = enum.auto()
    Z = enum.auto()
    Unlisted = enum.auto()


@dataclass(frozen=True, slots=True)
class Publisher:
    code: str
    name: str | None
    location: str | None
    year: int
    category: PublisherCategory

    def matches(self, isbn: ISBN13) -> bool:
        return str(isbn).startswith(self.code)


def _fix_windows_encoding(text: str) -> str:
    bs = bytearray()
    for c in text:
        try:
            bs += c.encode("cp1252")
        except UnicodeEncodeError:
            if ord(c) < 256:
                bs.append(ord(c))
            else:
                return text

    try:
        return bs.decode("utf-8")
    except UnicodeDecodeError:
        return text


def parse_sense_classification(filename: pathlib.Path) -> Sequence[Publisher]:
    import openpyxl

    wb = openpyxl.load_workbook(filename, read_only=True)
    if wb is None:
        raise ValueError(f"could not load workbook from file: '{filename}'")

    sheetname = "WASS-SENSE publishers"  # spell: disable
    if sheetname not in wb.sheetnames:
        raise ValueError(f"expected a sheet called '{sheetname}' in file: '{filename}'")
    ws = wb[sheetname]

    # NOTE: the format of these things seems to be something like
    #
    # XX | prefixMetCode | Code | Name | Location | Year | Category
    #    | 978...        | XXX  | ...  | ...      | ...  | A
    #
    # so we just iterate through them

    result: dict[str, Publisher] = {}
    for row in ws.iter_rows(min_row=7, max_col=7, values_only=True):
        if not row[0]:
            break

        code = str(row[1]).replace("-", "").strip()
        year = int(row[5])

        # if we already have a more recent entry, leave it
        if (entry := result.get(code)) and entry.year > year:
            continue

        # if the entry is Z, leave it so other code knows this is unlisted
        category = row[6].strip().upper()
        if category == "Z":
            continue

        # we have new entry
        name = name.strip() if (name := row[3]) else None
        if name is not None:
            name = _fix_windows_encoding(name)

        result[code] = Publisher(
            code=code,
            name=name,
            location=location.strip() if (location := row[4]) else None,
            year=year,
            category=PublisherCategory[category],
        )
        print(result[code].name)

    return tuple(sorted(result.values(), key=lambda v: v.category))


# }}}

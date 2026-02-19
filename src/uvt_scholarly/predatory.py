# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import TYPE_CHECKING

import httpx

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import ISSN

if TYPE_CHECKING:
    import pathlib

log = make_logger(__name__)

PREDATORY_PUBLISHER_URL = "https://beallslist.net/"
"""URL for a list of potential predatory publishers."""
PREDATORY_JOURNAL_URL = "https://beallslist.net/standalone-journals/"
"""URL for a list of potential predatory standalone journals."""

MDPI_JOURNAL_LIST_URL = "https://consortium.ch/mdpi_titlelist_publish"
"""Official URL for a list of all MDPI journals."""

# {{{ parser


class BeallParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()

        self.in_target_ul = False
        self.in_target_li = False
        self.current_href = None
        self.results = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "ul" and not attrs:
            self.in_target_ul = True

        if self.in_target_ul and tag == "li":
            self.in_target_li = True

        if self.in_target_li and tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.current_href = value
                    break

    def handle_data(self, data: str) -> None:
        if self.current_href:
            if "(" in data:
                data, _ = data.split("(", maxsplit=1)

            # FIXME: there's an extra remark at the end with mdpi that we want
            # to skip. There's probably a smarter way to do that..
            if "mdpi" not in self.current_href:
                self.results.append((data.strip(), self.current_href))

            # NOTE: we only want to parse one href from each list item
            self.in_target_li = False
            self.current_href = None

    def handle_endtag(self, tag: str) -> None:
        if self.in_target_ul and tag == "li":
            self.in_target_li = False

        if tag == "ul":
            self.in_target_ul = False


# }}}

# {{{ parse_beall_publishers


@dataclass(frozen=True)
class Publisher:
    name: str
    url: str

    def __str__(self) -> str:
        return f"{self.name} ({self.url})"


def parse_beall_publishers(client: httpx.Client | None = None) -> tuple[Publisher, ...]:
    if client:
        response = client.get(PREDATORY_PUBLISHER_URL)
    else:
        with httpx.Client(timeout=5) as c:
            response = c.get(PREDATORY_PUBLISHER_URL)

    response.raise_for_status()
    text = response.text

    parser = BeallParser()
    parser.feed(text)

    return tuple(Publisher(name, url) for name, url in parser.results)


# }}}


# {{{ parse_beall_journals


@dataclass(frozen=True)
class Journal:
    name: str
    url: str
    issn: ISSN | None

    def __str__(self) -> str:
        return f"{self.name} ({self.url})"


def parse_beall_journals(client: httpx.Client | None = None) -> tuple[Journal, ...]:
    if client:
        response = client.get(PREDATORY_JOURNAL_URL)
    else:
        with httpx.Client(timeout=5) as c:
            response = c.get(PREDATORY_JOURNAL_URL)

    response.raise_for_status()
    text = response.text

    parser = BeallParser()
    parser.feed(text)

    return tuple(Journal(name, url, issn=None) for name, url in parser.results)


# }}}


# {{{ parse_mdpi_journals


def parse_mdpi_journals(filename: pathlib.Path) -> tuple[Journal, ...]:
    if not filename.exists():
        raise FileNotFoundError(filename)

    import openpyxl

    wb = openpyxl.load_workbook(filename, read_only=True)
    if wb is None:
        raise ValueError(f"could not load workbook from file: '{filename}'")

    result = []
    for row in wb.active.iter_rows(min_row=13, max_col=3, values_only=True):
        if row[0] is None:
            break

        issn = ISSN.from_string(row[1])
        if not issn.is_valid:
            log.warning("Journal '%s' does not have a valid ISSN: '%s'", row[0], issn)
            continue

        result.append(Journal(row[0], row[2], issn))

    return tuple(result)


# }}}

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

import httpx

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)

PREDATORY_PUBLISHER_URL = "https://beallslist.net/"
"""URL for a list of potential predatory publishers."""
PREDATORY_JOURNAL_URL = "https://beallslist.net/standalone-journals/"
"""URL for a list of potential predatory standalone journals."""

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

    return tuple(Journal(name, url) for name, url in parser.results)


# }}}

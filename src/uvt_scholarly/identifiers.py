# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass

import httpx

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


# {{{ DOI

DOI_RESOLVER: str = "https://doi.org"
"""Default resolver for the [DOI][] class."""


def _lowercase_ascii(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


@dataclass(frozen=True, slots=True)
class DOI:
    """A parsed [Digital Object Identifier](https://en.wikipedia.org/wiki/Digital_object_identifier).

    The DOI has a standard form `NN.RRRR/suffix`, where the first part is the
    [namespace][], the second part is the [registrant][] and the last part is
    the [item][] suffix.

    !!! info

        When comparing two DOIs for equality, the suffix partially compares in
        a case-insensitive way. In particular, all ASCII letters from the
        suffix are considered to be case-insensitive, but other Unicode letters
        are compared in a case-sensitive fashion.
    """

    namespace: str
    """The namespace for the identifier. This is usually `10` for scientific
    publications."""
    registrant: str
    """The registrant for this identifier. There is no official list of all
    registrants, but some information can be obtained, e.g., from Crossref by
    querying `https://api.crossref.org/prefixes/10.1038`.
    """
    item: str
    """The unique identifier for this item."""

    def __str__(self) -> str:
        return f"{self.namespace}.{self.registrant}/{self.item}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"

    def display(self) -> str:
        """A display string for the DOI (recommended by the DOI Foundation)."""
        return f"doi:{self}"

    @property
    def url(self) -> str:
        """A URL for the DOI using a supported resolver."""
        from urllib.parse import quote

        suffix = quote(self.item, safe="")
        return f"{DOI_RESOLVER}/{self.namespace}.{self.registrant}/{suffix}"

    def __hash__(self) -> int:
        return hash((self.namespace, self.registrant, _lowercase_ascii(self.item)))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        if self is other:
            return True

        # NOTE: according to the DOI Handook, Section 3.4.4, two DOIs are considered
        # equivalent is the codepoints are the same, except ASCII letters, which
        # are case-insensitive.
        return (
            self.namespace == other.namespace
            and self.registrant == other.registrant
            and _lowercase_ascii(self.item) == _lowercase_ascii(other.item)
        )

    @staticmethod
    def from_string(doi: str) -> DOI:
        """Convert some text into a [DOI][] instance.

        Some basic structural checks are performed on the input string to ensure
        that it can represents a `DOI` (e.g. length of parts).
        """

        if "/" not in doi:
            raise ValueError(f"DOI has a form 'prefix/suffix': {doi!r}")

        prefix, suffix = doi.split("/", maxsplit=1)
        if "." not in prefix:
            raise ValueError(f"DOI prefix must have a form '10.NNNN[N]': {doi!r}")

        namespace, registrant = prefix.split(".")
        if not (namespace == "10" and len(registrant) >= 4 and registrant.isdigit()):
            raise ValueError(f"DOI prefix must have a form '10.NNNN[N]': {doi!r}")

        # NOTE: according to the DOI Handbook, ASCII letters are case-insensitive
        # in a DOI, so we just lowercase them to begin with.
        return DOI(namespace, registrant, _lowercase_ascii(suffix))

    @property
    def is_valid(self) -> bool:
        """*True* if the DOI is valid.

        Note that this just checks the general format of the DOI, e.g. size,
        allowed characters, etc. The only official way to verify if a DOI is valid
        is to resolve it. This can be done using [resolve][], which effectively
        checks if [url][] is redirects successfully.
        """

        if self.namespace != "10":
            return False

        if len(self.registrant) < 4 or not self.registrant.isdigit():
            return False

        if not self.item:
            return False

        for ch in self.item:
            if ch.isspace():
                return False

            # also reject ASCII control sequences
            if ord(ch) < 32 or ord(ch) == 127:
                return False

        # NOTE: this just validates the form of the DOI. To truly know if a DOI
        # is valid, we have to resolve it through doi.org or something.
        return True

    def resolve(self, client: httpx.Client | None = None) -> bool:
        """
        Parameters:
            client: A client used for the HTTP request. This function
                automatically creates a client if none is provided. However, if
                checking many DOIs at once, it is recommended to create a client,
                so that requests can be handled more efficiently.

        Returns:
            *True* if the current DOI redirects correctly.
        """
        # TODO: we should cache this result and just return it on the next call

        if not self.is_valid:
            return False

        try:
            if client:
                if not client.follow_redirects:
                    raise ValueError(
                        "'resolve' requires a client with follow_redirects=True"
                    )

                response = client.head(self.url)
            else:
                with httpx.Client(follow_redirects=True, timeout=5.0) as c:
                    response = c.head(self.url)

            return response.status_code == 200
        except httpx.HTTPError:
            return False


# }}}


# {{{ ISSN


@dataclass(frozen=True, slots=True)
class ISSN:
    """A parsed [International Standard Serial Number](https://en.wikipedia.org/wiki/ISSN)."""

    parts: tuple[str, str]
    """The two parts of the ISSN, which generally has the form `NNNN-NNNC`."""

    def __str__(self) -> str:
        return f"{self.parts[0]}-{self.parts[1]}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"

    @staticmethod
    def from_string(issn: str) -> ISSN:
        """Convert some text into an [ISSN][] instance.

        Some basic structural checks are performed on the input string to ensure
        that it can represents a `ISSN` (e.g. length of parts).
        """

        if "-" not in issn:
            raise ValueError(f"ISSN missing dash (expected NNNN-NNNC): {issn!r}")

        if len(issn) != 9:
            raise ValueError(f"invalid ISSN length (expected NNNN-NNNC): {issn!r}")

        part0, part1 = issn.split("-", maxsplit=1)
        if len(part0) != 4 or len(part1) != 4:
            raise ValueError(f"invalid ISSN part size (expected NNNN-NNNC): {issn!r}")

        # NOTE: we let the user check if this is a valid ISSN otherwise, since
        # they might want to just construct some for fun and games
        return ISSN((part0, part1))

    @property
    def is_valid(self) -> bool:
        """*True* if the ISSN is valid."""

        issn = f"{self.parts[0]}{self.parts[1]}"
        if len(issn) != 8:
            return False

        # NOTE: verify the "check" digit in the ISSN:
        #   https://en.wikipedia.org/wiki/ISSN#Code_format

        total = 0
        for i in range(7):
            if not issn[i].isdigit():
                return False

            total += int(issn[i]) * (8 - i)

        check = 11 - (total % 11)
        if check == 11:
            expected = "0"
        elif check == 10:
            expected = "X"
        else:
            expected = str(check)

        return issn[-1] == expected


# }}}


# {{{ ORCiD


@dataclass(frozen=True, slots=True)
class ORCiD:
    """A parsed [ORCiD](https://en.wikipedia.org/wiki/ORCID)."""

    parts: tuple[str, str, str, str]
    """The four parts of the ORCiD, which generally has the form
    `NNNN-NNNN-NNNN-NNNN`.
    """

    def __str__(self) -> str:
        return "-".join(self.parts)

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"

    @staticmethod
    def from_string(orcid: str) -> ORCiD:
        """Convert some text into an [ORCiD][] instance.

        Some basic structural checks are performed on the input string to ensure
        that it can represents a `ORCiD` (e.g. length of parts).
        """

        if "-" not in orcid:
            raise ValueError(
                f"no dash in ORCiD (format NNNN-NNNN-NNNN-NNNN): {orcid!r}"
            )

        parts = [part.strip().upper() for part in orcid.split("-")]
        if len(parts) != 4:
            raise ValueError(
                f"incorrect parts in ORCiD (format NNNN-NNNN-NNNN-NNNN): {orcid!r}"
            )

        if any(len(part) != 4 for part in parts):
            raise ValueError(
                f"incorrect part sizes in ORCiD (format NNNN-NNNN-NNNN-NNNN): {orcid!r}"
            )

        return ORCiD((parts[0], parts[1], parts[2], parts[3]))

    @property
    def is_valid(self) -> bool:
        """*True* if the [ORCiD][] is valid."""

        if any(len(part) != 4 for part in self.parts):
            return False

        if not (
            self.parts[0].isdigit()
            and self.parts[1].isdigit()
            and self.parts[2].isdigit()
            and self.parts[3][:-1].isdigit()
        ):
            return False

        check = self.parts[3][-1].upper()
        if not (check.isdigit() or check == "X"):
            return False

        total = 0
        digits = "".join(self.parts)
        for ch in digits[:-1]:
            total = 2 * (total + int(ch))

        remainder = total % 11
        result = (12 - remainder) % 11
        expected = "X" if result == 10 else str(result)

        return check == expected


# }}}


# {{{ ResearcherID


@dataclass(frozen=True, slots=True)
class ResearcherID:
    """A parsed [ResearcherID](https://en.wikipedia.org/wiki/ResearcherID)."""

    parts: tuple[str, str, str]
    """The three parts of the ResearcherID, which generally has the form
    `X[XX]-NNNN-NNNN`, which an ASCII letter as the first part and two 4-digit
    numeric identifiers.
    """

    def __str__(self) -> str:
        return "-".join(self.parts)

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"

    @staticmethod
    def from_string(rid: str) -> ResearcherID:
        """Convert some text into a [ResearcherID][] instance.

        Some basic structural checks are performed on the input string to ensure
        that it can represents a `ResearcherID` (e.g. length of parts).
        """

        if "-" not in rid:
            raise ValueError(
                f"no dash in ResearcherID (format X[XX]-NNNN-NNNN): {rid!r}"
            )

        parts = [part.strip().upper() for part in rid.upper().split("-")]
        if len(parts) != 3:
            raise ValueError(
                f"incorrect parts in ResearcherID (format X[XX]-NNNN-NNNN): {rid!r}"
            )

        if not (len(parts[0]) >= 1 and len(parts[1]) == 4 and len(parts[2]) == 4):
            raise ValueError(
                f"incorrect part size in ResearcherID (format X[XX]-NNNN-NNNN): {rid!r}"
            )

        return ResearcherID((parts[0], parts[1], parts[2]))

    @property
    def year(self) -> int:
        """The year the `ResearcherID` was registered. This is only the last 4 digits
        of the identifier.
        """
        return int(self.parts[-1])

    @property
    def is_valid(self) -> bool:
        """*True* if the [ResearcherID][] is valid.

        Note that there is no standardized format for the `ResearcherID`, so this
        validation should be taken with a grain of salt. It mainly checks that
        values found in the wild are considered valid.
        """

        if not (
            len(self.parts[0]) >= 1
            and len(self.parts[1]) == 4
            and len(self.parts[2]) == 4
        ):
            return False

        if not all("A" <= ch <= "Z" for ch in self.parts[0]):
            return False

        if not (self.parts[1].isdigit() and self.parts[2].isdigit()):
            return False

        from datetime import datetime

        # NOTE: the last part of the ResearcherID should represent the year. Given
        # that it started in 2008, we do not expect to see earlier values there.
        year = int(self.parts[2])
        return 2008 <= year < datetime.now().year + 1


# }}}

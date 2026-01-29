# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


# {{{ test_issn

TEST_ISSN_VALID = (
    "0378-5955",
    "0028-0836",
    "0036-8075",
    "0006-808X",
    "0016-7568",
    "0022-1694",
    "0044-7447",
    "0264-9381",
    "0950-9232",
    "1234-5679",
)

TEST_ISSN_INVALID = (
    "0378-5954",
    "0028-0837",
    "0036-8074",
    "0006-8081",
    "1234-5678",
    "1234-567X",
    "123-45678",
    "12345-678",
    "ABCD-1234",
    "12345678",
)


def test_issn() -> None:
    from uvt_scholarly.publication import ISSN

    for value in TEST_ISSN_VALID:
        issn = ISSN.from_string(value)
        assert issn.is_valid
        assert str(issn) == value

    for value in TEST_ISSN_INVALID:
        try:
            issn = ISSN.from_string(value)
            is_valid = issn.is_valid
        except ValueError:
            is_valid = False

        assert not is_valid

    with pytest.raises(ValueError, match="missing dash"):
        ISSN.from_string("123456789")

    with pytest.raises(ValueError, match="invalid ISSN length"):
        ISSN.from_string("1234-123")

    with pytest.raises(ValueError, match="invalid ISSN part size"):
        ISSN.from_string("123-A123A")


# }}}


# {{{ test_doi

TEST_DOI_VALID = (
    "10.1000/182",
    "10.1000/xyz123",
    "10.1016/j.cell.2019.05.001",
    "10.1038/nphys1170",
    "10.1126/science.169.3946.635",
    "10.1093/mind/LIX.236.433",
    "10.1007/s00134-020-06050-2",
    "10.1145/3375637.3392412",
    "10.1371/journal.pone.0152612",
    "10.1080/02626667.2018.1560449",
    "10.1000/<>?",
    "10.1000//1234",
)

TEST_DOI_INVALID = (
    "11.1000/182",
    "10.abc/12345",
    "10.1000",
    "10.1000\182",
    "10.1000/",
    "10./12345",
    "doi:10.1000/182",
    "10.1000/white space",
)


def test_doi() -> None:
    from uvt_scholarly.publication import DOI, _lowercase_ascii  # noqa: PLC2701

    for value in TEST_DOI_VALID:
        doi = DOI.from_string(value)
        assert str(doi) == _lowercase_ascii(value)
        assert doi.display() == f"doi:{_lowercase_ascii(value)}"

    for value in TEST_DOI_INVALID:
        try:
            doi = DOI.from_string(value)
            is_valid = doi.is_valid
        except ValueError:
            is_valid = False

        assert not is_valid, value

    with pytest.raises(ValueError, match="prefix/suffix"):
        DOI.from_string("10.1000")

    with pytest.raises(ValueError, match="prefix must have a form"):
        DOI.from_string("101000/12345")

    with pytest.raises(ValueError, match="prefix must have a form"):
        DOI.from_string("11.1000/12345")

    with pytest.raises(ValueError, match="prefix must have a form"):
        DOI.from_string("11.10000/12345")

    with pytest.raises(ValueError, match="prefix must have a form"):
        DOI.from_string("11.1A000/12345")

    doi = DOI.from_string("10.1000/<>?")
    assert doi.url == "https://doi.org/10.1000/%3C%3E%3F"

# }}}

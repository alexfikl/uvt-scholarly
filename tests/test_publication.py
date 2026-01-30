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

        assert not is_valid, value

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


# {{{ test_researcherid

TEST_RESEARCHERID_VALID = (
    "A-1234-2008",
    "B-9876-2012",
    "Z-0001-2015",
    "AB-4321-2019",
    "XY-8080-2020",
    "IWL-8088-2023",
    "QRS-1000-2010",
    "T-5555-2018",
    "MN-2468-2016",
    "KLM-9999-2024",
)

TEST_RESEARCHERID_INVALID = (
    "A-123-2019",
    "A-12345-2019",
    "A-1234-1999",
    "A1234-2019",
    "A-1234-19",
    "A-1234-201X",
    "12-1234-2019",
    "A--1234-2019",
)


def test_researcherid() -> None:
    from uvt_scholarly.publication import ResearcherID

    for value in TEST_RESEARCHERID_VALID:
        rid = ResearcherID.from_string(value)
        assert str(rid) == value

    for value in TEST_RESEARCHERID_INVALID:
        try:
            doi = ResearcherID.from_string(value)
            is_valid = doi.is_valid
        except ValueError:
            is_valid = False

        assert not is_valid, value

    with pytest.raises(ValueError, match="no dash"):
        ResearcherID.from_string("A00002009")

    with pytest.raises(ValueError, match="incorrect parts"):
        ResearcherID.from_string("A-2009")

    with pytest.raises(ValueError, match="incorrect part size"):
        ResearcherID.from_string("A-203-2009")


# }}}


# {{{ test_orcid

TEST_ORCID_VALID = (
    "0000-0002-1825-0097",
    "0000-0001-5109-3700",
    "0000-0002-1694-233X",
    "0000-0003-1419-2405",
    "0000-0002-9079-593X",
    "0000-0001-0000-0007",
    "0000-0001-2345-6789",
    "0000-0002-0000-0015",
    "0000-0003-0000-0006",
    "0000-0001-9999-9991",
)

TEST_ORCID_INVALID = (
    # invalid checksums
    "0000-0002-1825-0098",
    "0000-0001-5109-3701",
    "0000-0002-1694-2339",
    "0000-0003-1419-2400",
    "0000-0001-0000-0000",
    "0000-0002-1825-009x",
    # invalid format
    "0000-0002-1825-009",
    "0000-0002-1825-00977",
    "0000-0002-1825-00A7",
    "0000000218250097",
)


def test_orcid() -> None:
    from uvt_scholarly.publication import ORCiD

    for value in TEST_ORCID_VALID:
        orcid = ORCiD.from_string(value)
        assert str(orcid) == value

    for value in TEST_ORCID_INVALID:
        try:
            orcid = ORCiD.from_string(value)
            is_valid = orcid.is_valid
        except ValueError:
            is_valid = False

        assert not is_valid, value

    with pytest.raises(ValueError, match="no dash"):
        ORCiD.from_string("0000000100000000")

    with pytest.raises(ValueError, match="incorrect parts"):
        ORCiD.from_string("0000-0001-0000")

    with pytest.raises(ValueError, match="incorrect part sizes"):
        ORCiD.from_string("0000-0001-0000-000")

    # check case insensitive
    orcid = ORCiD.from_string("0000-0002-1694-233x")
    assert orcid.is_valid


# }}}

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

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
    from uvt_scholarly.identifiers import ISSN

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
    "10.10001/182",
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
    from uvt_scholarly.identifiers import DOI, _lowercase_ascii  # noqa: PLC2701

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
        DOI.from_string("10.1A000/12345")

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
    from uvt_scholarly.identifiers import ResearcherID

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
    from uvt_scholarly.identifiers import ORCiD

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


# {{{ test_arxiv

TEST_MODERN_ARXIV_VALID = (
    "0704.0001",  # First ever new-style ID (April 2007)
    "0709.4123",  # 4-digit sequence
    "1001.4538",  # 4-digit sequence
    "1507.04356",  # 5-digit sequence
    "2301.00001",  # Leading zeros in sequence
    "2312.99999",  # Max month, large sequence
    "2403.12345",  # Typical recent ID
    "0704.0001v1",  # Version 1 suffix
    "2301.12345v2",  # Version 2 suffix
    "2210.07032v14",  # High version number
)

TEST_MODERN_ARXIV_INVALID = (
    "0701.1234",  # Modern IDs start from 0704
    "2300.1234",  # Month 00 is not valid
    "2313.1234",  # Month 13 is not valid
    "1001.45381",  # 5-digit sequence in a 4-digit year
    "1507.0435",  # 4-digit sequence in a 5-digit year
    "2301.123",  # Sequence number too short (only 3 digits; minimum is 4)
    "2301.123456",  # Sequence number too long (6 digits; maximum is 5)
    "230112345",  # Missing the . separator
    "2301.1234v0",  # Version 0 is not valid (must be >= 1)
    "2301.1234v",  # Version suffix has no number
    "2301.1234v1.5",  # Version is not an integer
    "abcd.1234",  # Non-numeric YYMM field
    "2301.abcd",  # Non-numeric sequence field
)

TEST_LEGACY_ARXIV_VALID = (
    "hep-th/9210001",  # Early hep-th paper, 3-digit sequence
    "math/0309136",  # Math archive, no subcategory
    "cond-mat/9901001",  # Condensed matter
    "quant-ph/0601001",  # Quantum physics (no subcategory ever used)
    "hep-ph/0512001",  # Hep phenomenology
    "cs/0401001",  # CS archive, no subcategory
    "math.AG/0101001",  # Math with algebraic geometry subcategory
    "cond-mat.str-el/0601001",  # Cond-mat with strongly-correlated subcategory
    "astro-ph/9912001",  # Astrophysics
    "gr-qc/0401001",  # General relativity & quantum cosmology
)

TEST_LEGACY_ARXIV_INVALID = (
    "hep-th/9200001",  # Month 00 is not valid
    "hep-th/9213001",  # Month 13 is not valid
    # "hep/9210001",  # hep alone is not a valid archive name
    "hep-th/921001",  # Sequence number too short (2 digits after YYMM)
    "9210001",  # Missing archive prefix entirely
    "hep-th/9210",  # Missing sequence number
    "hep-th/9210001v0",  # Version 0 is not valid (must be >= 1)
    "math.123/0101001",  # Subcategory must not be numeric
    "hep_th/9210001",  # Underscore instead of hyphen in archive name
)


@pytest.mark.parametrize(
    ("valid_ids", "invalid_ids"),
    [
        (TEST_MODERN_ARXIV_VALID, TEST_MODERN_ARXIV_INVALID),
        (TEST_LEGACY_ARXIV_VALID, TEST_LEGACY_ARXIV_INVALID),
    ],
)
def test_arxiv(valid_ids: tuple[str, ...], invalid_ids: tuple[str, ...]) -> None:
    from uvt_scholarly.identifiers import LegacyArXiv, ModernArXiv, arXiv

    for value in valid_ids:
        arxivid = arXiv.from_string(value)
        assert arxivid.is_valid, value
        assert str(arxivid) == value

        if arxivid.archive is None:
            assert isinstance(arxivid, ModernArXiv)
        else:
            assert isinstance(arxivid, LegacyArXiv)

    for value in invalid_ids:
        try:
            arxivid = arXiv.from_string(value)
            is_valid = arxivid.is_valid
        except ValueError:
            is_valid = False

        assert not is_valid, value


# }}}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

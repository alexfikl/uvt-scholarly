# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from uvt_scholarly.export.common import POSITION_NAME, Position
from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import (
    Author,
    DocumentType,
    Grant,
    Publication,
    ScoreType,
)

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence


log = make_logger(__name__)


# {{{ utils

MIN_AIS_SCORE = 0
"""The minimum score allowed for publications by the Mathematics Department."""

PAST_YEAR_CUTOFF = 5
"""The span over which the AIS should be considered. The presented score is
a maximum over this period.
"""

RECENT_YEAR_CUTOFF = 7
"""The span over which the publication is considered as *RECENT*."""


def _format_author(au: Author) -> str:
    if au.first_name is not None:
        return f"{au.first_name[0]}. {au.last_name}"
    else:
        return f"{au.last_name}"


def filter_latex_format_pub(pub: Publication, candidate: str) -> str:
    from pylatexenc.latexencode import UnicodeToLatexEncoder

    u2l = UnicodeToLatexEncoder(
        unknown_char_policy="ignore",
        unknown_char_warning=False,
    )
    encode = u2l.unicode_to_latex

    parts: list[str] = []

    # authors
    authors = ", ".join(
        (
            rf"\textbf{{{_format_author(au)}}}"
            # FIXME: this isn't a great check. It already failed once
            if au.last_name in candidate.split()
            else _format_author(au)
        )
        for au in pub.authors
    )
    parts.append(authors)

    # title
    parts.append(rf"\enquote{{{encode(pub.title)}}}")

    # journal
    parts.append(rf"\textit{{{encode(pub.journal)}}}")

    # volume + year
    if pub.volume:
        parts.append(rf"vol.\ {pub.volume} ({pub.year})")
    else:
        parts.append(f"{pub.year}")

    if pages := str(pub.pages):
        if pub.pages.end is not None:
            parts.append(rf"pp.\ {pages}")
        else:
            parts.append(rf"art. no.\ {pub.pages.start}")

    # doi
    if pub.doi:
        doi = encode(str(pub.doi))
        parts.append(
            rf"\href{{https://doi.org/{pub.doi}}}{{\bfseries\ttfamily doi:{doi}}}"
        )

    return ", ".join(parts)


def filter_latex_format_book(pub: Publication, candidate: str) -> str:
    from pylatexenc.latexencode import UnicodeToLatexEncoder

    u2l = UnicodeToLatexEncoder(
        unknown_char_policy="ignore",
        unknown_char_warning=False,
    )
    encode = u2l.unicode_to_latex

    parts: list[str] = []

    # authors
    authors = ", ".join(
        (
            rf"\textbf{{{_format_author(au)}}}"
            # FIXME: this isn't a great check. It already failed once
            if au.last_name in candidate.split()
            else _format_author(au)
        )
        for au in pub.authors
    )
    parts.append(authors)

    # title + year
    parts.append(rf"\enquote{{{encode(pub.title)}}} ({pub.year})")

    # publisher
    parts.append(rf"\textit{{{encode(pub.journal)}}}")

    if pub.isbn:
        parts.append(f"ISBN:{pub.isbn}")

    return ", ".join(parts)


def filter_latex_format_grant(grant: Grant) -> str:
    parts = []

    # name + identifier + funder + period
    parts.extend([
        rf"\textbf{{{grant.name}}}",
        f"Contract: {grant.identifier}",
        rf"\textit{{{grant.funder}}}",
        (
            f"{grant.period[0]}--{grant.period[1]}"
            if grant.period[0] != grant.period[1]
            else f"{grant.period[0]}"
        ),
        rf"Poziție: \textbf{{{grant.position}}}",
    ])

    if grant.budget:
        parts.append(f"Budget: approx. {grant.budget}")

    if grant.url:
        parts.append(rf"(\href{{{grant.url}}}{{LINK}})")

    return ", ".join(parts)


def filter_csv_format_pub(pub: Publication) -> str:
    parts: list[str] = []

    # authors
    authors = ", ".join(_format_author(au) for au in pub.authors)
    parts.append(authors)

    # title
    parts.append(pub.title)

    # journal
    parts.append(f"{pub.journal}")

    # volume + year
    if pub.volume:
        parts.append(f"vol. {pub.volume} ({pub.year})")
    else:
        parts.append(f"{pub.year}")

    if pages := str(pub.pages):
        parts.append(f"pp. {pages}".replace("--", "-"))

    # doi
    if pub.doi:
        parts.append(f"DOI: {pub.doi}")

    return ", ".join(parts)


def filter_latex_is_recent(pub: Publication) -> str:
    from datetime import datetime

    seven_years_ago = datetime.now().year - RECENT_YEAR_CUTOFF
    return r"\textbf{X}" if pub.year >= seven_years_ago else ""


def filter_get_score(pub: Publication, name: str) -> float:
    try:
        score = ScoreType[name]
    except KeyError:
        return -1.0

    try:
        return pub.journal.scores[score]
    except KeyError:
        return 0


def filter_get_average_score(pub: Publication, name: str) -> float:
    return filter_get_score(pub, name) / len(pub.authors)


# }}}

# {{{ criteria


@dataclass(frozen=True)
class Criteria:
    position: Position
    min_ais: float
    min_recent_ais: float
    min_citations: int
    min_c1_uvt_books: int
    min_c2_uvt_courses: int
    min_c3_uvt_projects: int
    min_c4_uvt_publications: int
    min_c5_uvt_recommendations: int

    @property
    def position_name(self) -> str:
        return POSITION_NAME[self.position]


MIN_CRITERIA_FOR_POSITION = {
    # academic
    Position.Professor: Criteria(Position.Professor, 5.0, 2.5, 12, 2, 1, 2, 0, 2),
    Position.AssociateProfessor: Criteria(
        Position.AssociateProfessor, 2.5, 1.5, 6, 1, 1, 1, 0, 2
    ),
    Position.AssistantProfessor: Criteria(
        Position.AssistantProfessor, 1.0, 0.0, 0, 0, 0, 0, 5, 2
    ),
    Position.Assistant: Criteria(Position.Assistant, 0.0, 0.0, 0, 0, 0, 0, 3, 2),
    # research
    Position.SeniorResearcher: Criteria(
        Position.SeniorResearcher, 5.0, 2.5, 12, 2, 1, 2, 0, 2
    ),
    Position.Researcher: Criteria(Position.Researcher, 2.5, 1.5, 6, 1, 1, 1, 0, 2),
    Position.JuniorResearcher: Criteria(
        Position.JuniorResearcher, 1.0, 0.0, 0, 0, 0, 0, 5, 2
    ),
}


# }}}


# {{{ candidate

AVERAGED_AIS_POSITIONS = {
    Position.Professor,
    Position.AssociateProfessor,
    Position.Assistant,
    Position.SeniorResearcher,
    Position.Researcher,
}


@dataclass(frozen=True)
class Candidate:
    qualname: str

    ais: float
    recent_ais: float
    total_citations: int

    books: Sequence[Publication]
    courses: Sequence[Publication]
    publications: Sequence[Publication]
    grants: Sequence[Grant]

    @property
    def c1_uvt_books(self) -> int:
        return len(self.books)

    @property
    def c2_uvt_courses(self) -> int:
        return len(self.courses)

    @property
    def c3_uvt_grants(self) -> int:
        return len(self.grants)

    @property
    def c4_uvt_publications(self) -> int:
        return len(self.publications)

    @property
    def c5_uvt_recommendations(self) -> int:
        return 2


def sortedpubs(pubs: Sequence[Publication]) -> tuple[Publication, ...]:
    return tuple(
        sorted(
            pubs,
            key=lambda p: (p.year, p.journal.scores.get(ScoreType.AIS, 0)),
            reverse=True,
        )
    )


def make_candidate(
    name: str,
    pubs: Sequence[Publication],
    grants: Sequence[Grant],
    *,
    position: Position = Position.Professor,
) -> Candidate:
    from datetime import datetime

    recent_year_cutoff = datetime.now().year - RECENT_YEAR_CUTOFF

    total_ais = 0.0
    recent_total_ais = 0.0
    total_citations = 0

    books = []
    courses = []
    publications = []
    for pub in pubs:
        if pub.dtype == DocumentType.Book:
            books.append(pub)
        elif pub.dtype == DocumentType.Report:
            courses.append(pub)
        else:
            ais = pub.journal.scores.get(ScoreType.AIS)
            if ais is None:
                log.warning("Journal does not have a AIS score: '%s'.", pub.journal)
                ais = 0

            if ais < MIN_AIS_SCORE:
                log.warning(
                    "Journal AIS '%.3f' < %.3f: '%s'.", ais, MIN_AIS_SCORE, pub.journal
                )
                ais = 0

            if position in AVERAGED_AIS_POSITIONS:
                ais /= len(pub.authors)

            total_ais += ais
            if pub.year >= recent_year_cutoff:
                recent_total_ais += ais

            cited_by = []
            if ais != 0:
                for cite in pub.cited_by:
                    ais = cite.journal.scores.get(ScoreType.AIS)
                    if ais is None or ais < MIN_AIS_SCORE:
                        continue

                    if any(au.last_name in name for au in cite.authors):
                        log.warning(
                            "Self-citation for publication '%s': '%s'.",
                            pub.doi,
                            cite.title,
                        )
                        continue

                    total_citations += 1
                    cited_by.append(cite)

            publications.append(
                replace(
                    pub,
                    cited_by=sortedpubs(cited_by),
                    cited_by_count=len(cited_by),
                )
            )

    return Candidate(
        qualname=name,
        ais=total_ais,
        recent_ais=recent_total_ais,
        total_citations=total_citations,
        books=tuple(books),
        courses=tuple(courses),
        publications=sortedpubs(publications),
        grants=tuple(sorted(grants, key=lambda g: g.period[1], reverse=True)),
    )


# }}}


# {{{ export_publications_csv

PUBLICATION_FIELD_NAMES = (
    "Nr. Crt.",
    "Articol - referință bibliografică",
    "Publicat în ultimii 7 ani",
    "SRI revistă",
    "Nr. autori",
    "Scor",
)

CITATION_FIELD_NAMES = (
    "Nr. Crt.",
    "Articol citat",
    "Revista și articolul în care a fost citat",
    "SRI revistă",
)


def export_publications_csv(
    filename: pathlib.Path,
    candidate_name: str,
    pubs: Sequence[Publication],
    grants: Sequence[Grant],
    *,
    position: Position = Position.Professor,
    encoding: str = "utf-8",
    dialect: str = "excel",
    overwrite: bool = False,
) -> None:
    if not overwrite and filename.exists():
        raise FileExistsError(filename)

    import csv
    from datetime import datetime

    seven_years_ago = datetime.now().year - RECENT_YEAR_CUTOFF
    candidate = make_candidate(candidate_name, pubs, grants, position=position)

    with open(filename, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            PUBLICATION_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        for i, pub in enumerate(candidate.publications):
            ais = pub.journal.scores[ScoreType.AIS]
            if position in AVERAGED_AIS_POSITIONS:
                ais_per_author = ais / len(pub.authors)
            else:
                ais_per_author = ais

            writer.writerow(
                dict(
                    zip(
                        PUBLICATION_FIELD_NAMES,
                        [
                            str(i + 1),
                            filter_csv_format_pub(pub),
                            "X" if pub.year >= seven_years_ago else "",
                            f"{ais:.3f}",
                            str(len(pub.authors)),
                            f"{ais_per_author:.3f}",
                        ],
                        strict=True,
                    )
                )
            )

        writer.writerow({
            PUBLICATION_FIELD_NAMES[1]: "Total",
            PUBLICATION_FIELD_NAMES[3]: f"S = {candidate.ais:.3f}",
            PUBLICATION_FIELD_NAMES[5]: f"S_recent = {candidate.recent_ais:.3f}",
        })

    filename = filename.with_stem(f"{filename.stem}.cites")
    with open(filename, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            CITATION_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        i = 0
        for pub in candidate.publications:
            for j, cited_by in enumerate(pub.cited_by):
                ais = cited_by.journal.scores[ScoreType.AIS]

                i += 1
                writer.writerow(
                    dict(
                        zip(
                            CITATION_FIELD_NAMES,
                            [
                                str(i),
                                filter_csv_format_pub(pub) if j == 0 else "",
                                filter_csv_format_pub(cited_by),
                                f"{ais:.3f}",
                            ],
                            strict=True,
                        )
                    )
                )

        writer.writerow({
            CITATION_FIELD_NAMES[1]: "Total",
            CITATION_FIELD_NAMES[3]: f"C = {candidate.total_citations}",
        })


# }}}


# {{{ export_publications_latex


def export_publications_latex(
    outfile: pathlib.Path,
    candidate_name: str,
    pubs: Sequence[Publication],
    grants: Sequence[Grant],
    *,
    position: Position = Position.Professor,
    overwrite: bool = False,
) -> None:
    if not overwrite and outfile.exists():
        raise FileExistsError(outfile)

    # {{{ set up jinja environment

    import jinja2

    env = jinja2.Environment(  # ruff:ignore[jinja2-autoescape-false]
        block_start_string=r"\TplBlock{",
        block_end_string="}",
        variable_start_string=r"\TplVar{",
        variable_end_string="}",
        comment_start_string="((=",
        comment_end_string="=))",
    )

    env.filters["format_pub"] = lambda pub: filter_latex_format_pub(pub, candidate_name)
    env.filters["format_book"] = lambda pub: filter_latex_format_book(
        pub, candidate_name
    )
    env.filters["format_grant"] = filter_latex_format_grant
    env.filters["is_recent"] = filter_latex_is_recent
    env.filters["get_score"] = filter_get_score

    if position in AVERAGED_AIS_POSITIONS:
        env.filters["get_average_score"] = filter_get_average_score
    else:
        env.filters["get_average_score"] = filter_get_score

    # }}}

    # {{{ render the template

    from importlib.resources import files

    criteria = MIN_CRITERIA_FOR_POSITION[position]
    candidate = make_candidate(candidate_name, pubs, grants, position=position)

    template_file = files("uvt_scholarly.resources").joinpath("math.tpl.tex")
    with template_file.open(encoding="utf-8") as f:
        tex = (
            env
            .from_string(f.read())
            .render(candidate=candidate, criteria=criteria)
            .strip()
        )

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(tex)

    # }}}


# }}}

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import Publication, Score

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence


log = make_logger(__name__)


# {{{ utils

MIN_RIS_SCORE = 0.5
"""The minimum score allowed for publications by the Mathematics Department."""

PAST_YEAR_CUTOFF = 5
"""The span over which the RIS should be considered. The presented score is
a maximum over this period.
"""

RECENT_YEAR_CUTOFF = 7
"""The span over which the publication is considered as *RECENT*."""


def filter_latex_format_pub(pub: Publication) -> str:
    from pylatexenc.latexencode import unicode_to_latex

    parts: list[str] = []

    # authors
    authors = ", ".join(f"{au.first_name[0]}. {au.last_name}" for au in pub.authors)
    parts.append(unicode_to_latex(authors))

    # title
    parts.append(unicode_to_latex(pub.title))

    # journal
    parts.append(rf"\textit{{{unicode_to_latex(pub.journal)}}}")

    # volume + year
    parts.append(f"vol. {pub.volume} ({pub.year})")
    if pages := str(pub.pages):
        parts.append(f"{pages}")

    # doi
    if pub.doi:
        doi = unicode_to_latex(str(pub.doi))
        parts.append(
            rf"DOI: \href{{https://doi.org/{pub.doi}}}{{\bfseries\ttfamily {doi}}}"
        )

    return ", ".join(parts)


def filter_csv_format_pub(pub: Publication) -> str:
    parts: list[str] = []

    # authors
    authors = ", ".join(f"{au.first_name[0]}. {au.last_name}" for au in pub.authors)
    parts.append(authors)

    # title
    parts.append(pub.title)

    # journal
    parts.append(f"{pub.journal}")

    # volume + year
    parts.append(f"vol. {pub.volume} ({pub.year})")
    if pages := str(pub.pages):
        parts.append(f"{pages}".replace("--", "-"))

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
        score = Score[name]
    except KeyError:
        return -1.0

    return pub.journal.scores[score]


def filter_get_average_score(pub: Publication, name: str) -> float:
    return filter_get_score(pub, name) / len(pub.authors)


# }}}

# {{{ position


@enum.unique
class Position(enum.Enum):
    Professor = enum.auto()
    AssociateProfessor = enum.auto()
    AssistantProfessor = enum.auto()
    Assistant = enum.auto()

    SeniorResearcher = enum.auto()
    Researcher = enum.auto()
    JuniorResearcher = enum.auto()


POSITION_NAME = {
    # academic
    Position.Professor: "Profesor Universitar",  # spell: disable
    Position.AssociateProfessor: "Conferențiar",
    Position.AssistantProfessor: "Lector",
    Position.Assistant: "Asistent Universitar",
    # research
    Position.SeniorResearcher: "Cercetător Științific I",
    Position.Researcher: "Cercetător Științific II",
    Position.JuniorResearcher: "Cercetător Științific III",
}

POSITION_SHORT_NAME = {
    Position.Professor: "Prof. Dr.",
    Position.AssociateProfessor: "Conf. Dr.",
    Position.AssistantProfessor: "Lect. Dr.",
    Position.Assistant: "Ass.",
    # research
    Position.SeniorResearcher: "C.S. I",
    Position.Researcher: "C.S. II",
    Position.JuniorResearcher: "C.S. III",
}

ID_TO_POSITION = {
    "prof": Position.Professor,
    "conf": Position.AssociateProfessor,
    "lect": Position.AssistantProfessor,
    "assi": Position.Assistant,
    "cs1": Position.SeniorResearcher,
    "cs2": Position.Researcher,
    "cs3": Position.JuniorResearcher,
}

# }}}


# {{{ criteria


@dataclass(frozen=True)
class Criteria:
    position: Position
    min_ris: float
    min_recent_ris: float
    min_citations: int

    @property
    def position_name(self) -> str:
        return POSITION_NAME[self.position]


MIN_INDICATOR_FOR_POSITION = {
    # academic
    Position.Professor: (5.0, 2.5, 12),
    Position.AssociateProfessor: (2.5, 1.5, 6),
    Position.AssistantProfessor: (1.0, 0.0, 0),
    Position.Assistant: (0.0, 0.0, 0),
    # research
    Position.SeniorResearcher: (5.0, 2.5, 12),
    Position.Researcher: (2.5, 1.5, 6),
    Position.JuniorResearcher: (1.0, 0.0, 0),
}


# }}}


# {{{ candidate


@dataclass(frozen=True)
class Candidate:
    qualname: str
    publications: Sequence[Publication]
    ris: float
    recent_ris: float
    total_citations: int


def make_candidate(name: str, pubs: Sequence[Publication]) -> Candidate:
    from datetime import datetime

    seven_years_ago = datetime.now().year - RECENT_YEAR_CUTOFF

    total_ris = 0.0
    recent_total_ris = 0.0
    total_citations = 0

    publications = []
    for pub in pubs:
        ris = pub.journal.scores.get(Score.RIS)
        if ris is None:
            log.warning("Journal does not have a RIS score: '%s'.", pub.journal)
            continue

        if ris < MIN_RIS_SCORE:
            log.warning("Journal RIS '%.3f' < 0.5: '%s'.", ris, pub.journal)
            continue

        total_ris += ris
        if pub.year >= seven_years_ago:
            recent_total_ris += ris

        cited_by = []
        for cite in pub.cited_by:
            ris = cite.journal.scores.get(Score.RIS)
            if ris is None or ris < MIN_RIS_SCORE:
                continue

            if any(au.last_name in name for au in cite.authors):
                continue

            total_citations += 1
            cited_by.append(cite)

        publications.append(
            replace(
                pub,
                cited_by=tuple(cited_by),
                cited_by_count=len(cited_by),
            )
        )

    return Candidate(
        qualname=name,
        publications=publications,
        ris=total_ris,
        recent_ris=recent_total_ris,
        total_citations=total_citations,
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
    candidate = make_candidate(candidate_name, pubs)

    with open(filename, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            PUBLICATION_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        for i, pub in enumerate(candidate.publications):
            ris = pub.journal.scores[Score.RIS]
            if position in {Position.AssistantProfessor, Position.JuniorResearcher}:
                ris_per_author = ris
            else:
                ris_per_author = ris / len(pub.authors)

            writer.writerow(
                dict(
                    zip(
                        PUBLICATION_FIELD_NAMES,
                        [
                            str(i + 1),
                            filter_csv_format_pub(pub),
                            "X" if pub.year >= seven_years_ago else "",
                            f"{ris:.3f}",
                            str(len(pub.authors)),
                            f"{ris_per_author:.3f}",
                        ],
                        strict=True,
                    )
                )
            )

        writer.writerow({
            PUBLICATION_FIELD_NAMES[1]: "Total",
            PUBLICATION_FIELD_NAMES[3]: f"S = {candidate.ris}",
            PUBLICATION_FIELD_NAMES[5]: f"S_recent = {candidate.recent_ris}",
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
            for cited_by in pub.cited_by:
                ris = pub.journal.scores[Score.RIS]

                i += 1
                writer.writerow(
                    dict(
                        zip(
                            CITATION_FIELD_NAMES,
                            [
                                str(i),
                                filter_csv_format_pub(pub),
                                filter_csv_format_pub(cited_by),
                                f"{ris:.3f}",
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
    *,
    position: Position = Position.Professor,
    overwrite: bool = False,
) -> None:
    if not overwrite and outfile.exists():
        raise FileExistsError(outfile)

    # {{{ set up jinja environment

    import jinja2

    env = jinja2.Environment(  # noqa: S701
        block_start_string=r"\TplBlock{",
        block_end_string="}",
        variable_start_string=r"\TplVar{",
        variable_end_string="}",
        comment_start_string="((=",
        comment_end_string="=))",
    )

    env.filters["format_pub"] = filter_latex_format_pub
    env.filters["is_recent"] = filter_latex_is_recent
    env.filters["get_score"] = filter_get_score

    if position in {Position.AssistantProfessor, Position.JuniorResearcher}:
        env.filters["get_average_score"] = filter_get_score
    else:
        env.filters["get_average_score"] = filter_get_average_score

    # }}}

    # {{{ render the template

    from importlib.resources import files

    min_ris, min_recent_ris, min_citations = MIN_INDICATOR_FOR_POSITION[position]
    criteria = Criteria(
        position=position,
        min_ris=min_ris,
        min_recent_ris=min_recent_ris,
        min_citations=min_citations,
    )

    candidate = make_candidate(candidate_name, pubs)

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

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import Author, Publication, Score

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence


log = make_logger(__name__)


# {{{ export_publications_csv

PUBLICATION_FIELD_NAMES = (
    "Nr. Crt.",
    "Autori",
    "Titlu",
    "Revista",
    "Detalii",
    "ISSN",
    "Publicat în ultimii 7 ani",
    "Scor revistă (S_i)",
    "Nr. autori (N_i)",
    "S_i / N_i",
)


def export_publications_csv(
    filename: pathlib.Path,
    pubs: Sequence[Publication],
    *,
    encoding: str = "utf-8",
    dialect: str = "excel",
    overwrite: bool = False,
) -> None:
    if not overwrite and filename.exists():
        raise FileExistsError(filename)

    import csv
    from datetime import datetime

    seven_years_ago = datetime.now().year - 7

    with open(filename, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            PUBLICATION_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        s_score = 0.0
        s_recent_score = 0.0

        for i, pub in enumerate(pubs):
            if Score.RIS not in pub.journal.scores:
                log.warning("Journal does not have a RIS score: '%s'.", pub.journal)
                continue

            author = "; ".join(
                f"{au.last_name} {au.first_name[0]}." for au in pub.authors
            )
            ris = pub.journal.scores[Score.RIS]
            ris_per_author = ris / len(pub.authors)

            s_score += ris_per_author
            if pub.year >= seven_years_ago:
                s_recent_score += ris_per_author

            writer.writerow(
                dict(
                    zip(
                        PUBLICATION_FIELD_NAMES,
                        [
                            str(i),
                            author,
                            pub.title,
                            pub.journal.name,
                            f"{pub.volume}({pub.issue}) ({pub.year})",
                            str(pub.issn or pub.eissn),
                            "Da" if pub.year >= seven_years_ago else "Nu",
                            f"{ris:.3f}",
                            str(len(pub.authors)),
                            f"{ris_per_author:.3f}",
                        ],
                        strict=True,
                    )
                )
            )

        writer.writerow({"Autori": "Total S_i", "S_i / N_i": f"{s_score:.3f}"})
        writer.writerow({
            "Autori": "Total S_recent",
            "S_i / N_i": f"{s_recent_score:.3f}",
        })


# }}}


# {{{ export_citations_csv

CITATION_FIELD_NAMES = ("Nr. Crt.", "Articol citat", "Articol", "ISSN", "S_i")


def _display_publication_short(pub: Publication) -> str:
    author = "; ".join(f"{au.last_name} {au.first_name[0]}." for au in pub.authors)
    issn = pub.issn or pub.eissn

    return (
        f'{author}, "{pub.title}", {pub.journal.name}, {pub.volume}({pub.year}), '
        f"ISSN: {issn}, DOI: {pub.doi}"
    )


def export_citations_csv(
    filename: pathlib.Path,
    pubs: Sequence[Publication],
    *,
    encoding: str = "utf-8",
    dialect: str = "excel",
    overwrite: bool = False,
) -> None:
    if not overwrite and filename.exists():
        raise FileExistsError(filename)

    import csv

    with open(filename, "w", encoding=encoding) as f:
        writer = csv.DictWriter(
            f,
            CITATION_FIELD_NAMES,
            dialect=dialect,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        i = 0
        for pub in pubs:
            for j, cited_by in enumerate(pub.cited_by):
                if Score.RIS not in cited_by.journal.scores:
                    log.warning("Journal does not have a RIS score: '%s'.", pub.journal)
                    continue

                row = {
                    "Nr. Crt.": str(i),
                    "Articol citat": "",
                    "Articol": _display_publication_short(cited_by),
                    "ISSN": str(cited_by.issn or cited_by.eissn),
                    "S_i": f"{cited_by.journal.scores[Score.RIS]:.3f}",
                }

                if j == 0:
                    row["Articol citat"] = _display_publication_short(pub)

                writer.writerow(row)
                i += 1


# }}}


# {{{ Position


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
    Position.SeniorResearcher: "C. S. I",
    Position.Researcher: "C. S. II",
    Position.JuniorResearcher: "C. S. III",
}

# }}}


# {{{ Summary


@dataclass(frozen=True)
class Summary:
    position: Position
    minindicator: tuple[float, float, int]

    @property
    def positionname(self) -> str:
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


# {{{ export_publications_latex


@dataclass(frozen=True)
class Researcher:
    name: str
    position: Position | None
    publications: Sequence[Publication]
    indicator: tuple[float, float, int]
    ris: float
    recentris: float
    totalcitations: int

    @property
    def qualname(self) -> str:
        if self.position is None:
            return self.name

        return f"{POSITION_SHORT_NAME[self.position]} {self.name}"


def filter_yes_or_no(value: bool) -> str:  # noqa: FBT001
    return r"\textbf{DA}" if value else r"\textit{NU}"


def filter_format_pub(pub: Publication) -> str:
    return _display_publication_short(pub)


def filter_format_authors(value: tuple[Author, ...]) -> str:
    return "; ".join(f"{au.last_name} {au.first_name[0]}." for au in value)


def filter_format_details(pub: Publication) -> str:
    return f"{pub.volume}({pub.issue}) ({pub.year})"


def filter_is_recent(pub: Publication) -> str:
    from datetime import datetime

    seven_years_ago = datetime.now().year - 7

    return filter_yes_or_no(pub.year >= seven_years_ago)


def filter_get_score(pub: Publication, name: str) -> float:
    try:
        score = Score[name]
        is_average = False
    except KeyError:
        try:
            score = Score[name[1:]]
            is_average = True
        except KeyError:
            return -1.0

    value = pub.journal.scores[score]
    if is_average:
        value /= len(pub.authors)

    return value


def filter_latex_escape(value: str) -> str:
    from pylatexenc.latexencode import unicode_to_latex

    return unicode_to_latex(value)


def export_publications_latex(
    outfile: pathlib.Path,
    researcher_name: str,
    pubs: Sequence[Publication],
    *,
    position: Position = Position.Professor,
    overwrite: bool = False,
) -> None:
    # {{{ preprocess publications

    from datetime import datetime

    seven_years_ago = datetime.now().year - 7

    total_ris = 0.0
    recent_total_ris = 0.0
    total_citations = 0

    publications = []
    for pub in pubs:
        ris = pub.journal.scores.get(Score.RIS)
        if ris is None:
            log.warning("Journal does not have a RIS score: '%s'.", pub.journal)
            continue

        if ris < 0.5:
            log.warning("Journal RIS '%.3f' < 0.5: '%s'.", ris, pub.journal)
            continue

        cited_by = []
        for cite in pub.cited_by:
            ris = cite.journal.scores.get(Score.RIS)
            if ris is None or ris < 0.5:
                continue

            total_citations += 1
            cited_by.append(replace(cite, issn=cite.issn or cite.eissn))

        publications.append(
            replace(
                pub,
                issn=pub.issn or pub.eissn,
                cited_by=tuple(cited_by),
                cited_by_count=len(cited_by),
            )
        )

        total_ris += ris
        if pub.year >= seven_years_ago:
            recent_total_ris += ris

    researcher = Researcher(
        name=researcher_name,
        position=position,
        publications=publications,
        indicator=(total_ris, recent_total_ris, total_citations),
        ris=total_ris,
        recentris=recent_total_ris,
        totalcitations=total_citations,
    )

    # }}}

    # {{{ set up jinja environment

    import jinja2

    env = jinja2.Environment(  # noqa: S701
        block_start_string="(((",
        block_end_string=")))",
        variable_start_string="((*",
        variable_end_string="*))",
        comment_start_string="((=",
        comment_end_string="=))",
    )
    env.filters["yesorno"] = filter_yes_or_no
    env.filters["formatpub"] = filter_format_pub
    env.filters["formatauthors"] = filter_format_authors
    env.filters["formatdetails"] = filter_format_details
    env.filters["isrecent"] = filter_is_recent
    env.filters["getscore"] = filter_get_score
    env.filters["latexescape"] = filter_latex_escape

    # }}}

    # {{{ render the template

    from importlib.resources import files

    summary = Summary(
        position=position,
        minindicator=MIN_INDICATOR_FOR_POSITION[position],
    )

    template_file = files("uvt_scholarly.resources").joinpath("math.tpl.tex")
    with template_file.open(encoding="utf-8") as f:
        tex = (
            env
            .from_string(f.read())
            .render(researcher=researcher, summary=summary)
            .strip()
        )

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(tex)

    # }}}


# }}}

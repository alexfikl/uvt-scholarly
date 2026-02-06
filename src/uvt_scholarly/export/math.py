# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger
from uvt_scholarly.publication import Publication, Score

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

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from importlib import metadata

import click

from uvt_scholarly.export.math import ID_TO_POSITION
from uvt_scholarly.logging import make_logger
from uvt_scholarly.utils import PROJECT_NAME

log = make_logger(__name__)

SUPPORTED_SOURCES = {"wos"}

# {{{ main


@click.group(
    context_settings={"show_default": True, "max_content_width": 100},
    invoke_without_command=False,
)
@click.help_option("-h", "--help")
@click.version_option(metadata.version(PROJECT_NAME), "-v", "--version")
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Only show error messages",
)
@click.pass_context
def main(
    ctx: click.Context,
    quiet: bool,  # noqa: FBT001
) -> None:
    if quiet:
        import logging

        # NOTE: set logging level on root logger only since it propagates
        root = logging.getLogger("uvt_scholarly")
        root.setLevel(logging.ERROR)


# }}}


# {{{ download


@main.command("download")
@click.help_option("-h", "--help")
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Re-download and re-create all the databases",
)
@click.pass_context
def download(
    ctx: click.Context,
    force: bool,  # noqa: FBT001
) -> None:
    from uvt_scholarly.uefiscdi import UEFISCDI_CACHE_DIR, UEFISCDI_DB_FILE
    from uvt_scholarly.utils import ScholarlyError

    if not UEFISCDI_CACHE_DIR.exists():
        log.info("Creating UEFISCDI cache directory: '%s'.", UEFISCDI_CACHE_DIR)
        UEFISCDI_CACHE_DIR.mkdir(parents=True)

    if UEFISCDI_DB_FILE.exists():
        if force:
            log.info("Clearing RIS database: '%s'.", UEFISCDI_DB_FILE)
            UEFISCDI_DB_FILE.unlink()
        else:
            log.warning("RIS database already exists: '%s'", UEFISCDI_DB_FILE)
            ctx.exit(1)

    from uvt_scholarly.uefiscdi.ris import store_relative_influence_score

    try:
        store_relative_influence_score(UEFISCDI_DB_FILE, force=force)
    except ScholarlyError as exc:
        log.error("Failed to download RIS scores.", exc_info=exc)

        UEFISCDI_DB_FILE.unlink()
        ctx.exit(1)

    from uvt_scholarly.uefiscdi.rif import store_relative_impact_factor

    try:
        store_relative_impact_factor(UEFISCDI_DB_FILE, force=force)
    except ScholarlyError as exc:
        log.error("Failed to download RIF scores.", exc_info=exc)

        UEFISCDI_DB_FILE.unlink()
        ctx.exit(1)


# }}}

# {{{ generate


@main.group("generate")
@click.help_option("-h", "--help")
def generate() -> None:
    """Generate documents based on citation data."""
    pass


@generate.command("math")
@click.option(
    "--source",
    type=click.Choice(sorted(SUPPORTED_SOURCES)),
    required=True,
    help="The source format of the publications and citations",
)
@click.option(
    "--candidate",
    required=True,
    help="Full name of the candidate for which to generate the list",
)
@click.option(
    "--position",
    type=click.Choice(list(ID_TO_POSITION)),
    required=True,
    help="The position for which the candidate is applying",
)
@click.option(
    "--outfile",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="The file name for the generated documents",
)
@click.option(
    "--pub-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default=None,
    help="A list of publications",
)
@click.option(
    "--cite-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default=None,
    help="A list of citations for the given publications",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite generated file if it exists",
)
@click.pass_context
def generate(
    ctx: click.Context,
    source: str,
    candidate: str,
    position: str,
    outfile: pathlib.Path,
    pub_file: pathlib.Path,
    cite_file: pathlib.Path,
    force: bool,  # noqa: FBT001
) -> None:
    """Generate citation data for the Mathematics Department."""

    from uvt_scholarly.publication import Score
    from uvt_scholarly.uefiscdi import UEFISCDI_DB_FILE

    if not UEFISCDI_DB_FILE.exists():
        log.error("UEFISCDI database file does not exist: '%s'.", UEFISCDI_DB_FILE)
        log.info("Run 'uvtscholarly download' to generate the database.")
        ctx.exit(1)

    if not force and outfile.exists():
        log.error("File already exists (use --force to overwrite): '%s'.", outfile)
        ctx.exit(1)

    from uvt_scholarly.enrich import add_cited_by, add_scores
    from uvt_scholarly.export.math import PAST_YEAR_CUTOFF

    if source == "wos":
        from uvt_scholarly.wos import read_pubs

        pubs = read_pubs(pub_file)
        cites = read_pubs(cite_file, include_citations=True)
        cites = add_scores(
            cites, UEFISCDI_DB_FILE, scores={Score.RIS}, past=PAST_YEAR_CUTOFF
        )

        pubs = add_cited_by(pubs, cites)
        pubs = add_scores(
            pubs, UEFISCDI_DB_FILE, scores={Score.RIS}, past=PAST_YEAR_CUTOFF
        )
    else:
        log.error("Unknown source format: '%s'", source)
        ctx.exit(1)

    if outfile.suffix == ".tex":
        from uvt_scholarly.export.math import ID_TO_POSITION, export_publications_latex

        export_publications_latex(
            outfile,
            candidate,
            pubs,
            position=ID_TO_POSITION[position],
            overwrite=force,
        )
    elif outfile.suffix == ".csv":
        from uvt_scholarly.export.math import (
            export_citations_csv,
            export_publications_csv,
        )

        export_publications_csv(outfile, pubs)
        export_citations_csv(outfile.with_stem(f"{outfile.stem}.cites"), pubs)
    else:
        raise ValueError(f"unrecognized file type: {outfile.suffix}")


# }}}


if __name__ == "__main__":
    import sys

    sys.exit(main())

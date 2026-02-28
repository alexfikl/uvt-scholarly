# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from importlib import metadata

import click

from uvt_scholarly.export.common import ID_TO_POSITION
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
    """Download required scores and rankings to generate documents."""
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

    from uvt_scholarly.uefiscdi.ais import store_article_influence_score

    try:
        store_article_influence_score(UEFISCDI_DB_FILE, force=force)
    except ScholarlyError as exc:
        log.error("Failed to download AIS scores.", exc_info=exc)

        UEFISCDI_DB_FILE.unlink()
        ctx.exit(1)


# }}}

# {{{ math


@main.group("math")
@click.help_option("-h", "--help")
@click.pass_context
def math(ctx: click.Context) -> None:
    """Generate documents based on citation data for the Mathematics Department."""


@math.command("generate")
@click.help_option("-h", "--help")
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
    default=None,
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
def math_generate(
    ctx: click.Context,
    source: str,
    candidate: str,
    position: str,
    outfile: pathlib.Path | None,
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

    if outfile is None:
        basename = candidate.lower().replace(" ", "-").replace(".", "")
        outfile = pathlib.Path(f"math-{basename}.tex")

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
        from uvt_scholarly.export.math import export_publications_latex

        export_publications_latex(
            outfile,
            candidate,
            pubs,
            position=ID_TO_POSITION[position],
            overwrite=force,
        )
    elif outfile.suffix == ".csv":
        from uvt_scholarly.export.math import export_publications_csv

        export_publications_csv(
            outfile,
            candidate,
            pubs,
            position=ID_TO_POSITION[position],
            overwrite=force,
        )
    else:
        log.error("Unsupported file format '%s'.", outfile)
        ctx.exit(1)

    log.info("Generated file: '%s'.", outfile)


# }}}


# {{{ wos


@main.group("wos")
@click.help_option("-h", "--help")
@click.pass_context
def wos(ctx: click.Context) -> None:
    """Utilities for pre-processing Web of Science data."""


@wos.command("merge")
@click.help_option("-h", "--help")
@click.argument(
    "paths",
    nargs=-1,
    type=click.Path(exists=True, path_type=pathlib.Path),
)
@click.option(
    "--outfile",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    default=None,
    help="The file name for the generated documents",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite generated file if it exists",
)
@click.pass_context
def wos_merge(
    ctx: click.Context,
    paths: tuple[pathlib.Path, ...],
    outfile: pathlib.Path | None,
    force: bool,  # noqa: FBT001
) -> None:
    """Merge multiple Web of Science exports."""

    if not paths:
        log.error("Must give files or directories containing files to merge.")
        ctx.exit(1)

    filenames = []
    for path in paths:
        if path.is_dir():
            filenames.extend(f for f in path.iterdir() if f.is_file())
        else:
            filenames.append(path)

    if not filenames:
        log.error("No files found in given paths: %s", paths)
        ctx.exit(1)

    ext = filenames[0].suffix
    if any(f.suffix != ext for f in filenames):
        log.error("Expected all files to have the same extension '%s'.", ext)
        for i, f in enumerate(filenames):
            log.info("    %d. %s", i, f)

        ctx.exit(1)

    if outfile is None:
        outfile = pathlib.Path(f"{filenames[0].stem}.merge{ext}")

    if not force and outfile.exists():
        log.error("File already exists (use --force to overwrite): '%s'.", outfile)
        ctx.exit(1)

    from uvt_scholarly.wos import merge_csv_files

    if ext in {".txt", ".csv"}:
        merge_csv_files(filenames, outfile, overwrite=force)
    else:
        log.error("Unsupported extension '%s'.", ext)
        ctx.exit(1)

    log.info("Merged file into '%s'.", outfile)


@wos.command("filter")
@click.help_option("-h", "--help")
@click.argument(
    "filename",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--outfile",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    default=None,
    help="The file name for the generated documents",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite generated file if it exists",
)
@click.pass_context
def wos_filter(
    ctx: click.Context,
    filename: pathlib.Path,
    outfile: pathlib.Path | None,
    force: bool,  # noqa: FBT001
) -> None:
    """Remove publications that have invalid metadata."""

    if outfile is None:
        outfile = filename

    if not force and outfile.exists():
        log.error("File already exists (use --force to overwrite): '%s'.", outfile)
        ctx.exit(1)

    from uvt_scholarly.uefiscdi import UEFISCDI_DB_FILE

    if filename.suffix in {".txt", ".csv"}:
        from uvt_scholarly.wos import filter_csv_publications

        filter_csv_publications(
            filename,
            outfile,
            dbfile=UEFISCDI_DB_FILE,
            overwrite=force,
        )
    else:
        log.error("Unsupported file format: '%s'.", filename)
        ctx.exit(1)


# }}}


if __name__ == "__main__":
    import sys

    sys.exit(main())

# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from importlib import metadata

import click
import httpx
import platformdirs

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)

PROJECT_NAME = "uvt-scholarly"

UVT_SCHOLARLY_CACHE_DIR = pathlib.Path(platformdirs.user_cache_dir(PROJECT_NAME))

UEFISCDI_CACHE_DIR = UVT_SCHOLARLY_CACHE_DIR / "uefiscdi"

UEFISCDI_DB_FILE = UEFISCDI_CACHE_DIR / "uvt-scholarly.sqlite"

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

    from uvt_scholarly.publication import Score
    from uvt_scholarly.uefiscdi import UEFISCDI_DATABASE_URL, download_file
    from uvt_scholarly.uefiscdi.ris import (
        DB,
        ParsingError,
        parse_relative_influence_score,
    )

    with DB(UEFISCDI_DB_FILE) as db:
        for year in UEFISCDI_DATABASE_URL:
            url = UEFISCDI_DATABASE_URL[year][Score.RIS]

            xlsxfile = UEFISCDI_CACHE_DIR / f"uvt-scholarly-ris-{year}.xlsx"
            try:
                download_file(url, xlsxfile, force=force)
            except httpx.ConnectError:
                if xlsxfile.exists():
                    xlsxfile.unlink()

                log.error("Failed to download RIS scores: '%s'.", url)
                break

            log.info("Processing RIS scores for %d: '%s'.", year, xlsxfile)
            try:
                scores = parse_relative_influence_score(xlsxfile, year)
            except ParsingError:
                log.error("Failed to parse RIS scores: '%s'.", xlsxfile)
                break

            log.info("Inserting RIS scores for %d into database.", year)
            db.insert(year, scores)
        else:
            log.info("Database updated: '%s'.", UEFISCDI_DB_FILE)
            return

    # NOTE: we arrive here if some error happened in the database parsing, so
    # we make sure to clean up a bit. The rest of the data is temporary anyway..
    UEFISCDI_DB_FILE.unlink()
    ctx.exit(1)


# }}}

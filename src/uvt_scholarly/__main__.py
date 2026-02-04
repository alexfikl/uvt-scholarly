# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from importlib import metadata

import click

from uvt_scholarly.logging import make_logger
from uvt_scholarly.utils import PROJECT_NAME

log = make_logger(__name__)

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
    from uvt_scholarly.uefiscdi import (
        UEFISCDI_CACHE_DIR,
        UEFISCDI_DB_FILE,
        UEFISCDIError,
    )

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
    except UEFISCDIError:
        UEFISCDI_DB_FILE.unlink()
        ctx.exit(1)

    from uvt_scholarly.uefiscdi.rif import store_relative_impact_factor

    try:
        store_relative_impact_factor(UEFISCDI_DB_FILE, force=force)
    except UEFISCDIError:
        UEFISCDI_DB_FILE.unlink()
        ctx.exit(1)


# }}}

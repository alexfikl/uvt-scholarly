# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from importlib import metadata

import click

from uvt_scholarly.logging import make_logger

log = make_logger(__name__)


# {{{ main


@click.group(
    context_settings={"show_default": True, "max_content_width": 100},
    invoke_without_command=False,
)
@click.help_option("-h", "--help")
@click.version_option(metadata.version("uvt-scholarly"), "-v", "--version")
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
    profile: str,
    key: str,
    config: pathlib.Path,
    no_cache: bool,  # noqa: FBT001
    quiet: bool,  # noqa: FBT001
) -> None:
    if quiet:
        import logging

        # NOTE: set logging level on root logger only since it propagates
        root = logging.getLogger("uvt_scholarly")
        root.setLevel(logging.ERROR)


# }}}

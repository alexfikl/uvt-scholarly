# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging

from rich.logging import RichHandler


def quiet() -> None:
    """Only show errors in all ``uvt_scholarly`` loggers."""

    root = logging.getLogger("uvt_scholarly")
    root.setLevel(logging.ERROR)


def make_logger(module: str, level: int | str | None = None) -> logging.Logger:
    """Make a logger that is always a child of the root ``uvt_scholarly`` logger."""

    if level is None:
        level = logging.INFO

    if isinstance(level, str):
        level = getattr(logging, level.upper())

    assert isinstance(level, int)

    if not module.startswith("uvt_scholarly"):
        # NOTE: adding the suffix to ensure that they're all in the same root logger
        module = f"uvt_scholarly.{module}"

    name, *rest = module.split(".", maxsplit=1)
    root = logging.getLogger(name)

    if not root.hasHandlers():
        root.addHandler(RichHandler())
        root.setLevel(level)

    return root.getChild(rest[0]) if rest else root

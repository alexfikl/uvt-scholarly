# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import platformdirs

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import TracebackType

log = make_logger(__name__)


# {{{ config

PROJECT_NAME = "uvt-scholarly"

UVT_SCHOLARLY_CACHE_DIR = pathlib.Path(platformdirs.user_cache_dir(PROJECT_NAME))


# }}}

# {{{ exceptions


class ScholarlyError(Exception):
    """A generic exception raised by this library."""


class ParsingError(ScholarlyError):
    """Exception raised while parsing a score file."""


class DownloadError(ScholarlyError):
    """Exception raised when failing a download."""


# }}}

# {{{ download_file


def download_file(
    url: str,
    filename: pathlib.Path,
    *,
    # NOTE: the default timeout in httpx is 5s. We set it higher just in case..
    timeout: float = 15.0,
    force: bool = False,
) -> None:
    if not force and filename.exists():
        return

    import httpx

    # TODO: allow passing a httpx.Client
    try:
        with (
            open(filename, "wb") as f,
            httpx.stream("GET", url, timeout=timeout) as response,
        ):
            response.raise_for_status()

            for chunk in response.iter_bytes():
                f.write(chunk)
    except httpx.ConnectError:
        if filename.exists():
            filename.unlink()

        raise DownloadError(f"failed to download '{url}'") from None


# }}}

# {{{ BlockTimer


@dataclass
class BlockTimer:
    """A context manager for timing blocks of code.

    .. code:: python

        with BlockTimer("my-code-block") as bt:
            # ... do some work ...

        print(bt)
    """

    name: str = "block"
    """An identifier used to differentiate the timer."""

    t_wall_start: float = field(init=False)
    t_wall: float = field(init=False)
    """Total wall time (set after ``__exit__``), obtained from
    :func:`time.perf_counter`.
    """

    t_proc_start: float = field(init=False)
    t_proc: float = field(init=False)
    """Total process time (set after ``__exit__``), obtained from
    :func:`time.process_time`.
    """

    @property
    def t_cpu(self) -> float:
        """Total CPU time, obtained from ``t_proc / t_wall``."""
        return self.t_proc / self.t_wall

    def __enter__(self) -> BlockTimer:
        self.t_wall = self.t_proc = 0.0
        self.t_wall_start = time.perf_counter()
        self.t_proc_start = time.process_time()

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.t_wall = time.perf_counter() - self.t_wall_start
        self.t_proc = time.process_time() - self.t_proc_start

    def __str__(self) -> str:
        import datetime

        t_wall = datetime.timedelta(seconds=round(self.t_wall))
        return f"{self.name}: {t_wall} wall, {self.t_cpu:.3f}x cpu"

    def pretty(self) -> str:
        # NOTE: this matches how MATLAB shows the time from `toc`.
        return f"[{self.name}] Elapsed time is {self.t_wall:.5f} seconds."


@contextmanager
def block_timer(name: str) -> Iterator[None]:
    with BlockTimer(name) as bt:
        yield

    log.info(bt.pretty())


# }}}

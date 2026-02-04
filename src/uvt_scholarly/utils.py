# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import TracebackType

log = make_logger(__name__)


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

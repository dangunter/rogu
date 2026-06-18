"""
Get information about the current tree of
Python loggers and write it in a compact
form.

Note: This is a very simple package that has no
dependencies outside the Python standard library.
"""

from collections import defaultdict
from io import IOBase
import logging
import math
from pathlib import Path
import sys

__author__ = "Dan Gunter"

logging.basicConfig()
_log = logging.getLogger("rogu.rogu")

# vt100 color codes
RED, GRN, YEL = "\033[31m", "\033[32m", "\033[33m"
BLU, CYN, MGN = "\033[34m", "\033[35m", "\033[36m"
DIM, RST = "\033[2m", "\033[0m"

# colors for different logging levels
logcol = defaultdict(
    lambda: "",
    {
        logging.DEBUG: GRN,
        logging.INFO: BLU,
        logging.WARNING: YEL,
        logging.ERROR: RED,
        logging.CRITICAL: MGN,
    },
)


def dsplit(s: str) -> list[str]:
    """Split on dots"""
    return s.split(".")


class LogInfo:
    """
    Collect info about current logging state in a convenient form for
    printing out to the console.

    Attributes:
        app: Name for root of printed information, where None = all
        handlers: List of all handler objects used by selected loggers
        loggers: List of all logger names
        logger_levels: Dict mapping logger names to its numeric level
        logger_handlers: Dict mapping logger names to a list of
                         integer indexes in `handlers`
    """

    def __init__(self, app: str = None):
        logger_dict = logging.getLogger().manager.loggerDict

        # select loggers
        if app is None:
            self.loggers = list(logger_dict.keys())
            self.app = "<root>"
        else:
            pfx = lambda s: s.startswith(app + ".") or s == app
            self.loggers = [name for name in logger_dict if pfx(name)]
            self.app = app
        self.loggers.sort()

        # cache level of each selected logger
        self.logger_levels = {
            name: logging.getLogger(name).level for name in self.loggers
        }

        # get handlers for selected loggers
        self.logger_handlers = defaultdict(list)  # logger: list(index)
        handler_map = {}  # handler: index
        for lg in self.loggers:
            for h in getattr(logging.getLogger(lg), "handlers", []):
                if h in handler_map:
                    self.logger_handlers[lg].append(handler_map[h])
                else:
                    index = len(handler_map)
                    handler_map[h] = index
                    self.logger_handlers[lg].append(index)

        # copy unique handlers from `handler_map` into a list (by index)
        self.handlers = [None] * len(handler_map)
        for h, index in handler_map.items():
            self.handlers[index] = h

    def write(self, stream: IOBase):
        """Write the log information, in a compact form, to the provided stream."""
        # write header
        stream.write(f"[{self.app}]\n")

        # write logging tree
        hlen = len(self.handlers)
        handler_digits = 1 if hlen < 1 else int(math.log(hlen)) + 1
        handler_fmt = f"{{n:{handler_digits}d}}"
        if self.logger_handlers:
            max_handlers = max([len(v) for v in self.logger_handlers.values()])
        else:
            max_handlers = 1
        handlers_width = max_handlers * (handler_digits + 1) - 1
        indent, colsep = "  ", " | "
        for logger in self.loggers:
            count = 0
            first = True
            for index in self.logger_handlers[logger]:
                if not first:
                    stream.write(" ")
                    count += 1
                lvl = self.handlers[index].level
                stream.write(logcol[lvl])
                stream.write(handler_fmt.format(n=index + 1))
                stream.write(RST)
                count += handler_digits
                first = False
            stream.write(" " * (handlers_width - count))
            stream.write(colsep)
            parts = dsplit(logger)
            lvl = self.logger_levels[logger]
            stream.write(logcol[lvl])
            stream.write(indent * (len(parts) - 1) + parts[-1])
            stream.write(f"{RST}\n")

        # write list of handlers
        stream.write("\n")
        rec = logging.LogRecord("example", logging.INFO, "/", 0, "message", [], None)
        for i, handler in enumerate(self.handlers):
            lvl = handler.level
            num = handler_fmt.format(n=i + 1)  # lines up with column above
            out = self._stream_output(handler)
            ex = handler.format(rec)
            stream.write(
                f"{logcol[lvl]}{num}. {handler.__class__.__name__}({out}) - {ex}{RST}\n"
            )

    @staticmethod
    def _stream_output(h) -> str:
        if isinstance(h, logging.StreamHandler):
            if h.stream == sys.stdout:
                return "stdout"
            elif h.stream == sys.stderr:
                return "stderr"
            else:
                return "stream"
        elif isinstance(h, logging.FileHandler):
            return "file"
        return "other"


def _get_stream(stream) -> IOBase:
    if isinstance(stream, str):
        return Path(stream).open("w")
    elif isinstance(stream, Path):
        return stream.open("w")
    return stream


def write_log_tree(root: str = None, stream: IOBase | str | Path = sys.stdout):
    """Write the logging information, for all loggers below a given root,
    to the provided stream.

    Arguments:
        root: Select only loggers at or below this one
        stream: Output stream. A string or Path is interpreted as a file to open
                in "w" mode (overwrite any existing).
    """
    li = LogInfo(root)
    li.write(_get_stream(stream))

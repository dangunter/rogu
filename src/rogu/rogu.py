"""
Get information about the current tree of
Python loggers.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from io import IOBase
import logging
import math
from operator import itemgetter
from pathlib import Path
import sys

__author__ = "Dan Gunter"

logging.basicConfig()
_log = logging.getLogger("rogu.rogu")

loglvl = defaultdict(
    lambda: "U",
    {
        logging.NOTSET: "N",
        logging.DEBUG: "D",
        logging.INFO: "I",
        logging.WARNING: "W",
        logging.ERROR: "E",
        logging.CRITICAL: "C",
    },
)

# vt100 color codes
RED, GRN, YEL = "\033[31m", "\033[32m", "\033[33m"
BLU, CYN, MGN = "\033[34m", "\033[35m", "\033[36m"
DIM, RST = "\033[2m", "\033[0m"

# colors for different logging levels
logcol = {"U": "", "N": "", "P": "", "D": GRN, "I": BLU, "W": YEL, "E": RED, "C": MGN}


def dsplit(s: str) -> list[str]:
    """Split on dots"""
    return s.split(".")


def djoin(a: list[str]) -> str:
    """Join with dots"""
    return ".".join(a)


@dataclass
class LogTree:
    root_name: str
    root_level: str
    log_handlers: list[list[tuple[int, int]]] = field(default_factory=list)
    loggers: list[str] = field(default_factory=list)
    handler_digits: int = 0
    handler_details: list = field(default_factory=list)

    gutter_width: int = 0

    def write(self, stream):
        stream.write(f"from {logcol[self.root_level]}{self.root_name}{RST}:\n")
        h_fmt = f"{{n:{self.handler_digits}d}}"
        for i, logger in enumerate(self.loggers):
            hstr_list = []
            for n, lvl in self.log_handlers[i]:
                nstr = h_fmt.format(n=n)
                hstr_list.append(f"{logcol[lvl]}{nstr}{RST}")
            hstr = " ".join(hstr_list)
            hstr += " " * (self.gutter_width - len(hstr))
            stream.write(f"|{hstr}|{logger}\n")
        stream.write("\n")
        num = 1
        for lvl, class_name, stream_name in self.handler_details:
            col = logcol[lvl]
            hstr = h_fmt.format(n=num)
            stream.write(f" {col}{hstr}. {class_name}({stream_name}) {RST}\n")
            num += 1


class LoggingInfo:
    def __init__(self, app: str | list[str] = None):
        self.ostrm = sys.stdout
        if app is None:  # get list of all top-level names
            logger_names = logging.getLogger().manager.loggerDict
            apps = [n for n in logger_names if "." not in n]
        elif isinstance(app, str):
            apps = [app]
        else:  # assume list[str]
            apps = app

        # collect info on logger objects
        self._loggers = {}
        for app in apps:
            lmap = self._get_loggers(app)
            if not lmap:
                raise ValueError(f"No loggers for {app}")
            self._loggers.update(lmap)

    def _get_loggers(self, app):
        m = {}
        for name, logger in logging.getLogger().manager.loggerDict.items():
            parts = tuple(dsplit(name))
            if parts[0] == app:
                lvl = loglvl[getattr(logger, "level", None)]
                m[(parts, lvl)] = logger
        # return sorted by name
        return {k: m[k] for k in sorted(m.keys(), key=itemgetter(0))}

    def get_tree(self, target: str = "") -> LogTree:
        root_item = ((("<root>",), loglvl[logging.root.level]), logging.root)
        items = [root_item] + list(self._loggers.items())

        # find target root logger
        if target:
            target_parts, match = tuple(dsplit(target)), False
            for key, _ in items:
                if key[0] == target_parts:
                    match, lvl = True, key[1]
                    break
            if not match:
                raise ValueError(f"logger {target} not found")
        else:
            target_parts, lvl = root_item[0]
        name, col = djoin(target_parts), logcol[lvl]
        tree = LogTree(root_name=name, root_level=lvl)

        # get the relevant loggers
        target_parts_len = len(target_parts)
        h_refs, h_logger_max = {}, 0
        logrs, logr_handlers = [], []
        for key, logger in items:
            parts, lvl = key
            if target:
                if (
                    len(parts) < target_parts_len
                    or parts[:target_parts_len] != target_parts
                ):
                    continue
            indent = "  " * (len(parts) - 1)
            col, ppg = logcol[lvl], (
                "." if getattr(logger, "propagate", None) is False else ""
            )
            logr = f"{indent}{col}{parts[-1]}{ppg}{RST}"
            logr_h = []  # list of logger handler info
            cur_handlers = getattr(logger, "handlers", [])
            for h in cur_handlers:
                parts = getattr(h, "name", "-") or "-"
                try:  # look for existing first
                    h_num = h_refs[h]
                except KeyError:
                    h_num = len(h_refs)
                    h_refs[h] = h_num
                logr_h.append((loglvl[h.level], h_num + 1))
            h_logger_max = max(h_logger_max, len(cur_handlers))
            logrs.append(logr)
            logr_handlers.append(logr_h)

        # calculate left-hand gutter for handler numbers
        tree.handler_digits = int(math.log(len(h_refs), 10)) + 1
        tree.gutter_width = tree.handler_digits * h_logger_max + h_logger_max - 1

        # process handlers + loggers
        for i in range(len(logrs)):
            if logr_handlers[i]:
                nwid, hlist = 0, []
                for lvl, n in logr_handlers[i]:
                    hlist.append((n, lvl))
                    nwid += tree.handler_digits  # len(nstr)
                nwid += len(logr_handlers[i]) - 1
                tree.log_handlers.append(hlist)
            else:
                tree.log_handlers.append([])
            tree.loggers.append(logrs[i])

        # add handler details
        h_refs_rev = {i: h for h, i in h_refs.items()}
        for i in range(len(h_refs)):
            h = h_refs_rev[i]
            lvl = loglvl[h.level]
            cname = h.__class__.__name__
            # get a name for the stream output
            if isinstance(h, logging.StreamHandler):
                if h.stream == sys.stderr:
                    strm = "err"
                elif h.stream == sys.stdout:
                    strm = "out"
                else:
                    strm = "stream"
            elif isinstance(h, logging.FileHandler):
                strm = str(h.baseFilename)
            else:
                strm = "other"
            tree.handler_details.append((lvl, cname, strm))

        return tree


def print_log_tree(root: str = None, stream: IOBase | str | Path = None):
    """Print the logging information for all loggers below a given root."""
    li = LoggingInfo(root)
    if stream:
        if isinstance(stream, str):
            path = Path(stream)
            ostream = path.open("w")
        elif isinstance(stream, Path):
            ostream = stream.open("w")
        else:
            ostream = stream
        li.output_stream = ostream
    else:
        ostream = sys.stdout
    li.get_tree().write(ostream)

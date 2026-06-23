"""
Logging helpers. By no means a new logging library.

Example usage:
```
from rogu.log import begin as B, end as E, msg as M
import logging

_log = logging.getLogger(__name__)


def add(a, b):
    _log.info(B("add", a=a, b=b))
    x = a + b
    _log.info(E("add", a=a, b=b, sum=x))
    return x


if __name__ == "__main__":
    logging.basicConfig()
    _log.setLevel(logging.INFO)
    add(2, 2)
    _log.info(M("done"))
```

The script above will output something like:
```
INFO:__main__:(begin)add: a=2;b=2
INFO:__main__:(end)add: a=2;b=2;sum=4;dur_sec=0.000152588
INFO:__main__:done: result=4
```
"""

import re
import time

__author__ = "Dan Gunter"


class Names:
    """Customize to use different markers for begin/end messages."""

    begin = "-"
    end = "~"
    begin_before = True  # before/after identifier
    end_before = True  # before/after identifier


class NVP:
    """Customize how name/value pairs are formatted."""

    nv_sep = "="
    pair_sep = ";"


_identifier_times = {}


def begin(identifier: str, **values) -> str:
    """Build and return a message string for something beginning.

    Args:
        identifier: Identifier/name for the message. This will be used
                    as a key to look up the message when `end()` is
                    called.
        values: Optional value dictionary, to be formatted in the message

    Returns:
        Message string
    """
    _identifier_times[identifier] = time.time()
    if Names.begin_before:
        return f"{Names.begin}{identifier}{_format_values(values)}"
    else:
        return f"{identifier}{Names.begin}{_format_values(values)}"


def end(identifier: str, **values) -> str:
    """Build and return a message string for something ending.

    Args:
        identifier: Identifier/name for the message. This will be used
                    as a key to match against a `begin()` call and
                    calculate a duration. If no match is found, the
                    duration is ignored.
        values: Optional value dictionary, to be formatted in the message

    Returns:
        Message string
    """
    # add duration to name/value pairs
    now = time.time()
    t0 = _identifier_times.get(identifier, -1)
    if t0 >= 0:
        values["dur_sec"] = f"{now - t0:.6g}"
        del _identifier_times[identifier]

    if Names.end_before:
        return f"{Names.end}{identifier}{_format_values(values)}"
    else:
        return f"{identifier}{Names.end}{_format_values(values)}"


def msg(identifier: str, **values) -> str:
    """Build and return a message string.

    Args:
        identifier: Identifier/name for the message.
        values: Optional value dictionary, to be formatted in the message

    Returns:
        Message string
    """
    return f"{identifier}{_format_values(values)}"


def _format_values(values: dict) -> str:
    if not values:
        return ""
    items = []
    for key, val in values.items():
        if isinstance(val, str):
            if re.search(r"\s", val):
                sval = "'" + val.replace("'", "\\'") + "'"
            else:
                sval = val
        else:
            sval = f"{val}"
        items.append(key + NVP.nv_sep + sval)
    return ": " + NVP.pair_sep.join(items)

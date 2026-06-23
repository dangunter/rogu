from rogu.log import begin as B, end as E, msg as M
import logging
from random import shuffle
import sys

_log = logging.getLogger(__name__)
_dbg = False


def add(a, b):
    _log.info(B("add", a=a, b=b))
    x = a + b
    _log.info(E("add", a=a, b=b, sum=x))
    return x


def sort(arr, p1, p2):
    n = p2 - p1 + 1
    id_ = f"sort_{p1}-{p2}"
    _dbg and _log.debug(B(id_, start=p1, end=p2, n=n))
    if n < 3:
        if n == 1:
            _dbg and _log.debug(E(id_, n=1))
            return
        elif n == 2:
            if arr[p1] > arr[p2]:
                arr[p2], arr[p1] = arr[p1], arr[p2]
            _dbg and _log.debug(E(id_, n=2))
            return
    n2 = n // 2
    pivot = n - n2 * 2
    sort(arr, p1, p1 + (n2 - 1) + pivot)
    sort(arr, p1 + (n2 - 1) + pivot, p2)
    _dbg and _log.debug(E(id_, start=p1, end=p2))


if __name__ == "__main__":
    logging.basicConfig()
    args = sys.argv[1:]
    _dbg = False
    _log.setLevel(logging.INFO)
    if args:
        if "-v" in args:
            _log.setLevel(logging.DEBUG)
            _dbg = True
    total = add(2, 2)
    arr = list(range(100))
    shuffle(arr)
    _log.info(B("sort", n=len(arr)))
    sort(arr, 0, len(arr) - 1)
    _log.info(E("sort", n=len(arr)))
    _log.info(M("done", result=total))

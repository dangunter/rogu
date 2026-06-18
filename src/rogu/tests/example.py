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
    total = add(2, 2)
    _log.info(M("done", result=total))

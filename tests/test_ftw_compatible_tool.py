import os
import filecmp
import pytest

from ftw_compatible_tool import main
from ftw_compatible_tool import broker


def warning_as_error(*args):
    raise ValueError(*args)


def test_unit_regression_test():
    brk = broker.Broker()
    brk.subscribe(broker.TOPICS.WARNING, warning_as_error)
    test_case = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "util",
        "regression-test"
    )
    main.execute(["-x", "load " + test_case +""], brk = brk)



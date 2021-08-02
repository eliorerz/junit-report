import pytest

from src.junit_report import JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


@pytest.fixture
def raise_before_yield():
    raise_os_exception("before")
    yield


@pytest.fixture
def raise_after_yield():
    yield
    raise_os_exception("after")


@JunitTestSuite(REPORT_DIR)
# @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
def test_suite_raise_before_yield(raise_before_yield):
    dummy_test_case()


# @JunitTestSuite(REPORT_DIR)
# def test_suite_raise_after_yield(raise_after_yield):
#     dummy_test_case()


@JunitTestCase()
def raise_os_exception(when: str):
    raise OSError(f"OS error on {when}")


@JunitTestCase()
def dummy_test_case():
    pass

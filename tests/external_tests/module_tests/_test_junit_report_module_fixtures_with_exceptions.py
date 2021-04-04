import pytest

from src.junit_report import JunitFixtureTestCase, JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


@pytest.fixture(scope="function")
@JunitFixtureTestCase()
def some_fixture():
    yield


@pytest.fixture(scope="function")
@JunitFixtureTestCase()
def exception_fixture():
    raise KeyError("Some key error")


@JunitTestSuite(REPORT_DIR)
def test_suite_fixture_throws_exception(some_fixture, exception_fixture):
    other_test_case()


@JunitTestSuite(REPORT_DIR)
@pytest.mark.parametrize(
    "version",
    ["5.1", "2.3", "5.01", "1.3.5", "5.1", "2.3", "48.1d", "2.3", 100, "250"],
)
def test_suite_fixture_with_parametrize_throws_exception(some_fixture, exception_fixture, version):
    other_test_case()


@JunitTestCase()
def other_test_case():
    pass


@JunitTestCase()
def first_test_case():
    pass


@JunitTestCase()
def third_test_case():
    pass

import pytest

from src.junit_report import JunitFixtureTestCase, JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


@pytest.fixture
@JunitFixtureTestCase()
def fixture_with_exception_after_yield():
    yield
    raise ValueError("Fixture Test Exception")


@pytest.fixture
@JunitFixtureTestCase()
def fixture_with_yield():
    class A:
        name = "class_a"

    yield A()


@JunitTestSuite(REPORT_DIR)
def test_suite_fixture_raise_exception_after_yield(fixture_with_yield, fixture_with_exception_after_yield):
    first_case()
    second_case()


@JunitTestCase()
def first_case():
    pass


@JunitTestCase()
def second_case():
    pass

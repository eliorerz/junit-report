from pathlib import Path

import pytest

from src.junit_report import JunitTestSuite, JunitFixtureTestCase, JunitTestCase

REPORT_DIR = Path.cwd().joinpath(".reports")


@pytest.fixture(scope="function")
@JunitFixtureTestCase()
def some_fixture():
    yield


@JunitTestSuite(REPORT_DIR)
def test_suite_one_fixture(some_fixture):
    other_test_case()
    first_test_case()


@JunitTestCase()
def other_test_case():
    pass


@JunitTestCase()
def first_test_case():
    pass

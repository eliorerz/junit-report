from dataclasses import dataclass

import pytest

from src.junit_report import JunitFixtureTestCase, JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


@dataclass
class SomeObj:
    name: str

    def get_name(self):
        return self.name


@pytest.fixture(scope="function")
@JunitFixtureTestCase()
def get_some_fixture():
    @JunitTestCase()
    def get_my_fixture():
        return SomeObj("123456789")

    yield get_my_fixture


@pytest.fixture(scope="function")
@JunitFixtureTestCase()
def raise_exception():
    @JunitTestCase()
    def get_my_fixture():
        raise KeyError("Invalid fixture")

    yield get_my_fixture


@JunitTestSuite(REPORT_DIR)
def test_suite_nested_fixture(get_some_fixture):
    other_test_case()
    get_some_fixture().get_name()
    third_test_case()


@JunitTestSuite(REPORT_DIR)
def test_suite_nested_fixture_wrong_type(raise_exception):
    other_test_case()
    raise_exception()
    third_test_case()


@JunitTestCase()
def other_test_case():
    pass


@JunitTestCase()
def third_test_case():
    pass


@JunitTestSuite(REPORT_DIR)
def test_suite_nested_test_case_exception():
    other_nested_test_case()


@JunitTestCase()
def other_nested_test_case():
    exception_test_case()


@JunitTestCase()
def exception_test_case():
    raise OSError("OSOSOSOS")

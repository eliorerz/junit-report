from dataclasses import dataclass

import pytest

from src.junit_report import JunitFixtureTestCase, JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


@dataclass
class SomeObj:
    name: str

    def get_name(self):
        return self.name


class TestJunitNestedBaseTestCase:
    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def get_some_fixture(self):
        @JunitTestCase()
        def get_my_fixture():
            return SomeObj("123456789")

        yield get_my_fixture

    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def raise_exception(self):
        @JunitTestCase()
        def get_my_fixture():
            raise KeyError("Invalid fixture")

        yield get_my_fixture


class TestJunitNestedTestCase(TestJunitNestedBaseTestCase):
    @JunitTestSuite(REPORT_DIR)
    def test_suite_nested_fixture(self, get_some_fixture):
        self.other_test_case()
        get_some_fixture().get_name()
        self.third_test_case()

    @JunitTestSuite(REPORT_DIR)
    def test_suite_nested_fixture_wrong_type(self, raise_exception):
        self.other_test_case()
        raise_exception()
        self.third_test_case()

    @JunitTestCase()
    def other_test_case(self):
        pass

    @JunitTestCase()
    def third_test_case(self):
        pass

    @JunitTestSuite(REPORT_DIR)
    def test_suite_nested_test_case_exception(self):
        self.other_nested_test_case()

    @JunitTestCase()
    def other_nested_test_case(self):
        self.exception_test_case()

    @JunitTestCase()
    def exception_test_case(self):
        raise OSError("OSOSOSOS")

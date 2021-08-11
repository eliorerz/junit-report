import pytest

from src.junit_report import JunitTestSuite, JunitTestCase, JunitFixtureTestCase
from tests import REPORT_DIR


class TestJunitSuiteNoCases:

    @JunitTestCase()
    def dummy_test_case(self):
        pass

    @JunitTestCase()
    def other_test_case(self):
        pass

    @JunitTestCase()
    def exception_test_case(self):
        raise BrokenPipeError("PIPE")

    @pytest.fixture
    @JunitFixtureTestCase()
    def my_test_fixture(self):
        self.other_test_case()
        yield

    @pytest.fixture
    @JunitFixtureTestCase()
    def exception_fixture(self):
        self.exception_test_case()
        yield

    @JunitTestSuite(REPORT_DIR)
    def test_suite_test_case_inside_fixture(self, my_test_fixture):
        self.dummy_test_case()

    @JunitTestSuite(REPORT_DIR)
    def test_suite_test_case_inside_fixture_with_exception(self, exception_fixture):
        self.dummy_test_case()

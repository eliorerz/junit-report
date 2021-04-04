import pytest

from src.junit_report import JunitFixtureTestCase, JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


class TestJunitFixtureTestCase:
    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def some_fixture(self):
        yield

    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def other_fixture(self, request):
        yield

    @JunitTestSuite(REPORT_DIR)
    def test_suite_two_fixtures(self, some_fixture, other_fixture):
        self.other_test_case()
        self.first_test_case()

    @JunitTestCase()
    def other_test_case(self):
        pass

    @JunitTestCase()
    def first_test_case(self):
        pass

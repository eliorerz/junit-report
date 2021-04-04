from pathlib import Path

import pytest

from src.junit_report import JunitTestCase, JunitTestSuite, JunitFixtureTestCase

REPORT_DIR = Path.cwd().joinpath(".reports")


class TestJunitFixtureTestCase:
    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def some_fixture(self):
        yield

    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def exception_fixture(self):
        raise KeyError("Some key error")

    @JunitTestSuite(REPORT_DIR)
    def test_suite_fixture_throws_exception(self, some_fixture, exception_fixture):
        self.other_test_case()

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize(
        "version",
        ["5.1", "2.3", "5.01", "1.3.5", "5.1", "2.3", "48.1d", "2.3", 100, "250"],
    )
    def test_suite_fixture_with_parametrize_throws_exception(self, some_fixture, exception_fixture, version):
        self.other_test_case()

    @JunitTestCase()
    def other_test_case(self):
        pass

    @JunitTestCase()
    def first_test_case(self):
        pass

    @JunitTestCase()
    def third_test_case(self):
        pass

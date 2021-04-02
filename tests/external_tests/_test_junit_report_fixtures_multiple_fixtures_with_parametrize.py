from pathlib import Path

import pytest

from src.junit_report import JunitTestCase, JunitTestSuite
from src.junit_report.junit_fixture_test_case import JunitFixtureTestCase

REPORT_DIR = Path.cwd().joinpath(".reports")


class TestJunitFixtureTestCase:
    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def some_fixture(self):
        yield

    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def other_fixture(self):
        yield

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("version", ["5.1", "6.21980874565", 6.5, "some__long_string_that_is_not_a_number"])
    def test_suite_two_fixtures_parametrize(self, some_fixture, other_fixture, version):
        self.other_test_case()
        self.first_test_case()
        self.third_test_case()

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("version", ["5.1", "6.21980874565", 6.5, "some__long_string_that_is_not_a_number"])
    @pytest.mark.parametrize("letter", ["A", "B", "C"])
    @pytest.mark.parametrize("animal", ["Dog", "Cat", "Horse", "Kangaroo"])
    @pytest.mark.parametrize("none", [None])
    def test_suite_two_fixtures_four_parametrize(self, some_fixture, other_fixture, version, letter, animal, none):
        self.other_test_case()
        self.first_test_case()

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("version", ["5.1", "6.21980874565", 6.5, "some__long_string_that_is_not_a_number"])
    @pytest.mark.parametrize("letter", ["A", "B", "C"])
    @pytest.mark.parametrize("none", [None])
    @pytest.mark.regression1
    @pytest.mark.sanity
    def test_suite_fixtures_with_marks(self, other_fixture, version, letter, none):
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

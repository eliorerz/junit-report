import pytest

from src.junit_report import JunitTestSuite, JunitTestCase, JunitFixtureTestCase
from tests import REPORT_DIR


class TestJunitSuiteNoCases:

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
    def test_suite_no_cases_with_exception_parametrize(self, number):
        raise OSError(f"Something went wrong {number}")

    @pytest.mark.regression1
    @pytest.mark.sanity
    @JunitTestSuite(REPORT_DIR)
    def test_suite_no_cases_with_exception(self):
        raise RuntimeError("Something went wrong during runtime")

    @JunitTestCase()
    def dummy_test_case(self):
        pass

    @JunitTestCase()
    def other_test_case(self):
        pass

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
    def test_suite_cases_with_inner_exception_with_parametrize(self, number):
        self.dummy_test_case()
        self.other_test_case()
        raise OSError(f"Something went wrong {number}")

    @pytest.fixture
    def my_fixture(self):
        yield 5

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
    def test_suite_cases_with_inner_exception_with_parametrize_and_fixture(self, my_fixture, number):
        self.dummy_test_case()
        self.other_test_case()
        assert my_fixture == 5
        raise OSError(f"Something went wrong {number}")

    @pytest.fixture
    @JunitFixtureTestCase()
    def my_tes_fixture(self):
        yield 6

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
    def test_suite_cases_with_inner_exception_with_parametrize_and_test_fixture(self, my_tes_fixture, number):
        self.dummy_test_case()
        assert my_tes_fixture == 6
        raise OSError(f"Something went wrong {number}")
        self.other_test_case()

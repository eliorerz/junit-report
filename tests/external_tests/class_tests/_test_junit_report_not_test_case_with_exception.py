import pytest
from _pytest.fixtures import SubRequest

from src.junit_report import JunitFixtureTestCase, JunitTestSuite
from tests import REPORT_DIR


class TestJunitSuiteNoCases:
    EXPECTED_FIXTURE_PARAMS = {"arg_to_pass": "test_arg_1234"}

    @pytest.fixture
    @JunitFixtureTestCase()
    def fixture_with_yield(self, request: SubRequest):
        class A:
            params = request.param

        yield A()

    @pytest.fixture
    @JunitFixtureTestCase()
    def fixture_yield_instance(self):
        class A:
            def func(self):
                return self.__class__.__name__

        yield A()

    @JunitTestSuite(REPORT_DIR)
    @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
    def test_suite_no_cases_with_exception_parametrize(self, number):
        raise OSError(f"Something went wrong {number}")

    @pytest.mark.regression1
    @pytest.mark.sanity
    @JunitTestSuite(REPORT_DIR)
    def test_suite_no_cases_with_exception(self):
        raise RuntimeError("Something went wrong during runtime")

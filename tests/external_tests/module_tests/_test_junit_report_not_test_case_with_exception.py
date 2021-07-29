import pytest
from _pytest.fixtures import SubRequest
from junit_report import JunitTestSuite

from src.junit_report import JunitFixtureTestCase
from tests import REPORT_DIR

EXPECTED_FIXTURE_PARAMS = {"arg_to_pass": "test_arg_1234"}


@pytest.fixture
@JunitFixtureTestCase()
def fixture_with_yield(request: SubRequest):
    class A:
        params = request.param

    yield A()


@pytest.fixture
@JunitFixtureTestCase()
def fixture_yield_instance():
    class A:
        def func(self):
            return self.__class__.__name__

    yield A()


@JunitTestSuite(REPORT_DIR)
@pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
def test_suite_no_cases_with_exception_parametrize(number):
    raise OSError(f"Something went wrong {number}")


@pytest.mark.regression1
@pytest.mark.sanity
@pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
def test_no_suite_with_parametrize(number):
    raise RuntimeError("Something went wrong during runtime")

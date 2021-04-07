import pytest

from src.junit_report import JunitFixtureTestCase, JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


class TestExceptionAfterYield:
    @pytest.fixture
    @JunitFixtureTestCase()
    def fixture_with_exception_after_yield(self):
        yield
        raise ValueError("Fixture Test Exception")

    @pytest.fixture
    @JunitFixtureTestCase()
    def fixture_with_yield(self):
        class A:
            name = "class_a"

        yield A()

    @JunitTestSuite(REPORT_DIR)
    def test_suite_fixture_raise_exception_after_yield(self, fixture_with_yield, fixture_with_exception_after_yield):
        self.first_case()
        self.second_case()

    @JunitTestCase()
    def first_case(self):
        pass

    @JunitTestCase()
    def second_case(self):
        pass

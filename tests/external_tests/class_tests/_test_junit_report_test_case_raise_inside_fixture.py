import pytest

from src.junit_report import JunitFixtureTestCase, JunitTestCase, JunitTestSuite
from tests import REPORT_DIR


class TestJunitTestCaseRaiseOnFixture:
    @pytest.fixture
    @JunitFixtureTestCase()
    def raise_before_yield(self):
        self.raise_os_exception("before")
        yield

    @pytest.fixture
    def raise_after_yield(self):
        yield
        self.raise_os_exception("after")

    @JunitTestSuite(REPORT_DIR)
    # @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
    def test_suite_raise_before_yield(self, raise_before_yield):
        self.dummy_test_case()

    # @JunitTestSuite(REPORT_DIR)
    # def test_suite_raise_after_yield(self, raise_after_yield):
    #     self.dummy_test_case()

    @JunitTestCase()
    def raise_os_exception(self, when: str):
        raise OSError(f"OS error on {when}")

    @JunitTestCase()
    def dummy_test_case(self):
        pass

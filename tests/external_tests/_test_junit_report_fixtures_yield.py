from pathlib import Path

import pytest

from src.junit_report import JunitTestSuite
from src.junit_report.junit_fixture_test_case import JunitFixtureTestCase

REPORT_DIR = Path.cwd().joinpath(".reports")


class TestJunitFixtureTestCase:
    @pytest.fixture(scope="function")
    @JunitFixtureTestCase()
    def some_fixture(self):
        pass

    @pytest.fixture
    @JunitFixtureTestCase()
    def fixture_with_yield(self):
        yield

    @pytest.fixture
    @JunitFixtureTestCase()
    def fixture_yield_instance(self):
        class A:
            def func(self):
                return self.__class__.__name__
        yield A()

    @JunitTestSuite(REPORT_DIR)
    def test_suite_fixture_yield(self, some_fixture, fixture_with_yield, fixture_yield_instance):
        assert hasattr(fixture_yield_instance, "func")
        assert fixture_yield_instance.func() == "A"

from pathlib import Path

import pytest

from src.junit_report import JunitTestSuite
from src.junit_report.junit_fixture_test_case import JunitFixtureTestCase

REPORT_DIR = Path.cwd().joinpath(".reports")


class TestJunitFixtureTestCase:
    index = 0

    def write_index(self, filename: str):
        with open(filename, "w") as f:
            f.write(str(self.index))
            self.index += 1

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
    def fixture_with_yield_2(self):
        class A:
            name = "class_a"

        self.write_index("file_before_yield")
        yield A()
        self.write_index("file_after_yield")

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

    @JunitTestSuite(REPORT_DIR)
    def test_suite_fixture_yield2(self, fixture_with_yield_2):
        self.write_index("file_in_case")
        assert fixture_with_yield_2.name == "class_a"

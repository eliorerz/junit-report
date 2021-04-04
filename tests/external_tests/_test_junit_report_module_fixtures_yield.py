from pathlib import Path

import pytest

from src.junit_report import JunitTestSuite, JunitFixtureTestCase

REPORT_DIR = Path.cwd().joinpath(".reports")

index = 0


def write_index(filename: str):
    global index
    with open(filename, "w") as f:
        f.write(str(index))
        index += 1


@pytest.fixture(scope="function")
@JunitFixtureTestCase()
def some_fixture():
    pass


@pytest.fixture
@JunitFixtureTestCase()
def fixture_with_yield():
    yield


@pytest.fixture
@JunitFixtureTestCase()
def fixture_with_yield_2():
    class A:
        name = "class_a"

    write_index("file_before_yield")
    yield A()
    write_index("file_after_yield")


@pytest.fixture
@JunitFixtureTestCase()
def fixture_yield_instance():
    class A:
        def func(self):
            return __class__.__name__

    yield A()


@JunitTestSuite(REPORT_DIR)
def test_suite_fixture_yield(some_fixture, fixture_with_yield, fixture_yield_instance):
    assert hasattr(fixture_yield_instance, "func")
    assert fixture_yield_instance.func() == "A"


@JunitTestSuite(REPORT_DIR)
def test_suite_fixture_yield2(fixture_with_yield_2):
    write_index("file_in_case")
    assert fixture_with_yield_2.name == "class_a"

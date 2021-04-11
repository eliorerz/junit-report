import pytest
from _pytest.fixtures import SubRequest

from src.junit_report import JunitFixtureTestCase


class TestJunitNoSuite:
    index = 0
    EXPECTED_FIXTURE_PARAMS = {"arg_to_pass": "test_arg_1234"}

    def write_index(self, filename: str):
        with open(filename, "w") as f:
            f.write(str(self.index))
            self.index += 1

    @pytest.fixture
    @JunitFixtureTestCase()
    def fixture_with_yield(self, request: SubRequest):
        class A:
            params = request.param

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

    @pytest.mark.parametrize("fixture_with_yield", [EXPECTED_FIXTURE_PARAMS], indirect=["fixture_with_yield"])
    def test_no_suite_fixture_yield(self, fixture_with_yield):
        self.write_index("file_in_case")
        assert fixture_with_yield.params == self.EXPECTED_FIXTURE_PARAMS

    @pytest.mark.regression1
    @pytest.mark.sanity
    @pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
    def test_no_suite_with_parametrize(self, number):
        pass

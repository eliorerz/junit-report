from _pytest.config import ExitCode

from tests import _TestExternal


class TestWithPytestDecorators(_TestExternal):

    def test_base_flow(self):
        test = "external_tests/_test_junit_report_fixtures_base_flow.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_one_fixture"
        self.base_flow(test, expected_suite_name)

    def test_multiple_fixtures(self):
        test = "external_tests/_test_junit_report_fixtures_multiple_fixtures.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures"
        self.multiple_fixtures(test, expected_suite_name)

    def test_multiple_fixtures_with_parametrize(self):
        test = "external_tests/_test_junit_report_fixtures_multiple_fixtures_with_parametrize.py"
        first_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures_parametrize"
        second_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures_four_parametrize"
        third_suite_name = "TestJunitFixtureTestCase_test_suite_fixtures_with_marks"

        self.multiple_fixtures_with_parametrize(test, first_suite_name, second_suite_name, third_suite_name)

    def test_junit_report_fixture_yield_none(self, files_cleaner):
        test = "external_tests/_test_junit_report_fixtures_yield.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_fixture_yield"

        self.junit_report_fixture_yield_none(test, expected_suite_name)

    def test_junit_report_fixtures_with_exceptions(self):
        test = "external_tests/_test_junit_report_fixtures_with_exceptions.py"
        first_suite_name = "fixture_test_suite_fixture_throws_exception"
        second_suite_name = "fixture_test_suite_fixture_with_parametrize_throws_exception"

        self.junit_report_fixtures_with_exceptions(test, first_suite_name, second_suite_name)

    def test_report_path_env_var(self):
        test = "external_tests/_test_junit_report_env_var.py"
        exit_code, _ = self.execute_test(test)
        assert exit_code == ExitCode.OK

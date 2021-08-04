from tests import _TestExternal


class TestPytestModule(_TestExternal):
    def test_module_base_flow(self):
        test = "external_tests/module_tests/_test_junit_report_module_base_flow.py"
        expected_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_module_base_flow_test_suite_one_fixture"
        )
        self.base_flow(test, expected_suite_name)

    def test_module_multiple_fixtures(self):
        test = "external_tests/module_tests/_test_junit_report_module_multiple_fixtures.py"
        expected_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_module_multiple_fixtures_test_suite_two_fixtures"
        )
        self.multiple_fixtures(test, expected_suite_name)

    def test_module_multiple_fixtures_with_parametrize(self):
        test = "external_tests/module_tests/_test_junit_report_module_multiple_fixtures_with_parametrize.py"
        first_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_module_multiple_fixtures_with_parametrize_"
            "test_suite_two_fixtures_parametrize"
        )
        second_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_module_multiple_fixtures_with_parametrize_"
            "test_suite_two_fixtures_four_parametrize"
        )
        third_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_module_multiple_fixtures_with_parametrize_"
            "test_suite_fixtures_with_marks"
        )

        self.multiple_fixtures_with_parametrize(test, first_suite_name, second_suite_name, third_suite_name)

    def test_module_junit_report_fixture_yield_none(self, files_cleaner):
        test = "external_tests/module_tests/_test_junit_report_module_fixtures_yield.py"
        expected_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_module_fixtures_yield_test_suite_fixture_yield"
        )

        self.junit_report_fixture_yield_none(test, expected_suite_name)

    def test_module_fixtures_with_exceptions(self):
        pkg = "_test_junit_report_module_fixtures_with_exceptions"
        test = f"external_tests/module_tests/{pkg}.py"

        first_suite_name = f"tests.external_tests.module_tests.{pkg}_test_suite_fixture_throws_exception"
        second_suite_name = (
            f"tests.external_tests.module_tests.{pkg}_test_suite_fixture_with_parametrize_throws_exception"
        )
        self.junit_report_fixtures_with_exceptions(test, first_suite_name, second_suite_name)

    def test_nested_test_case(self):
        test = "external_tests/module_tests/_test_junit_report_nested_test_case.py"
        first_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_nested_test_case_test_suite_nested_fixture"
        )
        second_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_nested_test_case_test_suite_nested_fixture_wrong_type"
        )

        self.nested_test_case(test, "module", first_suite_name, second_suite_name)

    def test_fixture_raise_exception_after_yield(self):
        test = "external_tests/module_tests/_test_junit_report_fixture_raise_exception_after_yield.py"
        first_suite_name = (
            "tests.external_tests.module_tests._test_junit_report_fixture_raise_exception_after_yield"
            "_test_suite_fixture_raise_exception_after_yield"
        )

        self.fixture_raise_exception_after_yield(test, first_suite_name)

    def test_no_suite(self, files_cleaner):
        test = "external_tests/module_tests/_test_junit_report_test_cases_without_suite.py"
        report_name = "unittest.xml"
        self.pytest_suite_no_junit_suite(test, report_name)

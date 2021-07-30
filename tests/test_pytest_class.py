from tests import _TestExternal


class TestWithPytestDecorators(_TestExternal):
    def test_base_flow(self):
        test = "external_tests/class_tests/_test_junit_report_class_fixtures_base_flow.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_one_fixture"

        self.base_flow(test, expected_suite_name)

    def test_custom_filename(self):
        test = "external_tests/class_tests/_test_junit_report_class_fixtures_with_custom_report_name.py"
        expected_suite_name = "some_test_with_one_fixture"
        expected_other_suite_name = "another_test_with_no_fixtures11"

        self.expected_filename(test, expected_suite_name, expected_other_suite_name)

    def test_multiple_fixtures(self):
        test = "external_tests/class_tests/_test_junit_report_class_fixtures_multiple_fixtures.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures"
        self.multiple_fixtures(test, expected_suite_name)

    def test_multiple_fixtures_with_parametrize(self):
        test = "external_tests/class_tests/_test_junit_report_class_multiple_fixtures_with_parametrize.py"
        first_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures_parametrize"
        second_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures_four_parametrize"
        third_suite_name = "TestJunitFixtureTestCase_test_suite_fixtures_with_marks"

        self.multiple_fixtures_with_parametrize(test, first_suite_name, second_suite_name, third_suite_name)

    def test_junit_report_fixture_yield_none(self, files_cleaner):
        test = "external_tests/class_tests/_test_junit_report_class_fixtures_yield.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_fixture_yield"

        self.junit_report_fixture_yield_none(test, expected_suite_name)

    def test_junit_report_fixtures_with_exceptions(self):
        test = "external_tests/class_tests/_test_junit_report_class_with_exceptions.py"
        first_suite_name = "TestJunitFixtureTestCase_test_suite_fixture_throws_exception"
        second_suite_name = "TestJunitFixtureTestCase_test_suite_fixture_with_parametrize_throws_exception"

        self.junit_report_fixtures_with_exceptions(test, first_suite_name, second_suite_name)

    def test_nested_test_case(self):
        test = "external_tests/class_tests/_test_junit_report_nested_test_case.py"
        first_suite_name = "TestJunitNestedTestCase_test_suite_nested_fixture"
        second_suite_name = "TestJunitNestedTestCase_test_suite_nested_fixture_wrong_type"
        third_suite_name = "TestJunitNestedTestCase_test_suite_nested_test_case_exception"

        self.nested_test_case(test, "class", first_suite_name, second_suite_name, third_suite_name)

    def test_fixture_raise_exception_after_yield(self):
        test = "external_tests/class_tests/_test_junit_report_fixture_raise_exception_after_yield.py"
        first_suite_name = "TestExceptionAfterYield_test_suite_fixture_raise_exception_after_yield"

        self.fixture_raise_exception_after_yield(test, first_suite_name)

    def test_no_suite(self, files_cleaner):
        test = "external_tests/class_tests/_test_junit_report_test_cases_without_suite.py"
        report_name = "unittest.xml"
        self.pytest_suite_no_junit_suite(test, report_name)

    def test_suite_no_cases_with_exception(self):
        test = "external_tests/class_tests/_test_junit_report_not_test_case_with_exception.py"
        first_suite_name = "TestJunitSuiteNoCases_test_suite_no_cases_with_exception_parametrize"
        second_suite_name = "TestJunitSuiteNoCases_test_suite_fixture_with_parametrize_throws_exception"

        self.junit_report_suite_no_cases_with_exception(test, first_suite_name, second_suite_name)

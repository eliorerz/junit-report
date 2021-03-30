import io
import os
import shutil
from collections import OrderedDict
from contextlib import redirect_stdout
from pathlib import Path
from typing import Tuple

import pytest
import xmltodict
from _pytest.config import ExitCode

from src.junit_report import JunitTestSuite
from tests import BaseTest

REPORT_DIR = Path.cwd().joinpath(".reports")


class TestWithPytestDecorators(BaseTest):
    @classmethod
    @pytest.fixture(autouse=True)
    def teardown(cls):
        yield
        shutil.rmtree(REPORT_DIR, ignore_errors=True)
        JunitTestSuite._junit_suites = dict()

    @classmethod
    def get_test_report(cls, suite_name: str) -> OrderedDict:
        test_report_path = REPORT_DIR.joinpath(JunitTestSuite.XML_REPORT_FORMAT.format(suite_name=suite_name))

        with open(test_report_path) as f:
            return xmltodict.parse(f.read())

    @classmethod
    def execute_test(cls, testfile: str) -> Tuple[ExitCode, str]:
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = pytest.main([testfile])

        return exit_code, f.getvalue()

    def test_base_flow(self):
        test = "external_tests/_test_junit_report_fixtures_base_flow.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_one_fixture"

        exit_code, _ = self.execute_test(test)
        assert exit_code == ExitCode.OK

        xml_results = self.get_test_report(suite_name=expected_suite_name)

        self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=3,
            testsuite_name=expected_suite_name,
            fixtures_count=1,
            functions_count=2,
        )

    def test_multiple_fixtures(self):
        test = "external_tests/_test_junit_report_fixtures_multiple_fixtures.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures"

        exit_code, _ = self.execute_test(test)

        assert exit_code == ExitCode.OK
        xml_results = self.get_test_report(suite_name=expected_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=4,
            testsuite_name=expected_suite_name,
            fixtures_count=2,
            functions_count=2,
        )

    def test_multiple_fixtures_with_parametrize(self):
        test = "external_tests/_test_junit_report_fixtures_multiple_fixtures_with_parametrize.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures_parametrize"
        parametrize_arg_count = 4
        case_count = 3
        fixtures_count = 2

        expected_fixtures_count = fixtures_count * parametrize_arg_count
        expected_cases_count = case_count * parametrize_arg_count

        exit_code, _ = self.execute_test(test)
        assert exit_code == ExitCode.OK
        xml_results = self.get_test_report(suite_name=expected_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=expected_fixtures_count + expected_cases_count,
            testsuite_name=expected_suite_name,
            fixtures_count=expected_fixtures_count,
            functions_count=expected_cases_count,
        )

        expected_suite_name = "TestJunitFixtureTestCase_test_suite_two_fixtures_four_parametrize"
        first_mark_count = 4
        second_mark_count = 3
        third_mark_count = 4
        fourth_mark_count = 1
        permutations_count = first_mark_count * second_mark_count * third_mark_count * fourth_mark_count
        fixtures_count = 2
        cases_count = 2
        expected_cases_count = permutations_count * fixtures_count * cases_count

        xml_results = self.get_test_report(suite_name=expected_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=expected_cases_count,
            testsuite_name=expected_suite_name,
            fixtures_count=fixtures_count * permutations_count,
            functions_count=cases_count * permutations_count,
        )

    def test_junit_report_fixture_yield_none(self):
        test = "external_tests/_test_junit_report_fixtures_yield.py"
        expected_suite_name = "TestJunitFixtureTestCase_test_suite_fixture_yield"
        expected_case_count = 0
        expected_fixtures_count = 3
        expected_failures = 0

        exit_code, _ = self.execute_test(test)
        assert exit_code == ExitCode.OK
        xml_results = self.get_test_report(suite_name=expected_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            failures=expected_failures,
            testsuite_tests=expected_fixtures_count,
            testsuite_name=expected_suite_name,
            fixtures_count=expected_fixtures_count,
            functions_count=expected_case_count,
        )

        expected_before_yield = "0"
        expected_in_case = "1"
        expected_after_yield = "2"

        file_before_yield_path = "file_before_yield"
        file_in_case_path = "file_in_case"
        file_after_yield_path = "file_after_yield"

        with open(file_before_yield_path) as f:
            assert f.read() == expected_before_yield

        with open(file_in_case_path) as f:
            assert f.read() == expected_in_case

        with open(file_after_yield_path) as f:
            assert f.read() == expected_after_yield

        os.remove(file_before_yield_path)
        os.remove(file_in_case_path)
        os.remove(file_after_yield_path)

    def test_junit_report_fixtures_with_exceptions(self):
        test = "external_tests/_test_junit_report_fixtures_with_exceptions.py"
        expected_suite_name = "fixture_test_suite_fixture_throws_exception"
        expected_case_count = 0
        expected_fixtures_count = 2
        expected_failures = 1

        exit_code, _ = self.execute_test(test)
        assert exit_code == ExitCode.TESTS_FAILED
        xml_results = self.get_test_report(suite_name=expected_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            failures=expected_failures,
            testsuite_tests=expected_fixtures_count,
            testsuite_name=expected_suite_name,
            fixtures_count=expected_fixtures_count,
            functions_count=expected_case_count,
        )

        expected_parametrize_suite_name = "fixture_test_suite_fixture_with_parametrize_throws_exception"
        expected_parametrize_fixture_failures = 1
        expected_parametrize_fixture_count = 2
        expected_parametrize_test_cases = 0
        expected_parametrize_count = 10

        xml_results = self.get_test_report(suite_name=expected_parametrize_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            failures=expected_parametrize_fixture_failures * expected_parametrize_count,
            testsuite_tests=(expected_parametrize_fixture_count * expected_parametrize_count),
            testsuite_name=expected_parametrize_suite_name,
            fixtures_count=expected_parametrize_fixture_count * expected_parametrize_count,
            functions_count=expected_parametrize_test_cases,
        )

    def test_report_path_env_var(self):
        test = "external_tests/_test_junit_report_env_var.py"
        exit_code, _ = self.execute_test(test)
        assert exit_code == ExitCode.OK

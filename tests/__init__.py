import io
import itertools
import os
import shutil
from collections import OrderedDict
from contextlib import redirect_stdout
from pathlib import Path
from typing import Callable, List, Tuple

import pytest
import xmltodict
from _pytest.config import ExitCode

from src.junit_report import JunitTestSuite, TestCaseCategories

try:
    os.chdir(Path().cwd().joinpath("tests"))
except FileNotFoundError:
    """ Ignore """

REPORT_DIR = Path.cwd().joinpath(".reports")


class BaseTest:
    @classmethod
    def assert_xml_report_results_with_cases(
        cls,
        xml_results: dict,
        testsuite_tests: int,
        testsuite_name: str,
        failures=0,
        errors=0,
        fixtures_count=0,
        functions_count=0,
    ) -> List[OrderedDict]:
        cases = cls.assert_xml_report_results(xml_results, testsuite_tests, testsuite_name, failures, errors)

        assert len([c for c in cases if c["@class"] == TestCaseCategories.FIXTURE]) == fixtures_count
        assert len([c for c in cases if c["@class"] == TestCaseCategories.FUNCTION]) == functions_count
        return cases

    @staticmethod
    def assert_xml_report_results(
        xml_results: dict,
        testsuite_tests: int,
        testsuite_name: str,
        failures=0,
        errors=0,
    ) -> List[OrderedDict]:
        assert "testsuites" in xml_results
        assert int(xml_results["testsuites"]["@failures"]) == failures
        assert int(xml_results["testsuites"]["@errors"]) == errors

        testsuite = xml_results["testsuites"]["testsuite"]
        assert int(testsuite["@failures"]) == failures
        assert int(testsuite["@errors"]) == errors
        assert int(testsuite["@tests"]) == testsuite_tests
        assert testsuite["@name"] == testsuite_name

        cases = testsuite["testcase"]
        return cases

    @staticmethod
    def delete_test_suite(key: Callable):
        JunitTestSuite._junit_suites.pop(key)


class ExternalBaseTest(BaseTest):
    @classmethod
    @pytest.fixture(autouse=True)
    def teardown(cls):
        yield
        shutil.rmtree(REPORT_DIR, ignore_errors=True)
        JunitTestSuite._junit_suites = dict()

    @classmethod
    def get_test_report(cls, suite_name: str, args="") -> OrderedDict:
        test_report_path = REPORT_DIR.joinpath(
            JunitTestSuite.XML_REPORT_FORMAT.format(suite_name=suite_name, args=args)
        )

        with open(test_report_path) as f:
            return xmltodict.parse(f.read())

    @classmethod
    def execute_test(cls, testfile: str) -> Tuple[ExitCode, str]:
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = pytest.main([testfile])

        return exit_code, f.getvalue()


class _TestExternal(ExternalBaseTest):
    def base_flow(self, test_name: str, expected_suite_name: str):
        exit_code, _ = self.execute_test(test_name)
        assert exit_code == ExitCode.OK

        xml_results = self.get_test_report(suite_name=expected_suite_name)

        self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=3,
            testsuite_name=expected_suite_name,
            fixtures_count=1,
            functions_count=2,
        )

    def multiple_fixtures(self, test_name: str, expected_suite_name: str):
        exit_code, _ = self.execute_test(test_name)

        assert exit_code == ExitCode.OK
        xml_results = self.get_test_report(suite_name=expected_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=4,
            testsuite_name=expected_suite_name,
            fixtures_count=2,
            functions_count=2,
        )

    def nested_test_case(self, test_name: str, exec_type: str, first_suite_name: str, second_suite_name: str):
        exit_code, _ = self.execute_test(test_name)
        assert exit_code == ExitCode.TESTS_FAILED
        xml_results = self.get_test_report(suite_name=first_suite_name)

        cases = self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=4,
            testsuite_name=first_suite_name,
            fixtures_count=1,
            functions_count=3,
        )

        expected_nested_test_case = f"tests.external_tests.{exec_type}_tests._test_junit_report_nested_test_case"
        nested_test_case = [c for c in cases if c["@name"] == "get_my_fixture"].pop()
        assert nested_test_case["@classname"] == expected_nested_test_case

        xml_results = self.get_test_report(suite_name=second_suite_name)
        cases = self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=3,
            failures=1,
            testsuite_name=second_suite_name,
            fixtures_count=1,
            functions_count=2,
        )

        nested_test_case = [c for c in cases if c["@name"] == "get_my_fixture"].pop()
        expected_nested_test_case = f"tests.external_tests.{exec_type}_tests._test_junit_report_nested_test_case"
        assert nested_test_case["@classname"] == expected_nested_test_case
        assert "KeyError: 'Invalid fixture'" in nested_test_case["failure"]["#text"]

    def multiple_fixtures_with_parametrize(
        self, test_name: str, first_suite_name: str, second_suite_name: str, third_suite_name: str
    ):
        version = {"version": ["5.1", "6.21980874565", 6.5, "some__long_string_that_is_not_a_number"]}
        letter = {"letter": ["A", "B", "C"]}
        animal = {"animal": ["Dog", "Cat", "Horse", "Kangaroo"]}
        none = {"none": [None]}

        first_args = dict(**version)
        second_args = dict(**version, **letter, **animal, **none)
        third_args = dict(**version, **letter, **none)

        case_count = 3
        fixtures_count = 2

        expected_fixtures_count = fixtures_count
        expected_cases_count = case_count

        exit_code, _ = self.execute_test(test_name)
        assert exit_code == ExitCode.OK

        parametrize = list()
        for k, lst in first_args.items():
            for v in lst:
                parametrize.append((k, v))

        for tup in parametrize:
            xml_results = self.get_test_report(suite_name=first_suite_name, args=str(tup[1]))
            self.assert_xml_report_results_with_cases(
                xml_results,
                testsuite_tests=expected_fixtures_count + expected_cases_count,
                testsuite_name=first_suite_name,
                fixtures_count=expected_fixtures_count,
                functions_count=expected_cases_count,
            )

        fixtures_count = 2
        cases_count = 2

        second_args = dict(sorted(second_args.items(), key=lambda x: x[0]))
        parametrize = [list(k) for k in list(itertools.product(*[v for v in second_args.values()]))]
        for k in parametrize:
            k = [str(i) for i in k]
            xml_results = self.get_test_report(suite_name=second_suite_name, args="_".join(k))
            cases = self.assert_xml_report_results_with_cases(
                xml_results,
                testsuite_tests=fixtures_count + cases_count,
                testsuite_name=second_suite_name,
                fixtures_count=fixtures_count,
                functions_count=cases_count,
            )

            # Verify that each case name have the represented values on its name
            for c in cases:
                if c["@class"] == TestCaseCategories.FUNCTION:
                    assert "animal=" in c["@name"] and k[0] in c["@name"]
                    assert "letter=" in c["@name"] and k[1] in c["@name"]
                    assert "none=None" in c["@name"]
                    assert "version=" in c["@name"] and k[2] in c["@name"]

        fixtures_count = 1
        cases_count = 1
        expected_cases_count = fixtures_count + cases_count

        third_args = dict(sorted(third_args.items(), key=lambda x: x[0]))
        parametrize = [list(k) for k in list(itertools.product(*[v for v in third_args.values()]))]
        for k in parametrize:
            k = [str(i) for i in k]

            xml_results = self.get_test_report(suite_name=third_suite_name, args="_".join(k))
            self.assert_xml_report_results_with_cases(
                xml_results,
                testsuite_tests=expected_cases_count,
                testsuite_name=third_suite_name,
                fixtures_count=fixtures_count,
                functions_count=cases_count,
            )

    @pytest.fixture
    def files_cleaner(self):
        file_before_yield_path = "file_before_yield"
        file_in_case_path = "file_in_case"
        file_after_yield_path = "file_after_yield"
        yield
        os.remove(file_before_yield_path)
        os.remove(file_in_case_path)
        os.remove(file_after_yield_path)

    def junit_report_fixture_yield_none(self, test_name: str, expected_suite_name: str):
        expected_case_count = 0
        expected_fixtures_count = 3
        expected_failures = 0

        exit_code, _ = self.execute_test(test_name)
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

    def junit_report_fixtures_with_exceptions(self, test_name: str, first_suite_name: str, second_suite_name: str):
        expected_case_count = 0
        expected_fixtures_count = 2
        expected_failures = 1

        exit_code, _ = self.execute_test(test_name)
        assert exit_code == ExitCode.TESTS_FAILED
        xml_results = self.get_test_report(suite_name=first_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            failures=expected_failures,
            testsuite_tests=expected_fixtures_count,
            testsuite_name=first_suite_name,
            fixtures_count=expected_fixtures_count,
            functions_count=expected_case_count,
        )

        xml_results = self.get_test_report(suite_name=second_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            failures=expected_failures,
            testsuite_tests=expected_fixtures_count,
            testsuite_name=second_suite_name,
            fixtures_count=expected_fixtures_count,
            functions_count=expected_case_count,
        )

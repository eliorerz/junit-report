import io
import itertools
import os
import re
import shutil
from collections import OrderedDict
from contextlib import redirect_stdout
from pathlib import Path
from typing import Callable, List, Tuple

import pytest
import xmltodict
from _pytest.config import ExitCode

from src.junit_report import JunitFixtureTestCase, JunitTestSuite, TestCaseCategories

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
        if isinstance(cases, OrderedDict):
            return [cases]
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
    def get_test_report(cls, suite_name: str, args="", custom_filename: str = None) -> OrderedDict:
        if not suite_name.endswith(".xml"):
            test_report_path = REPORT_DIR.joinpath(
                JunitTestSuite.get_report_file_name(suite_name=suite_name, args=args, custom_filename=custom_filename)
            )
        else:
            test_report_path = REPORT_DIR.joinpath(suite_name)

        with open(test_report_path) as f:
            return xmltodict.parse(f.read())

    @classmethod
    def execute_test(cls, testfile: str, *args) -> Tuple[ExitCode, str]:
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = pytest.main([testfile] + [a for a in args])

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

    def expected_filename(self, test_name: str, expected_suite_name: str, expected_other_suite_name: str):
        exit_code, _ = self.execute_test(test_name)
        assert exit_code == ExitCode.OK
        assert self.get_test_report(suite_name=expected_suite_name, custom_filename=expected_suite_name)
        assert self.get_test_report(suite_name=expected_other_suite_name, custom_filename=expected_other_suite_name)

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

    def nested_test_case(self, test_name: str, exec_type: str, first_suite_name: str,
                         second_suite_name: str, third_suite_name: str):
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

        xml_results = self.get_test_report(suite_name=third_suite_name)
        self.assert_xml_report_results_with_cases(
            xml_results,
            testsuite_tests=2,
            failures=1,
            testsuite_name=third_suite_name,
            fixtures_count=0,
            functions_count=2,
        )

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
            cases = self.assert_xml_report_results_with_cases(
                xml_results,
                testsuite_tests=expected_fixtures_count + expected_cases_count,
                testsuite_name=first_suite_name,
                fixtures_count=expected_fixtures_count,
                functions_count=expected_cases_count,
            )
            for case in cases:
                assert len(re.compile(r"\[(.*?)]").findall(str(case["@name"]))) == 1

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
                assert len(re.compile(r"\[(.*?)]").findall(str(c["@name"]))) == 1
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

        expected_before_yield = "0"
        expected_in_case = "1"
        expected_after_yield = "2"

        yield

        with open(file_before_yield_path) as f:
            assert f.read() == expected_before_yield

        with open(file_in_case_path) as f:
            assert f.read() == expected_in_case

        with open(file_after_yield_path) as f:
            assert f.read() == expected_after_yield

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
        version = {"version": ["5.1", "2.3", "5.01", "1.3.5", "5.1", "2.3", "48.1d", "2.3", 100, "250"]}
        second_args = dict(**version)
        parametrize = list()
        for k, lst in second_args.items():
            for v in lst:
                parametrize.append((k, v))

        for tup in parametrize:
            xml_results = self.get_test_report(suite_name=second_suite_name, args=str(tup[1]))
            self.assert_xml_report_results_with_cases(
                xml_results,
                failures=expected_failures,
                testsuite_tests=expected_fixtures_count,
                testsuite_name=second_suite_name,
                fixtures_count=expected_fixtures_count,
                functions_count=expected_case_count,
            )

    def fixture_raise_exception_after_yield(self, test_name: str, expected_suite_name: str):
        expected_case_count = 2
        expected_fixtures_count = 2
        expected_failures = 1

        exit_code, _ = self.execute_test(test_name)
        assert exit_code == ExitCode.TESTS_FAILED
        xml_results = self.get_test_report(suite_name=expected_suite_name)
        cases = self.assert_xml_report_results_with_cases(
            xml_results,
            failures=expected_failures,
            testsuite_tests=expected_fixtures_count + expected_case_count,
            testsuite_name=expected_suite_name,
            fixtures_count=expected_fixtures_count,
            functions_count=expected_case_count,
        )

        expected_fixture_name = "fixture_with_exception_after_yield"
        assert len([c for c in cases if c["@name"] == expected_fixture_name]) == 1

        failed_cases = [c for c in cases if "failure" in c]
        assert len(failed_cases) == 1

        failed_case = failed_cases[0]
        assert failed_case["@name"] == expected_fixture_name
        assert failed_case["failure"]["@type"] == ValueError.__name__
        assert failed_case["failure"]["@message"].startswith(JunitFixtureTestCase.AFTER_YIELD_EXCEPTION_MESSAGE_PREFIX)

    def pytest_suite_no_junit_suite(self, test_name: str, report_name: str):
        parametrize_count = 5

        exit_code, _ = self.execute_test(test_name, f"--junit-xml={REPORT_DIR.joinpath('unittest.xml')}")
        assert exit_code == ExitCode.OK

        xml_results = self.get_test_report(suite_name=report_name)
        assert xml_results["testsuites"]["testsuite"]["@name"] == "pytest"
        assert int(xml_results["testsuites"]["testsuite"]["@tests"]) == 1 + parametrize_count
        assert int(xml_results["testsuites"]["testsuite"]["@failures"]) == 0
        assert int(xml_results["testsuites"]["testsuite"]["@errors"]) == 0

    def junit_report_suite_no_cases_with_exception(self, test_name: str, first_suite_name: str, second_suite_name: str):
        expected_case_count = 1
        expected_fixtures_count = 0
        expected_failures = 1

        exit_code, _ = self.execute_test(test_name)
        assert exit_code == ExitCode.TESTS_FAILED

        number = {"number": [1, 2, 3, 4, 5]}

        parametrize = list()
        for k, lst in number.items():
            for v in lst:
                parametrize.append((k, v))

        for tup in parametrize:
            xml_results = self.get_test_report(suite_name=first_suite_name, args=str(tup[1]))
            self.assert_xml_report_results_with_cases(
                xml_results,
                failures=expected_failures,
                testsuite_tests=expected_case_count,
                testsuite_name=first_suite_name,
                fixtures_count=expected_fixtures_count,
                functions_count=expected_case_count,
            )

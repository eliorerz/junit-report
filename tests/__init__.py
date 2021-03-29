import os
from pathlib import Path
from typing import Callable, Dict

from src.junit_report import JunitTestSuite, TestCaseCategories

try:
    os.chdir(Path().cwd().joinpath("tests"))
except FileNotFoundError:
    """ Ignore """


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
    ):
        cases = cls.assert_xml_report_results(xml_results, testsuite_tests, testsuite_name, failures, errors)

        assert len([x for x in cases if x["@class"] == TestCaseCategories.FIXTURE]) == fixtures_count
        assert len([x for x in cases if x["@class"] == TestCaseCategories.FUNCTION]) == functions_count

    @staticmethod
    def assert_xml_report_results(
        xml_results: dict,
        testsuite_tests: int,
        testsuite_name: str,
        failures=0,
        errors=0,
    ) -> Dict[str, str]:
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

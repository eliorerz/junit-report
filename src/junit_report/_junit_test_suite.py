import datetime
import os
import traceback
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Tuple, Union

import pytest
from junit_xml import TestCase, TestSuite, to_xml_report_string

from ._junit_decorator import JunitDecorator
from ._test_case_data import CaseFailure, TestCaseCategories, TestCaseData, is_case_exception_already_raised


class DuplicateSuiteError(KeyError):
    """ Test Suite decorator name is already exist in suites poll """


class JunitTestSuite(JunitDecorator):
    """
    JunitTestSuite is a decorator that waits for JunitTestCases decorators to register their testcases instances.
    After all test cases has finished their execution, the JunitTestSuite instance collect all registered TestCases
    and generate junit xml accordingly.
    JunitTestSuite represents single TestSuite.
    Generated report format: junit_<Class Name>_<Suite Function Name>_report.xml
    The usage of this function is regardless of pytest unittest packages.
    Default report path can be override if DEFAULT_REPORT_PATH_KEY environment variable is set
    """

    _junit_suites: ClassVar[Dict[Callable, "JunitTestSuite"]] = dict()
    _report_dir: Path
    _cases = List[TestCase]
    _func: Union[Callable, None]
    suite: Union[TestSuite, None]

    DEFAULT_REPORT_PATH_KEY = "JUNIT_REPORT_DIR"
    SUITE_TEST_CASE_MESSAGE_PREFIX = "[SUITE EXCEPTION]"  # Exception on suite (without test case)

    XML_REPORT_FORMAT = "junit_{suite_name}_report{args}.xml"

    def __init__(self, report_dir: Path = None, custom_filename: str = None):
        """
        :param report_dir: Target directory, created if not exists
        :param custom_filename: If set, xml report will set to <exported_filename>.xml
        """
        super().__init__()
        self._report_dir = self.get_report_dir(report_dir)
        self._cases = list()
        self.suite = None
        self._timestamp = datetime.datetime.now()
        self._has_uncollected_fixtures = False
        self._custom_filename = custom_filename
        self._self_test_case = None

    def _on_call(self):
        self._register()

    def _on_wrapper_end(self):
        self.suite = TestSuite(
            name=f"{self._get_class_name()}_{self.name}", test_cases=self._get_cases(), timestamp=self._timestamp
        )
        self._export(self.suite)

    @classmethod
    def get_report_file_name(cls, suite_name: str, args: str = None, custom_filename: str = None):
        if custom_filename:
            return f"{custom_filename}.xml"
        if args:
            return cls.XML_REPORT_FORMAT.format(suite_name=suite_name, args=f"[{args}]")
        return cls.XML_REPORT_FORMAT.format(suite_name=suite_name, args="")

    @classmethod
    def get_suite(cls, suite_key: Callable) -> Union["JunitTestSuite", None]:
        """
        Return suite if exists, None otherwise
        :param suite_key: Wrapped function as cases key
        :return:
        """
        if cls.is_suite_exist(suite_key):
            return cls._junit_suites[suite_key]
        return None

    @classmethod
    def get_report_dir(cls, report_dir: Union[Path, None]) -> Path:
        if report_dir is None:
            return Path(os.getenv(cls.DEFAULT_REPORT_PATH_KEY, Path.cwd()))
        return report_dir

    @classmethod
    def collect_all(cls):
        """
        Collect all junit test suites reports from external source
        :return: None
        """
        for junit_suite in cls._junit_suites.values():
            cls._on_wrapper_end(self=junit_suite)

    @classmethod
    def is_suite_exist(cls, suite_func: Callable):
        return suite_func in cls._junit_suites

    @classmethod
    def register_case(cls, test_data: TestCaseData, suite_func: Callable) -> None:
        """
        Register test case to the relevant test suite
        :param test_data: TestCaseData instance
        :param suite_func: Wrapped function as cases key
        :return: None
        """
        if cls.is_suite_exist(suite_func):
            suite = cls.get_suite(suite_func)
            cls._add_case(suite, test_data)
            if test_data.is_inside_fixture and test_data.had_exception:
                suite._on_wrapper_end()

    def _register(self):
        if self._func in JunitTestSuite._junit_suites:
            raise DuplicateSuiteError(f"Suite {self.name} already exist")
        JunitTestSuite._junit_suites[self._func] = self

    def _get_cases(self):
        if self._self_test_case:
            return [data.case for data in self._cases] + [self._self_test_case]
        return [data.case for data in self._cases]

    def _add_case(self, test_data):
        if test_data.case.category == "fixture":
            self._has_uncollected_fixtures = True
        return self._cases.append(test_data)

    def _get_parametrize_as_str(self) -> str:
        """
        In case of pytest parametrize, this function collect and return parametrizes values
        :return: underscore separated parametrize values
        """
        parameterize = self.get_pytest_parameterized(self._pytest_function)
        if parameterize:
            return "_".join(str(tup[1]) for tup in parameterize)
        return ""

    def get_pytest_parameterized(self, pytest_function: pytest.Function) -> List[Tuple[str, Any]]:
        parameterized = list()
        if len(self._cases) == 0:
            return self._get_parameterized_on_no_cases()
        test_cases = [test_case_data for test_case_data in self._cases if test_case_data.parametrize]
        if test_cases:
            parameterized = [k for k in set([c.get_case_key() for c in test_cases if len(c.get_case_key()) > 0]).pop()]
        return parameterized

    def _export(self, suite: TestSuite) -> None:
        """
        Export test suite to JUnit xml file
        :param suite: TestSuite to export
        :return: None
        """
        if len(suite.test_cases) == 0:
            return

        if not self._has_uncollected_fixtures:
            values = self._get_parametrize_as_str()
            path = self._report_dir.joinpath(
                self.get_report_file_name(suite_name=suite.name, args=values, custom_filename=self._custom_filename)
            )
            xml_string = to_xml_report_string([suite])

            os.makedirs(self._report_dir, exist_ok=True)
            with open(path, "w") as f:
                f.write(xml_string)

            self.clear_cases()

    def clear_cases(self):
        """ Delete all cases from suite """
        self._cases = list()
        self.suite.test_cases = list()

    @classmethod
    def fixture_cleanup(cls, test_data, suite_func: Callable):
        """
        Collect junit suite after fixture yield
        :param test_data: TestCaseData
        :param suite_func: suite key
        :return: None
        """
        junit_suite = cls.get_suite(suite_func)
        if junit_suite and junit_suite._cases:
            first_fixture = junit_suite._cases[0].case
            if first_fixture == test_data.case:
                junit_suite._collect_yield()

    def _collect_yield(self):
        """
        Export suite if exist
        :return:
        """
        self._has_uncollected_fixtures = False
        self._export(self.suite)

    def _on_exception(self, e: BaseException):
        if is_case_exception_already_raised(e):
            raise e

        self._handle_in_suite_exception(e)

    def _handle_in_suite_exception(self, exception: BaseException):
        self._self_test_case = TestCase(
            name=self._func.__name__, classname=self._get_class_name(), category=TestCaseCategories.FUNCTION.value
        )
        data = TestCaseData(_start_time=self._start_time, case=self._self_test_case, _func=self._func)
        message = "[SUITE EXCEPTION] " + str(exception)
        failure = CaseFailure(message=message, output=traceback.format_exc(), type=exception.__class__.__name__)
        data.case.failures.append(failure)
        raise

    def _get_parameterized_on_no_cases(self) -> List[Tuple[str, Any]]:
        for f_locals in [stack_local for stack_local in self._stack_locals if "pyfuncitem" in stack_local]:
            pytest_func = f_locals["pyfuncitem"]
            if hasattr(self._func, "pytestmark"):
                parameterized = [m.args[0] for m in self._func.pytestmark if m.name == "parametrize"]
                if isinstance(pytest_func, pytest.Function) and parameterized:
                    return sorted(list({k: v for k, v in pytest_func.funcargs.items() if k in parameterized}.items()))

        return []

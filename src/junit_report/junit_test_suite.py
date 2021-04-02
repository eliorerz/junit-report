import os
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Type, Union

import decorator
from junit_xml import TestCase, TestSuite, to_xml_report_string


class SuiteNotExistError(KeyError):
    """ Test Suite decorator name is not exists in suites poll """


class DuplicateSuiteError(KeyError):
    """ Test Suite decorator name is already exist in suites poll """


class JunitTestSuite:
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
    _suite: Union[TestSuite, None]
    _klass = Any

    DEFAULT_REPORT_PATH_KEY = "JUNIT_REPORT_DIR"
    FAIL_ON_MISSING_SUITE_KEY = "FAIL_ON_MISSING_SUITE"

    XML_REPORT_FORMAT = "junit_{suite_name}_report.xml"
    FAIL_ON_MISSING_SUITE = os.getenv(FAIL_ON_MISSING_SUITE_KEY, "False").lower() in ["true", "1", "yes", "y"]

    def __init__(self, report_dir: Path = None):
        """
        :param report_dir: Target directory, created if not exists
        """
        self._report_dir = self.get_report_dir(report_dir)
        self._cases = list()
        self._func = None
        self._suite = None
        self._klass = None

    @classmethod
    def get_report_dir(cls, report_dir: Union[Path, None]) -> Path:
        if report_dir is None:
            return Path(os.getenv(cls.DEFAULT_REPORT_PATH_KEY, Path.cwd()))
        return report_dir

    def __call__(self, function: Callable):
        """
        Execute test suite decorated function and export the results to junit xml file
        :param function: Decorated test suite function
        :return: Converted caller function into a decorator
        """
        self._func = function
        self._register(function)

        def wrapper(_, obj: Any, *args, **kwargs):
            """
            :param _:  @ignored - Decorated test suite function -
            :param obj: Test class containing the test suite
            :param args: Function given arguments
            :param kwargs: Function given keyword arguments
            :return: Function return value
            """
            try:
                value = function(obj, *args, **kwargs)
            except BaseException:
                raise
            finally:
                self._collect(obj.__class__)
            return value

        return decorator.decorator(wrapper, function)

    @property
    def name(self):
        if self._func:
            return self._func.__name__
        return ""

    def _register(self, function: Callable):
        if function in JunitTestSuite._junit_suites:
            raise DuplicateSuiteError(f"Suite {function.__name__} already exist")
        JunitTestSuite._junit_suites[function] = self

    def _get_cases(self):
        return self._cases

    def _add_case(self, test_case: TestCase):
        return self._cases.append(test_case)

    @classmethod
    def collect_all(cls):
        """
        Collect all junit test suites reports from external source
        :return: None
        """
        for junit_suite in cls._junit_suites.values():
            junit_suite._suite = TestSuite(
                name=f"fixture_{junit_suite.name}",
                test_cases=cls._get_cases(junit_suite),
            )

            cls._export(junit_suite)

    def _collect(self, klass: Type[object]):
        """
        Collect all TestCases that
        :param klass: Class of which the decorated function contained in it
        :return: None
        """
        self._suite = TestSuite(
            name=f"{klass.__name__}_{self.name}",
            test_cases=self._cases,
        )
        self._export()

    def _export(self) -> None:
        path = self._report_dir.joinpath(self.XML_REPORT_FORMAT.format(suite_name=self._suite.name))
        xml_string = to_xml_report_string([self._suite])

        os.makedirs(self._report_dir, exist_ok=True)
        with open(path, "w") as f:
            f.write(xml_string)

    @classmethod
    def is_suite_exist(cls, suite_func: Callable):
        return suite_func in cls._junit_suites

    @classmethod
    def register_case(cls, test_case, suite_func: Callable) -> None:
        """
        Register test case to the relevant test suite
        :param test_case: TestCase instance
        :param suite_func: Wrapped function as cases key
        :return: None
        """
        if cls.is_suite_exist(suite_func):
            cls._add_case(cls._junit_suites[suite_func], test_case)
        else:
            if cls.FAIL_ON_MISSING_SUITE:
                raise SuiteNotExistError(f"Can't find suite named {suite_func} for {test_case} test case")

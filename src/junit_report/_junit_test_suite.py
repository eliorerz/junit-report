import os
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Union

from junit_xml import TestCase, TestSuite, to_xml_report_string

from ._junit_decorator import JunitDecorator


class SuiteNotExistError(KeyError):
    """ Test Suite decorator name is not exists in suites poll """


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

    _junit_suites: ClassVar[Dict[Callable, Dict]] = dict()
    _report_dir: Path
    _cases = List[TestCase]
    _func: Union[Callable, None]
    _suite: Union[TestSuite, None]

    DEFAULT_REPORT_PATH_KEY = "JUNIT_REPORT_DIR"
    FAIL_ON_MISSING_SUITE_KEY = "FAIL_ON_MISSING_SUITE"

    XML_REPORT_FORMAT = "junit_{suite_name}_report{args}.xml"
    FAIL_ON_MISSING_SUITE = os.getenv(FAIL_ON_MISSING_SUITE_KEY, "False").lower() in ["true", "1", "yes", "y"]

    def __init__(self, report_dir: Path = None):
        """
        :param report_dir: Target directory, created if not exists
        """
        super().__init__()
        self._report_dir = self.get_report_dir(report_dir)
        self._cases = list()
        self._klass = None

    def _on_call(self):
        self._register()

    def _on_wrapper_end(self):
        self._collect(self._get_class_name())

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
            suite = TestSuite(
                name=f"fixture_{junit_suite.name}",
                test_cases=cls._get_cases(junit_suite),
            )

            cls._export(junit_suite, suite)

    @classmethod
    def is_suite_exist(cls, suite_func: Callable):
        return suite_func in cls._junit_suites

    @classmethod
    def register_case(cls, test_data, suite_func: Callable) -> None:
        """
        Register test case to the relevant test suite
        :param test_data: TestCaseData instance
        :param suite_func: Wrapped function as cases key
        :return: None
        """
        if cls.is_suite_exist(suite_func):
            cls._add_case(cls._junit_suites[suite_func], test_data)
        else:
            if cls.FAIL_ON_MISSING_SUITE:
                raise SuiteNotExistError(f"Can't find suite named {suite_func} for {test_data} test case")

    def _execute_wrapped_function(self, *args, **kwargs) -> Any:
        return super()._execute_wrapped_function(*args, **kwargs)

    def _register(self):
        if self._func in JunitTestSuite._junit_suites:
            raise DuplicateSuiteError(f"Suite {self.name} already exist")
        JunitTestSuite._junit_suites[self._func] = self

    def _get_cases(self):
        return [data.case for data in self._cases]

    def _add_case(self, test_data):
        return self._cases.append(test_data)

    def _collect(self, class_name: str):
        """
        Collect all TestCases that
        :param class_name: Class name of which the decorated function contained in it
        :return: None
        """
        suite = TestSuite(
            name=f"{class_name}_{self.name}",
            test_cases=self._get_cases(),
        )
        self._export(suite)

    def _get_parametrize_values(self):
        values = ""
        parametrize = [p for p in self._cases if p.parametrize is not None]
        if parametrize:
            marks = {c.get_case_key() for c in self._cases if len(c.get_case_key()) > 0}
            if marks:
                values = "_".join([str(tup[1]) for tup in marks.pop()])
        return values

    def _export(self, suite: TestSuite) -> None:
        if len(suite.test_cases) == 0:
            return
        values = self._get_parametrize_values()
        path = self._report_dir.joinpath(self.XML_REPORT_FORMAT.format(suite_name=suite.name, args=values))
        xml_string = to_xml_report_string([suite])

        os.makedirs(self._report_dir, exist_ok=True)
        with open(path, "w") as f:
            f.write(xml_string)

        self._cases = list()

import inspect
import time
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple, Union

from junit_xml import TestCase

from ._junit_decorator import JunitDecorator
from ._junit_test_suite import JunitTestSuite


@dataclass
class CaseFailure:
    message: str
    output: str = ""
    type: str = ""

    def __getitem__(self, item):
        return self.__getattribute__(item)


@dataclass
class TestCaseData:
    case: TestCase
    _func: Callable
    _start_time: float
    parametrize: Union[None, List[Tuple[str, Any]]] = None
    _has_parent = False

    @property
    def name(self):
        return self._func.__name__

    @property
    def has_parent(self):
        return self._has_parent

    def set_fin_time(self):
        self.case.elapsed_sec = time.time() - self._start_time

    def get_case_key(self):
        if self.parametrize:
            return tuple(sorted(self.parametrize))
        return ()

    def set_parametrize(self, params: List[Tuple[str, Any]]):
        self.parametrize = params
        self.case.name += f'({", ".join([f"{p[0]}={p[1]}" for p in params])})'

    def set_parent(self, case_parent_name: str):
        self._has_parent = True
        self.case.classname = f"{self.case.classname}.{case_parent_name}"


class TestCaseCategories:
    FUNCTION = "function"
    FIXTURE = "fixture"


class JunitTestCase(JunitDecorator):
    """
    JunitTestCase is a decorator that represents single TestCase.
    When the decorated function finished its execution, it's registered to the relevant JunitTestSuite.
    TestCase will fail (TestCase failure) only when exception occurs during execution.
    """

    _func: Union[Callable, None]
    _stack_locals: List[Dict[str, Any]]
    _data: Union[TestCaseData, None]

    def __init__(self) -> None:
        super().__init__()
        self._stack_locals = list()
        self._data = None

    @property
    def name(self):
        if self._func:
            return self._data.name

    def _on_wrapper_start(self, function):
        self._stack_locals = [frame_info.frame.f_locals for frame_info in inspect.stack()]
        start_time = time.time()
        case = TestCase(name=function.__name__, classname=self._get_class_name(), category=TestCaseCategories.FUNCTION)
        self._data = TestCaseData(_start_time=start_time, case=case, _func=function)

    def _add_failure(self, e: BaseException, message_prefix: str = ""):
        message = f"{message_prefix} {str(e)}" if message_prefix else str(e)
        failure = CaseFailure(message=message, output=traceback.format_exc(), type=e.__class__.__name__)
        self._data.case.failures.append(failure)

    def _on_exception(self, e: BaseException):
        self._add_failure(e)
        raise

    def _on_wrapper_end(self):
        self._data.set_fin_time()
        JunitTestSuite.register_case(self._data, self.get_suite_key())

    def get_suite_key(self) -> Union[Callable, None]:
        """
        Get suite function as unique key.
        This function handles also on case that the test suite function decorated with pytest.mark.parametrize and
        collect its parameters and record them into the test case.
        :return: Wrapped Suite function instance
        """
        try:
            suite_func = self._get_suite()
            return suite_func
        except AttributeError:
            if JunitTestSuite.FAIL_ON_MISSING_SUITE:
                raise
        return None

    def _get_suite(self):
        suite_arguments = dict()
        suite_func = None

        for f_locals in [
            stack_local for stack_local in self._stack_locals if "function" in stack_local and "self" in stack_local
        ]:
            suite = f_locals["self"]
            if isinstance(suite, JunitTestCase) and f_locals["function"].__name__ != self.name:
                if not self._data.has_parent:
                    self._data.set_parent(f_locals["function"].__name__)

            if isinstance(suite, JunitTestSuite):
                suite_func = f_locals["function"]
                stack_keys = list(inspect.signature(suite_func).parameters.keys())
                for stack in self._stack_locals:
                    if all(key in stack for key in stack_keys):
                        suite_arguments = stack
                        break

                self.__set_parametrize(suite_func, suite_arguments)
                return suite_func

        return suite_func

    def __set_parametrize(self, suite_func: Callable, suite_arguments: Dict[str, Any]):
        """
        Grab and set current JunitTestCase parametrize values
        :param suite_func: Parametrize wrapped suite function
        :param suite_arguments: Arguments passed to the function
        :return:
        """
        if hasattr(suite_func, "pytestmark"):
            params = list()
            marks = [m for m in suite_func.pytestmark if m.name == "parametrize"]

            for i in range(len(marks)):
                arg = marks[len(marks) - i - 1].args[0]
                params.append((arg, suite_arguments[arg]))
            self._data.set_parametrize(params)

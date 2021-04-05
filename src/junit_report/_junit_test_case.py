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
    case: Union[TestCase, None]
    func: Union[Callable, None]
    start_time: float
    parametrize: Union[None, List[Tuple[str, Any]]] = None

    @property
    def name(self):
        return self.func.__name__

    def set_fin_time(self):
        self.case.elapsed_sec = time.time() - self.start_time

    def get_case_key(self):
        if self.parametrize:
            return tuple(sorted(self.parametrize))
        return ()


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

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self):
        if self._func:
            return self.data.name

    def _on_wrapper_start(self, function):
        start_time = time.time()
        case = TestCase(name=function.__name__, classname=self._get_class_name(), category=TestCaseCategories.FUNCTION)
        self.data = TestCaseData(start_time=start_time, case=case, func=function)

    def _on_exception(self, e: BaseException):
        failure = CaseFailure(message=str(e), output=traceback.format_exc(), type=e.__class__.__name__)
        self.data.case.failures.append(failure)
        raise

    def _on_wrapper_end(self):
        self.data.set_fin_time()
        JunitTestSuite.register_case(self.data, self.get_suite_key())
        if self.data.parametrize:
            self.data.case.name += f'({", ".join([f"{p[0]}={p[1]}" for p in self.data.parametrize])})'

    def get_suite_key(self) -> Callable:
        """
        Get suite function as unique key.
        This function handles also on case that the test suite function decorated with pytest.mark.parametrize and
        collect its parameters and record them into the test case.
        :return: Wrapped Suite function instance
        """
        stack_locals = [frame_info.frame.f_locals for frame_info in inspect.stack()]
        suite_func = self._get_class_suite(stack_locals)
        if suite_func is None:
            suite_func = self._get_module_suite(stack_locals)
        return suite_func

    def _get_class_suite(self, stack_locals: List[Dict[str, Any]]):
        suite_func = None

        for f_locals in [
            stack_local for stack_local in stack_locals if "function" in stack_local and "self" in stack_local
        ]:
            suite = f_locals["self"]
            if isinstance(suite, JunitTestSuite):
                suite_func = f_locals["function"]
                stack_keys = list(inspect.signature(suite_func).parameters.keys())
                suite_arguments = [stack for stack in stack_locals if all(key in stack for key in stack_keys)][0]

                self.__set_parametrize(suite_func, suite_arguments)
                return suite_func

        return suite_func

    def _get_module_suite(self, stack_locals: List[Dict[str, Any]]):
        suite_func = None

        for f_locals in [
            stack_local
            for stack_local in stack_locals
            if "item" in stack_local and "nextitem" in stack_local and stack_local["item"].name == self.data.name
        ]:
            module = f_locals["nextitem"].parent
            suite_func = getattr(module.obj, f_locals["nextitem"].name).__wrapped__
            return suite_func

        return suite_func

    def __set_parametrize(self, suite_func, suite_arguments):
        if hasattr(suite_func, "pytestmark"):
            prams = list()
            marks = [m for m in suite_func.pytestmark if m.name == "parametrize"]

            for i in range(len(marks)):
                arg = marks[len(marks) - i - 1].args[0]
                prams.append((arg, suite_arguments[arg]))
            self.data.parametrize = prams

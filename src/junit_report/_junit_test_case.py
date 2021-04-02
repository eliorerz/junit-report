import inspect
import time
import traceback
from dataclasses import dataclass
from typing import Any, Callable, List, Tuple, Union, Dict

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
    _case: Union[TestCase, None]
    _parametrize: Union[None, List[Tuple[str, Any]]]

    def __init__(self) -> None:
        super().__init__()
        self._case = None
        self._start_time = None
        self._parametrize = None

    @property
    def name(self):
        if self._func:
            return self._func.__name__

    def _on_wrapper_start(self, *args):
        self._start_time = time.time()
        self._case = TestCase(name=self.name, classname=self._get_class_name(*args),
                              category=TestCaseCategories.FUNCTION)

    def _on_exception(self, e: BaseException):
        failure = CaseFailure(message=str(e), output=traceback.format_exc(), type=e.__class__.__name__)
        self._case.failures.append(failure)
        raise

    def _on_wrapper_end(self, *args):
        self._case.elapsed_sec = time.time() - self._start_time
        JunitTestSuite.register_case(self._case, self.get_suite_key())
        if self._parametrize:
            self._case.name += f'({", ".join([f"{p[0]}={p[1]}" for p in self._parametrize])})'

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
                suite_arguments = [s for s in stack_locals if
                                   all(n in s for n in list(inspect.signature(suite_func).parameters.keys()))][0]

                self.__set_parametrize(suite_func, suite_arguments)
                return suite_func

        return suite_func

    def _get_module_suite(self, stack_locals: List[Dict[str, Any]]):
        suite_func = None

        for f_locals in [stack_local for stack_local in stack_locals if
                         "item" in stack_local and "nextitem" in stack_local and stack_local[
                             "item"].name == self._func.__name__]:
            module = f_locals['nextitem'].parent
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
            self._parametrize = prams

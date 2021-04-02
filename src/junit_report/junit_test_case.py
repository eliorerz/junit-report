import inspect
import time
import traceback
from dataclasses import dataclass
from typing import Any, Callable, List, Tuple, Union

import decorator
from junit_xml import TestCase

from .junit_test_suite import JunitTestSuite


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


class JunitTestCase:
    """
    JunitTestCase is a decorator that represents single TestCase.
    When the decorated function finished its execution, it's registered to the relevant JunitTestSuite.
    TestCase will fail (TestCase failure) only when exception occurs during execution.
    """

    _func: Union[Callable, None]
    _case: Union[TestCase, None]
    _parametrize: Union[None, List[Tuple[str, Any]]]

    def __init__(self) -> None:
        self._case = None
        self._func = None
        self._parametrize = None

    @property
    def name(self):
        if self._func:
            return self._func.__name__

    def _execute_function(self, function: Callable, obj: Any, *args, **kwargs):
        return function(obj, *args, **kwargs)

    def _wrapper(self, function: Callable, obj: Any, *args, **kwargs):
        """
        :param _:  @ignored - Decorated test suite function -
        :param obj: Class instance of which the decorated function contained in it
        :param args: Arguments passed to the function
        :param kwargs: Arguments passed to the function
        :return: function results
        """
        start = time.time()
        self._case = TestCase(name=self.name, classname=obj.__class__.__name__, category=TestCaseCategories.FUNCTION)
        try:
            value = self._execute_function(function, obj, *args, **kwargs)
        except BaseException as e:
            failure = CaseFailure(message=str(e), output=traceback.format_exc(), type=e.__class__.__name__)
            self._case.failures.append(failure)
            raise
        finally:
            self._case.elapsed_sec = time.time() - start
            self._finalize()
        return value

    def __call__(self, function: Callable) -> Callable:
        """
        Create a TestCase object for each executed decorated test case function and register it into the relevant
        JunitTestSuite object.
        If exception accrues during function execution, the exception is recorded as junit case failure (CaseFailure)
        and raises it.
        Execution time is being recorded and saved into the TestCase instance.
        :param function: Decorated function
        :return: Wrapped function
        """
        self._func = function

        def wrapper(_, obj: Any, *args, **kwargs):
            return self._wrapper(function, obj, *args, **kwargs)

        return decorator.decorator(wrapper, function)

    def _finalize(self):
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
        suite_func = None
        stack_locals = [frame_info.frame.f_locals for frame_info in inspect.stack()]
        for f_locals in [
            stack_local for stack_local in stack_locals if "function" in stack_local and "self" in stack_local
        ]:
            suite = f_locals["self"]
            if isinstance(suite, JunitTestSuite):
                suite_func = f_locals["function"]
                suite_arguments = [s for s in stack_locals if
                                   all(n in s for n in list(inspect.signature(suite_func).parameters.keys()))][0]

                self.__set_parametrize(suite_func, suite_arguments)
                break

        return suite_func

    def __set_parametrize(self, suite_func, suite_arguments):
        if hasattr(suite_func, "pytestmark"):
            prams = list()
            marks = [m for m in suite_func.pytestmark if m.name == "parametrize"]

            for i in range(len(marks)):
                arg = marks[len(marks) - i - 1].args[0]
                prams.append((arg, suite_arguments[arg]))
            self._parametrize = prams

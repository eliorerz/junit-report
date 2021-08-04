import traceback
from contextlib import suppress
from typing import Any, Callable, Dict, List, Union

from _pytest.python import Function
from junit_xml import TestCase

from . import _utils
from ._junit_decorator import JunitDecorator
from ._junit_test_suite import JunitTestSuite
from ._test_case_data import CaseFailure, TestCaseCategories, TestCaseData, is_case_exception_already_raised


class JunitTestCase(JunitDecorator):
    """
    JunitTestCase is a decorator that represents single TestCase.
    When the decorated function finished its execution, it's registered to the relevant JunitTestSuite.
    TestCase will fail (TestCase failure) only when exception occurs during execution.
    """

    _func: Union[Callable, None]
    _stack_locals: List[Dict[str, Any]]
    _case_data: Union[TestCaseData, None]

    def __init__(self) -> None:
        super().__init__()
        self._case_data = None
        self._is_inside_fixture = False

    @property
    def name(self):
        if self._func:
            return self._case_data.name

    def _on_wrapper_start(self, function):
        super()._on_wrapper_start(function)
        case = TestCase(name=function.__name__, classname=self._get_class_name(),
                        category=TestCaseCategories.FUNCTION.value)
        self._case_data = TestCaseData(_start_time=self._start_time, case=case, _func=function)

    def _add_failure(self, e: BaseException, message_prefix: str = ""):
        message = f"{message_prefix} {str(e)}" if message_prefix else str(e)
        failure = CaseFailure(message=message, output=traceback.format_exc(), type=e.__class__.__name__)
        self._case_data.case.failures.append(failure)

    def _on_exception(self, e: BaseException):
        self._case_data.had_exception = True
        if is_case_exception_already_raised(e):
            raise  # already registered on son test case
        setattr(e, "__is_junit_exception__", True)
        self._add_failure(e)
        raise e

    def _on_wrapper_end(self) -> bool:
        self._case_data.set_fin_time()
        suite_func = self.get_suite_key()
        if suite_func is None:
            return False
        JunitTestSuite.register_case(self._case_data, suite_func)
        return True

    def get_suite_key(self) -> Union[Callable, None]:
        """
        Get suite function as unique key.
        This function handles also on case that the test suite function decorated with pytest.mark.parametrize and
        collect its parameters and record them into the test case.
        :return: Wrapped Suite function instance
        """
        with suppress(AttributeError):
            suite_func = self._get_suite()
            return suite_func

        return None

    def _set_parameterized(self, pytest_function: Function):
        parameterized = self.get_pytest_parameterized(pytest_function)

        if parameterized and not self._case_data.parametrize:
            self._case_data.set_parametrize(parameterized)

    def _get_suite(self):
        stack_locals = [stack_local for stack_local in self._stack_locals if "self" in stack_local]
        function_locals = [stack_local for stack_local in stack_locals if "function" in stack_local]

        self._set_parameterized(self._pytest_function)
        is_inside_fixture = False

        suite_func = self._get_function_suite(function_locals)
        if suite_func is None:
            is_inside_fixture = True
            suite_func = self._get_fixture_suite(self._pytest_function)
            # test case inside fixture with suite_func - if also exception - that is our case

        self._case_data.is_inside_fixture = is_inside_fixture
        self._is_inside_fixture = is_inside_fixture
        return suite_func

    def _get_function_suite(self, function_locals: List[Dict[str, Any]]):
        suite_func = None

        for f_locals in function_locals:
            suite = f_locals["self"]
            if isinstance(suite, JunitTestCase) and f_locals["function"].__name__ != self.name:
                if not self._case_data.has_parent:
                    self._case_data.set_parent(f_locals["function"].__name__)

            if isinstance(suite, JunitTestSuite):
                suite_func = f_locals["function"]
                break
        return suite_func

    @staticmethod
    def _get_fixture_suite(func: Function):
        with suppress(AttributeError):
            # if pytest.mark.parametrize exist, get actual function from class while ignoring the add parameters
            if hasattr(func, "own_markers") and len(func.own_markers) > 0:
                mark_function = _utils.get_fixture_mark_function(func.own_markers, func)
                if mark_function:
                    return mark_function
            return _utils.get_wrapped_function(func)

        return None

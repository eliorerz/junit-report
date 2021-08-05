import traceback
from contextlib import suppress
from typing import Any, Callable, Dict, List, Union

import pytest

from ._junit_decorator import JunitDecorator
from ._junit_test_suite import JunitTestSuite
from .utils import TestCaseCategories, TestCaseData, CaseFailure, Utils, PytestUtils


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
        super()._on_wrapper_start(function)
        case = Utils.get_new_test_case(function, self._get_class_name(), TestCaseCategories.FUNCTION)
        self._data = TestCaseData(_start_time=self._start_time, case=case, _func=function)

    def _add_failure(self, e: BaseException, message_prefix: str = ""):
        message = f"{message_prefix} {str(e)}" if message_prefix else str(e)
        failure = CaseFailure(message=message, output=traceback.format_exc(), type=e.__class__.__name__)
        self._data.case.failures.append(failure)

    def _on_exception(self, e: BaseException):
        if Utils.is_case_exception_already_raised(e):
            raise  # already registered on son test case
        Utils.mark_case_exception_as_raised(e)
        self._add_failure(e)
        raise e

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
        with suppress(AttributeError):
            suite_func = self.get_suite()
            return suite_func

        return None

    def _set_parameterized(self, pytest_function: pytest.Function, parameterized: List = None):
        if not parameterized:
            parameterized = PytestUtils.get_case_pytest_parameterized(pytest_function)

        if parameterized and not self._data.parametrize:
            self._data.set_parametrize(parameterized)

    def get_suite(self):
        stack_locals = [stack_local for stack_local in self._stack_locals if "self" in stack_local]
        function_locals = [stack_local for stack_local in stack_locals if "function" in stack_local]
        pytest_function = [
            stack_local
            for stack_local in self._stack_locals
            if "self" in stack_local and isinstance(stack_local["self"], pytest.Function)][0]["self"]

        self._set_parameterized(pytest_function)
        is_inside_fixture = False

        suite_func = self._get_function_suite(function_locals)
        if suite_func is None:
            is_inside_fixture = True
            suite_func = PytestUtils.get_fixture_suite(pytest_function)
            fixture_params = PytestUtils.get_fixture_parameterized(pytest_function)
            if fixture_params:
                self._set_parameterized(pytest_function, fixture_params)

        self._data.is_inside_fixture = is_inside_fixture
        return suite_func

    def _get_function_suite(self, function_locals: List[Dict[str, Any]]):
        suite_func = None

        for f_locals in function_locals:
            suite = f_locals["self"]
            if isinstance(suite, JunitTestCase) and f_locals["function"].__name__ != self.name:
                if not self._data.has_parent:
                    self._data.set_parent(f_locals["function"].__name__)

            if isinstance(suite, JunitTestSuite):
                suite_func = f_locals["function"]
                break
        return suite_func

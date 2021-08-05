import time
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any, Tuple, List, Union, Dict

import pytest
from junit_xml import TestCase


class TestCaseCategories(Enum):
    SUITE = "suite-function"
    FUNCTION = "function"
    FIXTURE = "fixture"
    FIXTURE_TEARDOWN = "fixture-teardown"


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
        """ return immutable key """
        if self.parametrize:
            return tuple(sorted(self.parametrize))
        return ()

    def set_parametrize(self, params: List[Tuple[str, Any]]):
        self.parametrize = params
        self.case.name += f'({", ".join([f"{p[0]}={p[1]}" for p in params])})'

    def set_parent(self, case_parent_name: str):
        self._has_parent = True
        self.case.classname = f"{self.case.classname}.{case_parent_name}"


class Utils(ABC):
    JUNIT_EXCEPTION_ON_TAG = "__is_junit_exception__"

    @staticmethod
    def get_new_test_case(func: Callable, classname: str, category: TestCaseCategories) -> TestCase:
        return TestCase(name=func.__name__, classname=classname, category=category.value)

    @classmethod
    def is_case_exception_already_raised(cls, exception: BaseException) -> bool:
        return hasattr(exception, cls.JUNIT_EXCEPTION_ON_TAG)

    @classmethod
    def mark_case_exception_as_raised(cls, exception: BaseException):
        setattr(exception, cls.JUNIT_EXCEPTION_ON_TAG, True)


class PytestUtils:
    PARAMETERIZED_KEY = "parametrize"

    @staticmethod
    def get_case_pytest_parameterized(cls, pytest_function: pytest.Function) -> List[Tuple[str, Any]]:
        return (list(
            sorted(pytest_function.callspec.params.items())) if pytest_function and pytest_function.own_markers and all(
            m.name == cls.PARAMETERIZED_KEY for m in pytest_function.own_markers) else list())

    @classmethod
    def get_suite_pytest_parameterized(cls,
                                       cases_data: List[TestCaseData],
                                       func: Callable,
                                       stack_locals: List[Dict[str, Any]]
                                       ) -> List[Tuple[str, Any]]:
        parameterized = list()
        if len(cases_data) == 0:
            return cls._get_parameterized_on_no_cases(func, stack_locals)
        test_cases = [test_case_data for test_case_data in cases_data if test_case_data.parametrize]
        if test_cases:
            parameterized = [k for k in set([c.get_case_key() for c in test_cases if len(c.get_case_key()) > 0]).pop()]
        return parameterized

    @classmethod
    def _get_parameterized_on_no_cases(cls, func: Callable, stack_locals) -> List[Tuple[str, Any]]:
        for f_locals in [stack_local for stack_local in stack_locals if "pyfuncitem" in stack_local]:
            pytest_func = f_locals["pyfuncitem"]
            if hasattr(func, "pytestmark"):
                parameterized = [m.args[0] for m in func.pytestmark if m.name == cls.PARAMETERIZED_KEY]
                if isinstance(pytest_func, pytest.Function) and parameterized:
                    return sorted(list({k: v for k, v in pytest_func.funcargs.items() if k in parameterized}.items()))

        return list()

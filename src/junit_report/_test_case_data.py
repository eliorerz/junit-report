import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Tuple, Union

from junit_xml import TestCase


JUNIT_EXCEPTION_ON_TAG = "__is_junit_exception__"


class TestCaseCategories(Enum):
    FUNCTION = "function"
    FIXTURE = "fixture"


class MainRunner(Enum):
    PYTEST = "pytest"
    PYTHON = "python"
    NONE = "none"


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
    is_inside_fixture = False
    had_exception = False

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
        self.case.name += f'[{", ".join([f"{p[0]}={p[1]}" for p in params])}]'

    def set_parent(self, case_parent_name: str):
        self._has_parent = True
        self.case.classname = f"{self.case.classname}.{case_parent_name}"


def is_case_exception_already_raised(exception: BaseException) -> bool:
    return hasattr(exception, JUNIT_EXCEPTION_ON_TAG)

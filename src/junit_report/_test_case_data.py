import time
from dataclasses import dataclass
from typing import Any, Callable, List, Tuple, Union

from junit_xml import TestCase


class TestCaseCategories:
    FUNCTION = "function"
    FIXTURE = "fixture"


class JunitCaseException(BaseException):
    def __init__(self, exception: BaseException, *args: object) -> None:
        super().__init__(*args)
        self.exception: BaseException = exception


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
        self.case.name += f'[{", ".join([f"{p[0]}={p[1]}" for p in params])}]'

    def set_parent(self, case_parent_name: str):
        self._has_parent = True
        self.case.classname = f"{self.case.classname}.{case_parent_name}"

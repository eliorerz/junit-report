import re
from typing import Callable, List, Union

from _pytest.mark import Mark
from _pytest.python import Function

from ._junit_test_suite import JunitTestSuite


def is_suite_exist(obj: Union, func_name: str):
    if obj is None:
        return False

    func = getattr(obj, func_name)
    if hasattr(func, "__wrapped__"):
        return JunitTestSuite.is_suite_exist(func.__wrapped__)
    return False


def get_fixture_mark_function(own_markers: List[Mark], func: Function) -> Union[Callable, None]:
    """
    If mark parameterize decorate test suite with given fixture _get_mark_function is searching
    for all parametrize arguments and permutations.
    If mark type is parametrize, set self._parametrize with the current argument permutation.
    The representation of function name and arguments for N parametrize marks are as followed:
        func.name = some_func_name[param1-param2-...-paramN]
    :param own_markers: Pytest markers taken from func stack_locals
    :param func: wrapped function contained with pytest Function object
    :return: wrapped function itself
    """
    marks = [m for m in own_markers if m.name == "parametrize"]
    marks_count = len(marks)

    if marks_count == 0:
        return None

    params_regex = "-".join(["(.*?)"] * marks_count)
    args = list(re.compile(r"(.*?)\[{0}]".format(params_regex)).findall(func.name).pop())
    func_name = args.pop(0)

    params = list()
    for i in range(marks_count):
        params.append((marks[i].args[0], args[i]))

    return get_wrapped_function(func, func_name)


def get_wrapped_function(func: Function, func_name: str = None) -> Callable:
    """
    Get wrapped function from class or module
    :param func: wrapped function from class or module
    :param func_name: If there is pytest parameterized suite name is needed
    :return:
    """
    if func_name is None:
        func_name = func.name

    if func.cls:
        return getattr(func.cls, func_name).__wrapped__
    return getattr(func.module, func_name).__wrapped__

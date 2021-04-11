import re
from types import GeneratorType
from typing import Callable, List, Union

import decorator
from _pytest.mark import Mark
from _pytest.python import Function

from ._junit_test_case import JunitTestCase, TestCaseCategories
from ._junit_test_suite import JunitTestSuite


class JunitFixtureTestCase(JunitTestCase):
    """
    This class defines TestCase for pytest fixtures.
    When use, need to make sure that the fixture come first, for example:
        @pytest.fixture
        @JunitFixtureTestCase()
        def my_fixture()
            ...
    """

    _generator: Union[GeneratorType, None]

    AFTER_YIELD_EXCEPTION_MESSAGE_PREFIX = "[TEARDOWN EXCEPTION]"

    def __init__(self) -> None:
        super().__init__()
        self._generator = None

    def __call__(self, function: Callable) -> Callable:
        self._func = function

        def wrapper(_, *args, **kwargs):
            value = self._wrapper(function, *args, **kwargs)
            yield value
            try:
                if self._generator:
                    self._teardown_yield_fixture(self._generator)
            except BaseException as e:
                self._add_failure(e, self.AFTER_YIELD_EXCEPTION_MESSAGE_PREFIX)
                raise
            finally:
                JunitTestSuite.fixture_cleanup(self._data, self.get_suite_key())

        return decorator.decorator(wrapper, function)

    @classmethod
    def _teardown_yield_fixture(cls, it) -> None:
        """Execute the teardown of a fixture function by advancing the iterator
        after the yield and ensure the iteration ends (if not it means there is
        more than one yield in the function)."""
        try:
            next(it)
        except StopIteration:
            pass

    def _execute_wrapped_function(self, *args, **kwargs):
        generator = super()._execute_wrapped_function(*args, **kwargs)
        try:
            self._generator = generator
            return next(generator)
        except (StopIteration, TypeError):
            return None

    def _on_wrapper_end(self):
        """
        Fixtures executing before the test suite, due to that issue the suite can't collect the fixture case
        if there is an exception during it's execution. If exception occur, it call JunitTestSuite class method
        collect_all that trigger the suite to collect all cases and export them into xml
        :return: None
        """
        self._data.case.category = TestCaseCategories.FIXTURE

        super(JunitFixtureTestCase, self)._on_wrapper_end()
        if len(self._data.case.failures) > 0:
            JunitTestSuite.collect_all()

    def _get_suite(self) -> Union[Callable, None]:
        """
        Get suite function as unique key.
        This function handles also on case that the test suite function decorated with pytest.mark.parametrize
        :return: Wrapped Suite function instance
        """

        for f_locals in [
            stack_local
            for stack_local in self._stack_locals
            if "self" in stack_local and isinstance(stack_local["self"], Function)
        ]:
            func = f_locals["self"]

            try:
                # if pytest.mark.parametrize exist, get actual function from class while ignoring the add parameters
                if hasattr(func, "own_markers") and len(func.own_markers) > 0:
                    mark_function = self._get_mark_function(func.own_markers, func)
                    if mark_function:
                        return mark_function

                if func.cls and self._is_suite_exist(func.cls, func.name):
                    return getattr(func.cls, func.name).__wrapped__

                if func.cls is None and self._is_suite_exist(func.module, func.name):
                    return getattr(func.module, func.name).__wrapped__
            except AttributeError:
                pass

        return None

    @classmethod
    def _is_suite_exist(cls, obj: Union, func_name: str):
        func = getattr(obj, func_name)
        if hasattr(func, "__wrapped__"):
            return JunitTestSuite.is_suite_exist(func.__wrapped__)
        return False

    def _get_mark_function(self, own_markers: List[Mark], func: Function) -> Union[Callable, None]:
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

        if func.cls:
            return getattr(func.cls, func_name).__wrapped__
        else:
            return getattr(func.module, func_name).__wrapped__

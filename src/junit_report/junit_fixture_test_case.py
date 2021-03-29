import inspect
import re
from typing import Callable, List, Union

from _pytest.mark import Mark
from _pytest.python import Function

from .junit_test_case import JunitTestCase, TestCaseCategories
from .junit_test_suite import JunitTestSuite


class JunitFixtureTestCase(JunitTestCase):
    """
    This class defines TestCase for pytest fixtures.
    When use, need to make sure that the fixture come first, for example:
        @pytest.fixture
        @JunitFixtureTestCase()
        def my_fixture()
            ...
    """

    def _finalize(self):
        """
        Fixtures executing before the test suite, due to that issue the suite can't collect the fixture case
        if there is an exception during it's execution. If exception occur, it call JunitTestSuite class method
        collect_all that trigger the suite to collect all cases and export them into xml
        :return: None
        """
        self._case.category = TestCaseCategories.FIXTURE

        super(JunitFixtureTestCase, self)._finalize()
        if len(self._case.failures) > 0:
            JunitTestSuite.collect_all()

    def get_suite_key(self) -> Union[Callable, None]:
        """
        Get suite function as unique key.
        This function handles also on case that the test suite function decorated with pytest.mark.parametrize
        :return: Wrapped Suite function instance
        """
        stack_locals = [frame_info.frame.f_locals for frame_info in inspect.stack()]

        for f_locals in [
            stack_local
            for stack_local in stack_locals
            if "self" in stack_local and isinstance(stack_local["self"], Function)
        ]:
            func = f_locals["self"]

            # if pytest.mark.parametrize exist, get actual function from class while ignoring the add parameters
            if hasattr(func, "own_markers") and len(func.own_markers) > 0:
                mark_function = self._get_mark_function(func.own_markers, func)
                if mark_function:
                    return mark_function

            if JunitTestSuite.is_suite_exist(getattr(func.cls, func.name).__wrapped__):
                return getattr(func.cls, func.name).__wrapped__

        return None

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
        for mark in own_markers:
            if mark.name == "parametrize":
                marks_count = len(own_markers)

                params_regex = "-".join(["(.*?)"] * marks_count)
                args = list(re.compile(r"(.*?)\[{0}]".format(params_regex)).findall(func.name).pop())
                func_name = args.pop(0)

                params = list()
                for i in range(marks_count):
                    params.append((own_markers[i].args[0], args[i]))

                self._parametrize = params
                return getattr(func.cls, func_name).__wrapped__
        return None

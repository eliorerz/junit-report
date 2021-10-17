from types import GeneratorType
from typing import Callable, Union

import decorator

from ._junit_test_case import JunitTestCase, TestCaseCategories
from ._junit_test_suite import JunitTestSuite
from .utils import Utils


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
    _inner_test_case_exception: bool

    def __init__(self) -> None:
        super().__init__()
        self._generator = None
        self._inner_test_case_exception = False

    def __call__(self, function: Callable) -> Callable:
        self._func = function

        def wrapper(_, *args, **kwargs):
            value = self._wrapper(function, *args, **kwargs)
            yield value
            try:
                if self._generator:
                    self._teardown_yield_fixture(self._generator)
            except BaseException as e:
                self._case_data.case.category = TestCaseCategories.FIXTURE_TEARDOWN.value
                self._add_failure(e)
                raise
            finally:
                JunitTestSuite.fixture_cleanup(self._case_data, self.get_suite_key())

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
        except BaseException as e:
            if Utils.is_case_exception_already_raised(e):
                self._inner_test_case_exception = True
            raise

    def _on_wrapper_end(self):
        """
        Fixtures executing before the test suite, due to that issue the suite can't collect the fixture case
        if there is an exception during it's execution. If exception occur, it call JunitTestSuite class method
        collect_all that trigger the suite to collect all cases and export them into xml
        :return: None
        """
        self._case_data.case.category = TestCaseCategories.FIXTURE.value

        super(JunitFixtureTestCase, self)._on_wrapper_end()
        if len(self._case_data.case.failures) > 0 or self._inner_test_case_exception:
            JunitTestSuite.collect_all(True)

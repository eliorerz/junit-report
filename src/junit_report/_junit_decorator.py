import inspect
import re
import time
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Any, Callable, Union, List, Dict

import decorator


class JunitDecorator(ABC):

    _func: Union[Callable, None]
    _start_time: Union[float, None]
    _stack_locals: List[Dict[str, Any]]

    def __init__(self) -> None:
        self._func = None
        self._start_time = None
        self._stack_locals = list()

    def __call__(self, function: Callable) -> Callable:
        """
        :param function: Decorated function
        :return: Wrapped function
        """
        self._func = function
        self._on_call()

        def wrapper(_, *args, **kwargs):
            return self._wrapper(function, *args, **kwargs)

        return decorator.decorator(wrapper, function)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} {self.name}"

    @property
    def name(self):
        return self._func.__name__

    def _wrapper(self, function: Callable, *args, **kwargs):
        value = None

        with suppress(BaseException):
            self._on_wrapper_start(function)
        try:
            value = self._execute_wrapped_function(*args, **kwargs)
        except BaseException as e:
            self._on_exception(e)
        finally:
            with suppress(BaseException):
                self._on_wrapper_end()
        return value

    def _get_class_name(self) -> str:
        """
        Get class name of which the decorated function contained in it.
        If class doesn't exists, it returns the module name
        :return: class or module name
        """
        module = inspect.getmodule(self._func)
        try:
            classname, _ = re.compile(r"(\w+)\.(\w+)\sat\s").findall(str(self._func))[0]
            return classname
        except IndexError:
            return module.__name__

    @abstractmethod
    def _on_wrapper_end(self) -> None:
        """
        Executed after execution finished (successfully or not)
        :return: None
        """

    def _on_call(self) -> None:
        """
        Executed on __call__ start.
        :return: None
        """

    def _execute_wrapped_function(self, *args, **kwargs) -> Any:
        """
        Execute wrapped function and return its value.
        Exceptions in this function will be caught by _on_exception
        :param args: Arguments passed to the function
        :param kwargs: Key arguments passed to the function
        :return: Wrapped function return value
        """
        return self._func(*args, **kwargs)

    def _on_exception(self, e: BaseException) -> None:
        """
        This function executed when exception is raised within the wrapped function
        :param e: Raised BaseException
        :return: None
        """
        raise

    def _on_wrapper_start(self, function) -> None:
        """
        This function executed when wrapper function starts
        :return: None
        """
        self._start_time = time.time()
        self._stack_locals = [frame_info.frame.f_locals for frame_info in inspect.stack()]

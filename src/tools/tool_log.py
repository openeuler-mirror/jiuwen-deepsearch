#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
import logging
import time

from typing import TypeVar, Any, Type

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_logged_tool(base_tool_class: Type[T]) -> Type[T]:
    """
    Factory function that gets a logged version of any tool class.

    Args:
         base_tool_class: The original tool class to enhance with logging

    Returns:
        A new class that inherits both base tool's functionality and logging capabilities
    """
    # get metaclass of the base class
    base_metaclass = type(base_tool_class)

    # create a compatible metaclass that inherits from the base metaclass
    class LoggedToolMeta(base_metaclass):
        pass

    # create the logging mixin with the compatible metaclass
    class ToolLoggingMixin(metaclass=LoggedToolMeta):
        """Mixin class that adds logging capabilities to tools."""

        def _log_start(self, method: str, *args: Any, **kwargs: Any) -> None:
            """Log the start of tool execution with input parameters."""
            tool_name = self._get_tool_name()
            params = self._format_params(args, kwargs)
            logger.info(f"[TOOL START] {tool_name}.{method} | Params: {params}")

        def _log_end(self, method: str, result: Any, duration: float) -> None:
            """Log the successful completion of tool execution with results and duration"""
            tool_name = self._get_tool_name()
            result_summary = self._truncate_result(result)
            logger.info(f"[TOOL END] {tool_name}.{method} | Result: {result_summary} | Duration: {duration: .2f}s")

        def _log_error(self, method: str, error: Exception) -> None:
            """Log exceptions that occur during tool execution."""
            tool_name = self._get_tool_name()
            logger.error(f"[TOOL ERROR] {tool_name}.{method} | Error: {str(error)}", exc_info=True)

        def _get_tool_name(self) -> str:
            """Extract the original tool name by removing logging-related suffixes."""
            return self.__class__.__name__.replace("WithLogging", "")

        def _format_params(self, args: tuple, kwargs: dict) -> str:
            """Format arguments and keyword arguments into a readable string for logging."""
            args_str = [repr(arg) for arg in args]
            kwargs_str = [f"{k}={v!r}" for k, v in kwargs.items()]
            return ", ".join(args_str + kwargs_str)

        def _truncate_result(self, result: Any) -> str:
            """Truncate long results to avoid overly verbose logs."""
            result_str = repr(result)
            return result_str[:100] + "..." if len(result_str) > 100 else result_str

        def _run(self, *args: Any, **kwargs: Any) -> Any:
            """Synchronized tool execution with logging and timing."""
            start_time = time.time()
            self._log_start("_run", *args, **kwargs)
            try:
                result = super()._run(*args, **kwargs)
            except Exception as e:
                self._log_error("_run", e)
                raise
            self._log_end("_run", result, time.time() - start_time)
            return result

        async def _arun(self, *args: Any, **kwargs: Any) -> Any:
            """Asynchronous tool execution with logging and timing."""
            start_time = time.time()
            self._log_start("_arun", *args, **kwargs)
            try:
                result = await super()._arun(*args, **kwargs)
            except Exception as e:
                self._log_error("_arun", e)
                raise
            self._log_end("_arun", result, time.time() - start_time)
            return result

    # create the final enhanced tool class
    class ToolWithLogging(ToolLoggingMixin, base_tool_class):
        pass

    # set a descriptive name for the enhanced class
    ToolWithLogging.__name__ = f"{base_tool_class.__name__}WithLogging"
    return ToolWithLogging


def tool_invoke_log(func):
    """
    A decorator that logs the input parameters and return results of a function,
    with enhanced exception handling capabilities.
    """

    def wrapper(*args, **kwargs):
        # extract function name for logging
        function_name = func.__name__

        # format positional and keyword arguments for logging
        formatted_args = []
        formatted_args.extend([str(arg) for arg in args])
        formatted_args.extend([f"{k}={v}" for k, v in kwargs.items()])
        args_text = ", ".join(formatted_args)

        # log function invocation with parameters
        logger.info(f"[TOOL INVOKE] {function_name} | Args: {args_text}")

        try:
            # execute the original function
            result = func(*args, **kwargs)
        except Exception as e:
            # log exceptions with stack trace
            logger.error(f"[TOOL ERROR] {function_name} | Exception: {repr(e)}", exc_info=True)
            raise

        # log the return value
        logger.info(f"[TOOL INVOKE] {function_name} | Result: {result}")

        return result

    return wrapper

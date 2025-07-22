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
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from typing_extensions import Annotated

python_repl = PythonREPL()


@tool
def python_programmer_tool(
        code: Annotated[str, "python_repl"],
):

    """python programmer tool"""
    if not isinstance(code, str):
        err_msg = f"Input of programmer tool must be a string, but got {type(code)}"
        logging.error(err_msg)
        return f"Executing failed:\n```\n{code}\n```\nError: {err_msg}"

    logging.debug(f"Starting programmer tool: {code}")

    try:
        result = python_repl.run(code)
        if result is None or (isinstance(result, str) and ("ERROR" in result or "Exception" in result)):
            logging.error(result)
            return f"Executing failed:\n```\n{code}\n```\nError: {result}"
        logging.info(f"Finished programmer tool: {code}, result: {result}")
    except BaseException as err:
        err_msg = repr(err)
        logging.error(err_msg)
        return f"Executing failed:\n```\n{code}\n```\nError: {err_msg}"

    out = f"Successfully executed:\n```\n{code}\n```\nStdout: {result}"
    return out

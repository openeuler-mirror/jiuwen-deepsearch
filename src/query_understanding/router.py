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
# ******************************************************************************

import logging
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from src.llm.llm_wrapper import LLMWrapper
from src.manager.search_context import SearchContext
from src.prompts.template import apply_system_prompt

logging = logging.getLogger(__name__)


@tool
def send_to_planner(
        query_title: Annotated[str, "The title of the query to be handed off."],
        language: Annotated[str, "The user's detected language locale."]
):
    """
    This tool didn't return anything: it was just used as a way to signal to the LLM that it needed to be handed off to the planner agent.
    """
    return


def classify_query(context: SearchContext, config: RunnableConfig) -> (bool, str):
    """
        Query routing: Determine whether to enter the deep (re)search process.

        Args:
        context: Current agent context
        config: Current runtime configuration

        Returns:
            bool: whether to enter the deep (re)search process.
            str: language locale.
    """
    logging.info(f"Begin query classification operation.")
    prompts = apply_system_prompt("entry", context, config)
    response = (
        LLMWrapper("basic")
        .bind_tools([send_to_planner])
        .invoke(prompts)
    )
    if len(response.tool_calls) > 0:
        return True, response.tool_calls[0].get("args", {}).get("language")
    else:
        return False, "zh-CN"

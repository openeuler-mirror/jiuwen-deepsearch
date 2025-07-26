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

logger = logging.getLogger(__name__)

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from src.manager.search_context import SearchContext, Step
from src.tools.web_search import get_web_search_tool
from src.tools.crawl import get_crawl_tool
from src.llm.llm_wrapper import LLMWrapper
from src.prompts.template import apply_system_prompt


class Collector:
    def __init__(self, context: SearchContext, config: RunnableConfig):
        self.context = context
        self.config = config
        self.recursion_limit = config.get("recursion_limit", 10)
        self.max_search_results = config.get("configurable", {}).get("max_search_results", 5)
        self.max_crawl_length = config.get("configurable", {}).get("max_crawl_length", 2000)
        self.tools = [get_web_search_tool(self.max_search_results), get_crawl_tool(self.max_crawl_length)]
        self.agent = self.collector_agent_build()

    def collector_agent_build(self):
        llm_model = LLMWrapper("basic")
        return create_react_agent(model=llm_model, tools=self.tools,
                                  prompt=self._agent_dynamic_prompt_build)

    def _agent_dynamic_prompt_build(self, context: SearchContext):
        dynamic_prompt = apply_system_prompt("collector", context, self.config)
        return dynamic_prompt

    def _agent_input_build(self, task: Step):
        agent_input = {"messages": [HumanMessage(
            content=f"Now deal with the task:\n[Task Title]: {task.title}\n[Task Description]: {task.description}\n\n")]}
        return agent_input

    async def get_info(self, task: Step):
        agent_input = self._agent_input_build(task)
        result = self.agent.invoke(input=agent_input, config={"recursion_limit": self.recursion_limit})
        messages = result.get("messages", [])
        if not messages:
            clean_result = "Error: No messages found in the agent result."
            logger.error(clean_result)
        else:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                clean_result = last_message.content
            else:
                clean_result = f"Error: Unexpected message type: {type(last_message)}. Expected AIMessage."
                logger.error(clean_result)
        task.step_result = clean_result

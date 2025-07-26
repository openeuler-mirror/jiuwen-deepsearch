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

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from src.llm import LLMWrapper
from src.manager.search_context import Step, SearchContext
from src.prompts import apply_system_prompt
from src.tools.python_programmer import python_programmer_tool


class Programmer:
    def __init__(self, config: RunnableConfig):
        self._config = config
        self._agent = self._create_programmer_agent()

    def _create_programmer_agent(self):
        llm = LLMWrapper("basic")
        return create_react_agent(model=llm,
                                  tools=[python_programmer_tool],
                                  prompt=self._get_agent_prompt)

    def _get_agent_prompt(self, context: SearchContext):
        return apply_system_prompt(
            prompt_template_file="programmer",
            context=context,
            config=self._config)

    def _build_agent_input(self, task: Step):
        class AgentInput(BaseModel):
            messages: list

        return AgentInput(messages=[
            HumanMessage(
                content=f"# Current Task\n\n## Title\n\n{task.title}\n\n## Description\n\n{task.description}\n\n"
            )])

    def run(self, task: Step) -> str:
        agent_input = self._build_agent_input(task)
        try:
            logging.debug(f"reporter prompts: {agent_input}")
            agent_output = self._agent.invoke(input=agent_input)
        except Exception as e:
            error_message = str(e)
            logging.error(f"Generate report error: {error_message}")
            return error_message

        messages = agent_output.get("messages", [])
        if not messages:
            result = "Error: No messages found in the programmer result."
            logging.error(result)
        else:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                result = last_message.content
            else:
                result = f"Error: Unexpected message type: {type(last_message)}. Expected AIMessage."
                logging.error(result)
        logging.debug(f"programmer output: {result}")
        return result

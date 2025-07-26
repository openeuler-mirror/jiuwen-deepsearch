# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import json
import logging
from typing import List, cast

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import BaseMessage, AIMessageChunk

from src.config.configuration import Configuration
from .nodes import (
    entry_node,
    plan_reasoning_node,
    research_manager_node,
    info_collector_node,
    programmer_node,
    reporter_node,
    evaluator_node,
)
from .search_context import SearchContext

logging.basicConfig(
    filename=Configuration.get_conf("service", "log_file", expected_type=str),
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class Workflow:
    def __init__(self):
        self.graph = CompiledStateGraph

    def build_graph(self):
        builder = StateGraph(SearchContext)
        builder.add_edge(START, "entry")
        builder.add_node("entry", entry_node)
        builder.add_node("plan_reasoning", plan_reasoning_node)
        builder.add_node("research_manager", research_manager_node)
        builder.add_node("info_collector", info_collector_node)
        builder.add_node("programmer", programmer_node)
        builder.add_node("reporter", reporter_node)
        builder.add_node("evaluator", evaluator_node)
        builder.add_edge("research_manager", END)
        self.graph = builder.compile()

    async def run(self,
                  messages: str,
                  session_id: str,
                  local_datasets: List[str],
                  report_style: str = "",
                  report_format: str = "", ):
        input = {
            "messages": messages,
            "plan_executed_num": 0,
            "report": "",
            "current_plan": None,
            "collected_infos": [],
        }
        config = {
            "recursion_limit": Configuration.get_conf("workflow", "recursion_limit", expected_type=int),
            "configurable": {
                "session_id": session_id,
                "local_datasets": local_datasets,
                "max_plan_executed_num": Configuration.get_conf("workflow", "max_plan_executed_num", expected_type=int),
                "max_report_generated_num": Configuration.get_conf("workflow", "max_report_generated_num",
                                                                   expected_type=int),
                "report_style": report_style,
                "report_format": report_format,
                "max_step_num": Configuration.get_conf("planner", "max_task_num", expected_type=int),
                "report_output_path": Configuration.get_conf("report", "output_path", expected_type=str),
                "max_search_results": Configuration.get_conf("info_collector", "max_search_results", expected_type=int),
                "max_crawl_length": Configuration.get_conf("info_collector", "max_crawl_length", expected_type=int),
            }
        }

        async for agent, _, message_update in self.graph.astream(
                input=input, config=config, stream_mode=["messages", "updates"], subgraphs=True,
        ):
            logger.debug(f"Received message: {message_update}, agent: {agent}")
            if isinstance(message_update, dict):
                continue
            message, metadata = cast(tuple[BaseMessage, any], message_update)
            if not isinstance(message, AIMessageChunk):
                continue

            agent_name = message.name
            if not agent_name:
                if len(agent) > 0:
                    agent_name = agent[0].split(":")[0]
                elif "langgraph_node" in metadata:
                    agent_name = metadata["langgraph_node"]
            output_message: dict[str, any] = {
                "session_id": session_id,
                "agent": agent_name,
                "id": message.id,
                "role": "assistant",
                "content": message.content,
                "message_type": message.__class__.__name__
            }
            yield json.dumps(output_message, ensure_ascii=False)

# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import asyncio
import logging

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.llm.llm_wrapper import LLMWrapper
from src.manager.search_context import SearchContext, TaskType
from src.prompts import apply_system_prompt
from src.query_understanding.planner import Planner
from src.query_understanding.router import classify_query
from src.report import Reporter, ReportLang, ReportFormat, ReportStyle
from src.retrieval.collector import Collector

logger = logging.getLogger(__name__)


def entry_node(context: SearchContext, config: RunnableConfig) -> Command:
    logger.info(f"start entry node: \n{context}")
    go_deepsearch, lang = classify_query(context, config)
    if go_deepsearch:
        return Command(
            update={"language": lang},
            goto="plan_reasoning",
        )
    else:
        chat_prompt = apply_system_prompt("chat", context, config)
        response = (
            LLMWrapper("basic")
            .invoke(chat_prompt)
        )
        logger.info(f"Chat response: {response.content}")
        return Command(
            update={
                "messages": [AIMessage(content=response.content, name="entry")],
            },
            goto='__end__',
        )


def plan_reasoning_node(context: SearchContext, config: RunnableConfig) -> Command:
    logger.info(f"start plan reasoning node: \n{context}")
    planner = Planner()
    plan_info = planner.generate_plan(context, config)
    return Command(
        update={**plan_info},
        goto="research_manager",
    )


def research_manager_node(context: SearchContext, config: RunnableConfig) -> Command:
    logger.info(f"start research manager node: \n{context}")

    current_plan = context.get("current_plan")
    if current_plan is None:
        logger.error(f"current plan is none")
        return Command(goto="__end__")

    report = context.get("report", "")
    if current_plan.is_research_completed:
        if report == "":
            logger.info(f"current plan is research ending, goto reporter")
            return Command(goto="reporter")
    else:
        # Traverse the tasks in the plan, if any task has not been executed, call the relevant module to execute it.
        is_all_tasks_finish: bool = True
        for task in current_plan.tasks:
            if not task.task_result:
                is_all_tasks_finish = False
                break
        if not is_all_tasks_finish:
            if task.task_type == TaskType.INFO_COLLECTING:
                return Command(goto="info_collector")
            if task.task_type == TaskType.PROGRAMMING:
                return Command(goto="programmer")
            logger.error(f"unknown task type: {task.task_type}")
            return Command(goto="__end__")

    # All task have been executed, or the collected information is enough
    if report == "":
        # when report is empty, determine whether to continue plan iteration or to generate the report.
        plan_executed_num = int(context.get("plan_executed_num", 0))
        plan_executed_num += 1
        max_plan_executed_num = config.get("configurable", {}).get("max_plan_executed_num", 0)
        if plan_executed_num >= max_plan_executed_num:
            logger.info(f"reached max plan executed num: {max_plan_executed_num}, go to reporter")
            return Command(update={"plan_executed_num", plan_executed_num}, goto="reporter")
        logger.info(f"Has executed {plan_executed_num} plans, go to next plan reasoning")
        return Command(update={"plan_executed_num", plan_executed_num}, goto="plan_reasoning")

    # The report has been generated, and if the report_evaluation is empty, go to evaluator,
    report_evaluation = context.get("report_evaluation", "")
    if report_evaluation == "":
        return Command(goto="evaluator")

    # If the report_evaluation is "pass", terminate, otherwise, re-execute the plan
    if report_evaluation == "pass":
        logger.info(f"report evaluation passed")
        return Command(goto="__end__")

    logger.info(f"report evaluation not pass")
    report_generated_num = context.get("report_generated_num", 0)
    max_report_generated_num = config.get("configurable", {}).get("report_generated_num", 0)
    if report_generated_num >= max_report_generated_num:
        logger.info(f"reached max generation num: {max_report_generated_num}")
        return Command(goto="__end__")
    return Command(goto="plan_reasoning")

async def info_collector_node(context: SearchContext, config: RunnableConfig) -> Command:
    logger.info(f"start info collector node: \n{context}")
    current_plan = context.get("current_plan")
    if current_plan is None:
        return Command(goto="research_manager")

    collected_infos = context.get("collected_infos", [])
    collector = Collector(context, config)
    messages = []
    async_collecting = []
    collect_tasks = []
    for task in current_plan.tasks:
        if task.task_type == TaskType.INFO_COLLECTING and not task.task_result:
            async_collecting.append(collector.get_info(task))
            collect_tasks.append(task)
    await asyncio.gather(*async_collecting)

    for task in collect_tasks:
        collected_infos.append(task.task_result)
        messages.append(HumanMessage(
            content=task.task_result,
            name="info_collector",
        ))
        logger.info(f"The result of {task.title} is: {task.task_result}")

    return Command(
        update={
            "messages": messages,
        },
        goto="research_manager",
    )


def programmer_node(context: SearchContext, config: RunnableConfig) -> Command:
    logger.info(f"start programmer node: \n{context}")
    current_plan = context.get("current_plan")
    if current_plan is None:
        return Command(goto="research_manager")

    collected_infos = context.get("collected_infos", [])
    messages = []
    for task in current_plan.tasks:
        if task.task_type == TaskType.PROGRAMMING and not task.task_result:
            task.task_result = "programming result"
            collected_infos.append(task.task_result)
            messages.append(HumanMessage(
                content=task.task_result,
                name="programmer"
            ))
    return Command(
        update={
            "messages": messages,
        },
        goto="research_manager",
    )


def reporter_node(context: SearchContext, config: RunnableConfig) -> Command:
    logger.info(f"start reporter node: \n{context}")
    configurable = config.get("configurable", {})
    if not configurable.get("report_style"):
        configurable["report_style"] = ReportStyle.SCHOLARLY.value
    if not configurable.get("report_format"):
        configurable["report_format"] = ReportFormat.MARKDOWN
    if not configurable.get("language"):
        configurable["language"] = ReportLang.ZN.value
    config["configurable"] = configurable

    reporter = Reporter()
    success, report_str = reporter.generate_report(context, config)
    if not success:
        return Command(
            update={"report": "error: " + report_str},
            goto="__end__"
        )

    context["report_generated_num"] = context.get("report_generated_num", 0) + 1
    return Command(
        update={
            "report": context.get("report", ""),
            "report_generated_num": context["report_generated_num"],
            "messages": [AIMessage(content=context.get("report", ""), name="reporter")],
        },
        goto="research_manager",
    )

def evaluator_node(context: SearchContext, config: RunnableConfig) -> Command:
    logger.info(f"start evaluator node: \n{context}")
    return Command(
        update={"report_evaluation": "pass"},
        goto="research_manager",
    )

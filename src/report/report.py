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

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from src.llm.llm_wrapper import LLMWrapper
from src.manager.search_context import SearchContext
from src.prompts import apply_system_prompt
from src.report import ReportFormat

logger = logging.getLogger(__name__)


class Reporter:
    def __init__(self):
        self._llm = LLMWrapper("basic")

    def generate_report(self, context: SearchContext, config: RunnableConfig) -> tuple[bool, str]:
        """
        generate report according to report_style/report_format/report_lang.

        Args:
            context: the context which go through the whole search.
            config: can fetch the report style/format/language.

        Returns:
            tuple[bool, str]: The response.
                bool: Is request success.
                str: Success: Report path (maybe empty), Error: Error messages.
        """
        """Reporter node that write a final report."""
        configurable = config.get("configurable", {})
        report_format = configurable.get("report_format", ReportFormat.MARKDOWN)
        if not isinstance(report_format, ReportFormat):
            return False, f"Error: Report format is not instance of ReportFormat {report_format}"

        try:
            llm_input = apply_system_prompt(f"report_{report_format.get_name()}", context, config)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Generate report apply prompt error: {error_message}")
            return False, error_message

        current_plan = context.get("current_plan")
        if current_plan and current_plan.title and current_plan.thought:
            llm_input.append(HumanMessage(
                f"# Key Search Points\n\n## Title\n\n{current_plan.title}\n\n## Thought\n\n{current_plan.thought}"
            ))

        for info in context.get("collected_infos", []):
            llm_input.append(HumanMessage(
                f"The following is the information collected during the task processing:\n\n{info}"
            ))

        try:
            logger.debug(f"reporter prompts: {llm_input}")
            llm_output = self._llm.invoke(llm_input)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Generate report error: {error_message}")
            return False, error_message

        report_content = llm_output.content
        context["report"] = report_content
        logger.info(f"reporter content: {report_content}")

        return report_format.get_processor().write_file(context, config)

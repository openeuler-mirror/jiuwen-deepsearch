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
import os
import re
from datetime import datetime

import shortuuid
from langchain_core.runnables import RunnableConfig

from src.manager.search_context import SearchContext

logger = logging.getLogger(__name__)


class DefaultReportFormatProcessor:
    @staticmethod
    def generate_unique_filename() -> str:
        return f'report_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}_{shortuuid.uuid(pad_length=16)}'

    @staticmethod
    def write_file(context: SearchContext, config: RunnableConfig) -> tuple[bool, str]:
        return False, "Default report format processor"


class ReportMarkdown(DefaultReportFormatProcessor):
    @staticmethod
    def __remove_think_tag(report_msg: str) -> str:
        return re.sub(r'<think>.*?</think>', '', report_msg, flags=re.DOTALL)

    @staticmethod
    def __remove_useless_lines(report_msg: str) -> str:
        lines = report_msg.splitlines()
        while lines and not lines[0].strip():  # 删除头部空行
            lines.pop(0)
        while lines and not lines[-1].strip():  # 删除尾部空行
            lines.pop()

        if lines and lines[0].strip().startswith('```markdown'):  # 检查首行是否以 ```markdown 开头
            lines.pop(0)  # 删除 ```markdown 标记行
            if lines[-1].startswith('```'):  # 检查尾行是否以 ``` 开头
                lines.pop()  # 删除尾部 ``` 标记行

        return '\n'.join(lines)  # 将处理后的行列表重新组合为字符串

    @staticmethod
    def write_file(context: SearchContext, config: RunnableConfig):
        configurable = config.get("configurable", {})
        report_output_dir = configurable.get("report_output_path", "")
        if not report_output_dir:
            return True, ""

        report_content = context["report"]
        if not report_content:
            err_msg = "Error: Empty report content"
            logger.error(err_msg)
            return False, err_msg

        report_output_path = f"{report_output_dir}/{ReportMarkdown.generate_unique_filename()}.md"
        logger.debug(f"report output path: {report_output_path}")

        file_content = ReportMarkdown.__remove_think_tag(report_content)
        file_content = ReportMarkdown.__remove_useless_lines(file_content)
        with open(report_output_path, 'w', encoding='utf-8') as file:
            file.write(file_content)
            file.flush()
            os.fsync(file.fileno())

        return True, report_output_path
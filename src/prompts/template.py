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
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.runnables import RunnableConfig

from src.manager.search_context import SearchContext

logger = logging.getLogger(__name__)

jinja_env = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=select_autoescape(),
    loader=FileSystemLoader(os.path.dirname(__file__))
)


def apply_system_prompt(prompt_template_file: str, context: SearchContext, config: RunnableConfig) -> list:
    logger.debug(f'Apply system prompt with configuration: {config.get("configurable", {})}')

    # 将变量转换为dict用于渲染模板
    context_vars = {
        "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        **context,  # 添加context中的变量
        **(config.get("configurable", {}))  # 添加config中的变量
    }

    try:
        prompt_template = jinja_env.get_template(f"{prompt_template_file}.md")
        system_prompt = prompt_template.render(**context_vars)
        return [{"role": "system", "content": system_prompt}, *context["messages"]]
    except FileNotFoundError as e:
        error_msg = f"Template file not found: {prompt_template_file}.md"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        raise ValueError(f"Applying system prompt template with {prompt_template_file}.md failed: {e}")

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

import os
from typing import Any, Type

from dotenv import load_dotenv

load_dotenv()


class LLMWrapper:
    _registry: dict[str, Type] = {}

    def __new__(cls, llm_type: str, **kwargs) -> Any:
        llm_prefix = "LLM_" + llm_type.upper() + "_"
        api_type = os.getenv(llm_prefix + "API_TYPE", "openai")
        llm_conf = {
            "base_url": os.getenv(llm_prefix + "BASE_URL"),
            "model": os.getenv(llm_prefix + "MODEL"),
            "api_key": os.getenv(llm_prefix + "API_KEY")
        }
        creator_cls = cls._registry.get(api_type)
        if not creator_cls:
            raise KeyError(f"No LLM client registered under type '{api_type}'")

        creator = creator_cls(llm_conf)
        return creator.create()

    @classmethod
    def register(cls, api_type: str, llm_creator_cls: Type):
        cls._registry[api_type] = llm_creator_cls

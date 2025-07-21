# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from enum import Enum
from typing import List, Optional

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    INFO_COLLECTING = "info_collecting"
    PROGRAMMING = "programming"


class Task(BaseModel):
    type: TaskType = Field(..., description="任务类型（枚举值）")
    title: str = Field(..., description="任务标题，简要描述任务内容")
    description: str = Field(..., description="任务详细说明，明确指定需要收集的数据或执行的编程任务")
    task_result: Optional[str] = Field(default=None, description="任务执行结果，完成后由系统进行填充")


class Plan(BaseModel):
    language: str = Field(default="zh-CN", description="用户语言：zh-CN、en-US等")
    title: str = Field(..., description="计划标题，概括整体目标")
    thought: str = Field(..., description="计划背后的思考过程，解释任务顺序和选择的理由")
    is_research_completed: bool = Field(..., description="是否已完成信息收集工作")
    tasks: List[Task] = Field(default_factory=list, description="info_collecting | programming 类型的任务")


class SearchContext(MessagesState):
    language: str = "zh-CN"
    plan_executed_num: int = 0
    current_plan: Plan | str = None
    collected_infos: list[str] = []
    report: str = ""
    report_generated_num: int = 0
    report_evaluation: str = ""

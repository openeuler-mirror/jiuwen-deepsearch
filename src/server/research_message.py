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
from pydantic import BaseModel, Field
from typing import Optional, List


class ResearchRequest(BaseModel):
    messages: str = Field(None, description="user message")
    local_datasets: Optional[List[str]] = Field(None, description="local knowledge datasets")
    session_id: Optional[str] = Field(None, description="session id")
    report_style: Optional[str] = Field(None, description="report style")
    report_format: Optional[str] = Field(None, description="report format")


class ResearchResponse(BaseModel):
    content: str = Field(None, description="research content, markdown format")

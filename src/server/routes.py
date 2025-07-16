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
from fastapi import APIRouter
from .research_message import ResearchRequest, ResearchResponse

router = APIRouter(
    prefix="/api",
    tags=["api"],
)


@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    logging.info(f"research request {request.model_dump_json()}")
    return ResearchResponse(content=request.model_dump_json())

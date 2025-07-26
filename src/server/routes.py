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
from fastapi.responses import StreamingResponse
from .research_message import ResearchRequest, ResearchResponse
from src.manager.workflow import Workflow

router = APIRouter(
    prefix="/api",
    tags=["api"],
)

workflow = Workflow()
workflow.build_graph()


@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    logging.info(f"research request {request.model_dump_json()}")
    return StreamingResponse(
        workflow.run(
            messages=request.messages,
            session_id=request.session_id,
            local_datasets=request.local_datasets,
            report_style=request.report_style,
            report_format=request.report_format,
        ),
        media_type="text/event-stream",
    )

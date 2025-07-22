# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import argparse
import asyncio
import json

from src.manager.workflow import Workflow

async def run_workflow(query: str):
    workflow = Workflow()
    workflow.build_graph()
    async for msg in workflow.run(query, "default_session_id", []):
        msgObj = json.loads(msg)
        if "message_type" in msgObj and msgObj["message_type"] == "AIMessageChunk" and "content" in msgObj:
            print(msgObj["content"], end="")
        else:
            print(f"\n{msg}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run deepsearch project")
    parser.add_argument("query", nargs="*", help="The query to process")
    args = parser.parse_args()

    if not args.query:
        parser.print_help()
    else:
        asyncio.run(run_workflow(args.query))

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
import uvicorn


def server_run(host: str, port: int, reload: bool, log_level: str):
    logging.info(f"Starting jiuwen deep search server on {host}:{port}")
    try:
        uvicorn.run(
            "src.server.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
        )
    except SystemExit as e:
        logging.error(f"Server start fail and exited with error: {e.code}")
        return

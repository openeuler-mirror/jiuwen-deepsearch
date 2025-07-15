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
import argparse
import logging
from importlib import reload

from src.server import server_run


def parse_args():
    parser = argparse.ArgumentParser(description="jiuwen deep search args")
    parser.add_argument("-r", "--reload", action="store_true", help="enable auto reload")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="host of server")
    parser.add_argument("-p", "--port", type=int, default=8888, help="port of server")
    parser.add_argument("-l", "--log_level", type=str, default="info",
                        choices=["debug", "info", "warning", "error", "critical"], help="enable debug mode")
    return parser.parse_args()


def setup_logging(log_level: str):
    level = getattr(logging, log_level.upper(), logging.INFO)
    # logging config
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    )


if __name__ == "__main__":
    # parse command line arguments
    args = parse_args()
    setup_logging(args.log_level)

    # determine reload setting
    reload = False
    if args.reload:
        reload = True

    server_run(
        host=args.host,
        port=args.port,
        reload=reload,
        log_level=args.log_level,
    )

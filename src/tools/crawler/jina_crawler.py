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
import os
import requests
import logging

from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class JinaCrawler(BaseModel):
    max_length:Optional[int] = Field(None, description="max length of crawl information")

    def crawl(self, url: str):
        headers = {}
        jina_api_key = os.getenv("JINA_API_KEY", "")
        if jina_api_key:
            headers["Authorization"] = f"Bearer {jina_api_key}"
        else:
            logger.warning(
                "JINA_API_KEY is not provided. See https://jina.ai/reader for more information."
            )
        # request jina crawl service
        jina_url = "https://r.jina.ai/" + url
        try:
            response = requests.get(jina_url, headers=headers)
            context_result = response.text
            if isinstance(self.max_length, int):
                context_result = context_result[:self.max_length]
            logger.info("Crawl Tool: Jina request success.")
            return {
                "text_content": context_result.strip(),
            }
        except BaseException as e:
            error_msg = f"Crawl Tool: Jina request failed. Error: {repr(e)}"
            logger.error(error_msg)
            return {
                "error_msg": error_msg,
            }


if __name__ == "__main__":
    url = ""
    max_length = 1000
    os.environ["JINA_API_KEY"] = ""
    crawler = JinaCrawler(max_length=max_length)
    result = crawler.crawl(url)

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
import requests

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)


class BasicWebCrawler(BaseModel):
    max_length: Optional[int] = Field(None, description="max length of crawl information")
    def crawl(self, url: str) -> str:
        response = requests.get(url)
        if response.status_code != 200:
            soup = BeautifulSoup(response.text, "lxml")
            context_result = ""
            # title
            title = soup.title.string.strip() if soup.title else ""
            if title:
                context_result += title + "\n"
            # paragraph
            paragraphs = soup.find_all("p")
            if paragraphs:
                for paragraph in paragraphs:
                    context_result += paragraph.get_text(strip=True) + "\n"
            if isinstance(self.max_length, int):
                context_result = context_result[:self.max_length]
            logger.info("Crawl Tool: Html request success.")
            return context_result.strip()
        else:
            logger.error("Crawl Tool: Html request failed.")


if __name__ == "__main__":
    url = ""
    max_length = 1000
    crawler = BasicWebCrawler(max_length=max_length)
    result = crawler.crawl(url)

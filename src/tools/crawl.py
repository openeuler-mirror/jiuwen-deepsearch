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

from langchain_cores.tools import tool

from .crawler.html_parser_crawler import BasicWebCrawler
from .crawler.jina_crawler import JinaCrawler
from src.config.tools import CrawlTool, SELECTED_CRAWL_TOOL

logger = logging.getLogger(__name__)


def make_crawl_tool(crawler_instance):
    """
    Factory function: Generates a Langchain Tool based on crawler instance.
    """

    @tool("web_crawler")
    def crawl_tool(url: str) -> str:
        """
        Use crawl instance to get web information.

        Args:
            url: url to crawl

        Returns:
            crawl tool
        """
        return crawler_instance.crawl(url)

    return crawl_tool


def get_html_parser_crawl_tool(max_length=None):
    crawler = BasicWebCrawler(max_length=max_length)
    return make_crawl_tool(crawler)


def get_jina_crawl_tool(max_length=None):
    crawler = JinaCrawler(max_length=max_length)
    return make_crawl_tool(crawler)


crawl_tool_mapping = {
    CrawlTool.HTML_PARSER.value: get_html_parser_crawl_tool,
    CrawlTool.JINA.value: get_jina_crawl_tool,
}


def get_crawl_tool(max_length=None):
    """
    Use crawl tool to get web information.

    Args:
        max_length: max data length of crawl information

    Returns:
        crawl tool
    """
    if SELETED_CRAWL_TOOL in crawl_tool_mapping:
        try:
            return crawl_tool_mapping[SELETED_CRAWL_TOOL](max_length)
        except BaseException as e:
            error_info = {"error_type": type(e).__name__, "error_msg": str(e)}
            logger.error("Crawl failed", extra=error_info)
            return error_info
    else:
        raise ValueError(f"Unsupported crawl tool: {SELETED_CRAWL_TOOL}")

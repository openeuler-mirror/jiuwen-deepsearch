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
import enum

from dotenv import load_dotenv

load_dotenv()


class SearchEngine(enum.Enum):
    TAVILY = "tavily"
    BING = "bing"
    GOOGLE = "google"
    DUCKDUCKGO = "duckduckgo"
    ARXIV = "arxiv"
    BRAVE_SEARCH = "brave_search"
    PUBMED = "pubmed"
    JINA_SEARCH = "jina_search"


# web search tool configuration
SELECTED_SEARCH_ENGINE = os.getenv("SEARCH_ENGINE", SearchEngine.TAVILY.value)


class CrawlTool(enum.Enum):
    HTML_PARSER = "html_parser"
    JINA = "jina"


# crawl tool configuration
SELECTED_CRAWL_TOOL = os.getenv("CRAWL_TOOL", CrawlTool.HTML_PARSER.value)


class LocalSearch(enum.Enum):
    RAG_FLOW = "rag_flow"
    GRAPH_RAG = "graph_rag"


# local search tool configuration
SELECTED_LOCAL_SEARCH = os.getenv("LOCAL_SEARCH_TOOL", LocalSearch.RAG_FLOW.value)

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
import logging

from langchain_community.tools import (
    TavilySearchResults,
    BingSearchResults,
    GoogleSearchResults,
    DuckDuckGoSearchResults,
    BraveSearch,
    PubmedQueryRun,
    JinaSearch)
from langchain_community.tools.arxiv import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper, BraveSearchWrapper, PubMedAPIWrapper
from langchain_community.utilities.jina_search import JinaSearchAPIWrapper

from src.config.tools import SearchEngine, SELECTED_SEARCH_ENGINE
from src.tools.tool_log import get_logged_tool, tool_invoke_log


logger = logging.getLogger(__name__)


@tool_invoke_log
def get_tavily_search_tool(max_results: int):
    LoggedTavilySearchResults = get_logged_tool(TavilySearchResults)
    return LoggedTavilySearchResults(
        name='tavily_web_search',
        max_results=max_results,
    )


@tool_invoke_log
def get_bing_search_tool(max_results: int):
    LoggedBingSearchResults = get_logged_tool(BingSearchResults)
    return LoggedBingSearchResults(
        name='bing_web_search',
        num_results=max_results,
    )


@tool_invoke_log
def get_google_search_tool(max_results: int):
    LoggedGoogleSearchResults = get_logged_tool(GoogleSearchResults)
    return LoggedGoogleSearchResults(
        name='google_web_search',
        num_results=max_results,
    )


@tool_invoke_log
def get_duckduckgo_search_tool(max_results: int):
    LoggedDuckDuckGoSearchResults = get_logged_tool(DuckDuckGoSearchResults)
    return LoggedDuckDuckGoSearchResults(
        name='duckduckgo_web_search',
        num_results=max_results,
    )


@tool_invoke_log
def get_arxiv_search_tool(max_results: int):
    LoggedArxivQueryRun = get_logged_tool(ArxivQueryRun)
    return LoggedArxivQueryRun(
        name='arxiv_web_search',
        api_wrapper=ArxivAPIWrapper(
            top_k_results=max_results,
            load_max_docs=max_results,
            load_all_available_meta=True,
        ),
    )


@tool_invoke_log
def get_brave_search_tool(max_results: int):
    LoggedBraveSearch = get_logged_tool(BraveSearch)
    return LoggedBraveSearch(
        name='brave_web_search',
        search_wrapper=BraveSearchWrapper(
            api_key=os.getenv("BRAVE_SEARCH_API_KEY", ""),
            search_kwargs={"count": max_results},
        ),
    )


@tool_invoke_log
def get_pubmed_search_tool(max_results: int):
    LoggedPubmedQueryRun = get_logged_tool(PubmedQueryRun)
    return LoggedPubmedQueryRun(
        name='pubmed_web_search',
        api_wrapper=PubMedAPIWrapper(
            api_key=os.getenv("PUBMED_SEARCH_API_KEY", ""),
            top_k_results=max_results,
        ),
    )


@tool_invoke_log
def get_jina_search_tool(_):
    LoggedJinaSearch = get_logged_tool(JinaSearch)
    return LoggedJinaSearch(
        name='jina_web_search',
        search_wrapper=JinaSearchAPIWrapper(
            api_key=os.getenv("JINA_API_KEY", ""),
        ),
    )


search_engine_mapping = {
    SearchEngine.TAVILY.value: get_tavily_search_tool,
    SearchEngine.BING.value: get_bing_search_tool,
    SearchEngine.GOOGLE.value: get_google_search_tool,
    SearchEngine.DUCKDUCKGO.value: get_duckduckgo_search_tool,
    SearchEngine.ARXIV.value: get_arxiv_search_tool,
    SearchEngine.BRAVE_SEARCH.value: get_brave_search_tool,
    SearchEngine.PUBMED.value: get_pubmed_search_tool,
    SearchEngine.JINA_SEARCH.value: get_jina_search_tool,
}


# get the selected web search tool
def get_web_search_tool(max_results: int):
    """
    Use search engine to get web information.

    Args:
         max_results: max retrieve results of search engine

    Returns:
        search engine tool
    """
    if SELECTED_SEARCH_ENGINE in search_engine_mapping:
        return search_engine_mapping[SELECTED_SEARCH_ENGINE](max_results)
    else:
        raise ValueError(f"Unsupported search engine: {SELECTED_SEARCH_ENGINE}")


if __name__ == '__main__':
    SELECTED_SEARCH_ENGINE = SearchEngine.ARXIV.value

    results = get_web_search_tool(
        max_results=3
    )

    test = results.invoke("Alzheimer Disease")

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

from src.config.tools import LocalSearch, SELECTED_LOCAL_SEARCH
from src.retrieval.base_retriever import BaseRetriever
from src.retrieval.retrieval_tool import RetrieverTool

logger = logging.getLogger(__name__)


def get_rag_flow_tool() -> BaseRetriever:
    pass

def get_graph_rag_tool() -> BaseRetriever:
    pass

local_search_mapping = {
    LocalSearch.RAG_FLOW.value: get_rag_flow_tool,
    LocalSearch.GRAPH_RAG.value: get_graph_rag_tool,
}


# get the selected local search tool
def get_local_search_tool(dataset_name=None, dataset_id=None) -> RetrieverTool | None:
    """
    Use local search to get information.

    Args:
         dataset_name: Optional search name to filter datasets by name/description
         dataset_id: Optional dataset id to filter datasets by dataset id

    Returns:
        local search tool
    """
    if SELECTED_LOCAL_SEARCH in local_search_mapping:
        retriever = local_search_mapping[SELECTED_LOCAL_SEARCH]()
    else:
        raise ValueError(f"Unsupported local search tool: {SELECTED_LOCAL_SEARCH}")

    datasets = retriever.list_datasets(name=dataset_name, dataset_id=dataset_id)

    if not retriever or not datasets:
        return None

    return RetrieverTool(retriever=retriever, datasets=datasets)

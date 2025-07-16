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

from typing import Optional, Type
from langchain_core.tools import BaseTool
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field

from src.retrieval.base_retriever import BaseRetriever, Dataset, RetrievalResult

logger = logging.getLogger(__name__)


class RetrieverInput(BaseModel):
    query: str = Field(description="search query to look up")


class RetrieverTool(BaseTool):
    name: str = "local_search_tool"
    description: str = (
        "Retrieving information from local knowledge base files with 'rag://' URI prefix."
    )
    args_schema: Type[BaseModel] = RetrieverInput

    retriever: BaseRetriever = Field(default_factory=BaseRetriever)
    datasets: list[Dataset] = Field(default_factory=list, description="list of datasets to search")

    def _run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> RetrievalResult:
        """
        Synchronously retrieves relevant documents from local datasets.

        Args:
            query: Search query string
            run_manager: Optional callback manager for the tool runs

        Returns:
            Retrieved data
        """
        try:
            logger.info(
                f"Executing lcoal retrieval with query: {query}",
                extra={"dataset_count": len(self.datasets), "datasets": self.datasets},
            )

            # perform document retrieval
            retrieved_results = self.retriever.search_relevant_documents(
                question=query,
                datasets=self.datasets
            )
            if not retrieved_results:
                logger.warning(f"No relevant documents found for query: {query}")

            if run_manager:
                run_manager.on_tool_end(
                    output=str(retrieved_results)
                )

            logger.info(f"Successful retrieved documents for query: {query}")
            return retrieved_results
        except Exception as e:
            if run_manager:
                run_manager.on_tool_error(e)
            logger.error(f"Error during local retrieval: {str(e)}", exc_info=True)
            raise RuntimeError(f"Retrieval failed: {str(e)}")

    async def _arun(
            self,
            query: str,
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> RetrievalResult:
        return self._run(query, run_manager.get_sync())

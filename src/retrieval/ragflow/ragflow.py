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
import os
import requests

from abc import ABC
from typing import Optional, Tuple, Dict
from urllib.parse import urlparse
from pydantic import ValidationError

from src.retrieval.base_retriever import TextChunk, Document, Dataset, BaseRetriever, RetrievalResult

logger = logging.getLogger(__name__)


class RAGFlowRetriever(BaseRetriever, ABC):
    """
    RAGFlowRetriever is a document retriever that uses RAGFlow API to fetch relevant documents.
    """

    def __init__(
            self,
            api_url: Optional[str] = None,
            api_key: Optional[str] = None,
            page_size: int = 10
    ):
        """
        Initialize the RAGFlow Retriever with API credentials.

        Args:
            api_url: RAGFlow API base URL (defaults to RAGFLOW_API_URL env var)
            api_key: RAGFlow API key (defaults to RAGFLOW_API_KEY env var)
            page_size: Number of documents to retrieve per page
        """
        self.api_url = api_url or os.getenv("RAGFLOW_API_URL")
        self.api_key = api_key or os.getenv("RAGFLOW_API_KEY")
        self.page_size = os.getenv("RAGFLOW_PAGE_SIZE")

        if not self.api_url:
            raise ValueError("RAGFLOW_API_URL enviornment variable is not provided")
        if not self.api_key:
            raise ValueError("RAGFLOW_API_KEY enviornment variable is not provided")
        if not self.page_size:
            self.page_size = page_size

        self.headers = {"Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",}


    @staticmethod
    def parse_uri(uri: str) -> Tuple[str, Optional[str]]:
        """
        Parse a RAGFlow URI into dataset id and document id.

        Args:
             uri: URI in the format rag://dataset/{dataset_id}#{document_id}

        Returns:
            Tuple of (dataset id, document id)

        Raises:
            ValueError: If the URI is invalid
        """
        parsed = urlparse(uri)
        if parsed.scheme != "rag":
            raise ValueError(f"Invalid URI scheme: {uri}")

        path_parts = parsed.path.split("/")
        if len(path_parts) < 1:
            raise ValueError(f"Invalid URI scheme: {uri}")

        dataset_id = path_parts[1]
        document_id = parsed.fragment or []

        return dataset_id, document_id

    def search_relevant_documents(
            self,
            question: str,
            datasets: list[Dataset] = [],
            top_k: Optional[int] = 1024,
            similarity_threshold: Optional[float] = 0.2,
    ) -> RetrievalResult:
        """
        Search for relevant documents from RAGFlow API.

        Args:
             question: Search query string.
             datasets: List of datasets to query (empty for all avaliable datasets).
             top_k: Optional maximum number of chunks to return (defaults to 1024).
             similarity_threshold: Optional minimum similarity threshold for chunks to return (defaults to 0.2).

        Returns:
            RetrievalResult: RetrievalResult containing relevant chunks and metadata.

        Raises:
            ValueError: If the query is empty or invalid parameters are provided.
            HTTPException: If the API requests fails.
        """
        if not question:
            raise ValueError("Question cannot be empty")

        try:
            dataset_ids: list[str] = []
            document_ids: list[str] = []

            for dataset in datasets:
                if not dataset.uri.startswith("rag:"):
                    logger.warning(f"Skipping unsupported dataset URI: {dataset.uri}")
                    continue

                dataset_id, document_id = self.parse_uri(dataset.uri)
                dataset_ids.append(dataset_id)
                if document_id:
                    document_ids.append(document_id)

            request_body = {
                "question": question,
                "dataset_ids": dataset_ids,
                "document_ids": document_ids,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
                "page_size": self.page_size,
            }

            response = requests.post(
                f"{self.api_url}/api/v1/retrieval",
                headers=self.headers,
                json=request_body,
            )
            response.raise_for_status()
            result = response.json()
            if response.status_code != 200:
                raise Exception(f"Failed to search documents: {response.text}")
            data = result.get("data", {})

            # retrieve documents
            docs_dict: Dict[str, Document] = {}
            for doc in data.get("doc_aggs", []):
                doc_id = doc.get("doc_id")
                if not doc_id:
                    continue

                docs_dict[doc_id] = Document(
                    document_id=doc_id,
                    title=doc.get("doc_name"),
                    url="",
                    chunks=[],
                    metadata={}
                )

            for chunk_data in data.get("chunks", []):
                doc_id = chunk_data.get("document_id")
                if not doc_id or doc_id not in docs_dict:
                    continue
                docs_dict[doc_id].chunks.append(
                    TextChunk(
                        content=chunk_data.get("content", ""),
                        similarity_score=chunk_data.get("similarity", 0.0),
                        metadata={}
                    )
                )

            return RetrievalResult(
                query=question,
                datasets=datasets,
                documents=list(docs_dict.values()),
                metadata={
                    "total_docs": len(docs_dict),
                    "total_chunks": sum(len(doc.chunks) for doc in docs_dict.values()),
                    "query_params": request_body
                }
            )
        except requests.RequestException as e:
            logger.error(f"Failed to search documents: {str(e)}")
            raise Exception(f"API request failed: {str(e)}") from e
        except (KeyError, ValueError, ValidationError) as e:
            logger.error(f"Failed to parse document data: {str(e)}")
            raise Exception(f"Invalid API response: {str(e)}") from e

    def list_datasets(
            self,
            name: Optional[str] = None,
            dataset_id: Optional[str] = None,
    ) -> list[Dataset]:
        """
        List available datasets from RAGFlow API.

        Args:
             name: Optional search name to filter datasets by name/description.
             dataset_id: Optional search id to filter datasets by dataset id.

        Returns:
            List of Dataset Objects.

        Raises:
            HTTPException: If the API request fails.
        """
        try:
            params = {}
            if name:
                params["name"] = name
            if dataset_id:
                params["id"] = dataset_id

            response = requests.get(
                f"{self.api_url}/api/v1/datasets",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            result = response.json()

            return [
                Dataset(
                    description=item.get("description", ""),
                    title=item.get("name", ""),
                    uri=f"rag://dataset/{item.get('id')}",
                    metadata={}
                )
                for item in result.get("data", [])
            ]
        except requests.RequestException as e:
            logger.error(f"Failed to list datasets: {str(e)}")
            raise Exception(f"API request failed: {str(e)}") from e
        except (KeyError, ValueError, ValidationError) as e:
            raise Exception(f"Invalid API response: {str(e)}") from e

    def list_documents(
            self,
            dataset_id: str,
            document_id: Optional[str] = None,
    ) -> list[Document]:
        """
        List available documents from RAGFlow API.

        Args:
             dataset_id: Search id to filter document by datset id.
             document_id: Optional search id to filter documents by document id.

        Returns:
            List of Document Objects.

        Raises:
            HTTPException: If the API request fails.
        """
        try:
            params = {}
            if dataset_id:
                params["dataset_id"] = dataset_id
            if document_id:
                params["id"] = document_id

            response = requests.get(
                f"{self.api_url}/api/v1/datasets/{dataset_id}/documents",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            result = response.json()

            return [
                Document(
                    document_id=item.get("id"),
                    title=item.get("name"),
                    url="",
                    chunks=[],
                    metadata={}
                )
                for item in result.get("data", {}).get("docs", [])
            ]
        except requests.RequestException as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise Exception(f"API request failed: {str(e)}") from e
        except (KeyError, ValueError, ValidationError) as e:
            raise Exception(f"Invalid API response: {str(e)}") from e

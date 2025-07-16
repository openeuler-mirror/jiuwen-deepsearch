# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""Elasticsearch wrapper.

See Also:
    https://docs.llamaindex.ai/en/stable/examples/vector_stores/ElasticsearchIndexDemo/#load-documents-build-vectorstoreindex-with-elasticsearch
    https://docs.llamaindex.ai/en/stable/examples/low_level/oss_ingestion_retrieval/

"""

import asyncio
import copy
from typing import Any, Optional
from collections.abc import Callable

from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode
from llama_index.core.schema import TextNode
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers.vectorstore import AsyncBM25Strategy
from elasticsearch.exceptions import NotFoundError

from src.retrieval.base_retriever import TextChunk, Dataset, Document, RetrievalResult, BaseRetriever as _BaseRetriever
from src.retrieval.graph_retriever.grag.embed_models import EmbedModel
from src.retrieval.graph_retriever.grag.index import BaseESWrapper
from src.retrieval.graph_retriever.grag.search.rrf import reciprocal_rank_fusion


def rrf_nodes(rankings: list[list[TextNode]]) -> list[TextNode]:
    """Merge ranked lists of nodes."""
    # Note: `TextNode` is not hashable
    id2node = {}
    id_rankings = []
    for ranking in rankings:
        ids = []
        for node in ranking:
            id2node[node.node_id] = node
            ids.append(node.node_id)

        id_rankings.append(ids)

    ranked_ids = reciprocal_rank_fusion(id_rankings)
    return [id2node[id_] for id_ in ranked_ids]


class BaseRetriever(BaseESWrapper, _BaseRetriever):
    """Base class for retrieval.

    Support BM25, vector search, and hybrid search.

    """

    def __init__(
        self,
        es_index: str,
        es_url: str,
        embed_model: EmbedModel | None = None,
        es_client: AsyncElasticsearch | None = None,
    ) -> None:
        super().__init__(
            es_index=es_index,
            es_url=es_url,
            es_client=es_client,
        )

        self.embed_model = embed_model
        self._es_bm25: ElasticsearchStore | None = None

        self.dataset = Dataset(title = es_index, uri = es_url + '/' + es_index)

    @property
    def es_dense(self) -> ElasticsearchStore:
        return self.es

    @property
    def es_bm25(self) -> ElasticsearchStore:
        if self._es_bm25 is None:
            self._es_bm25 = ElasticsearchStore(
                index_name=self.es_index,
                es_client=self.es_client,
                retrieval_strategy=AsyncBM25Strategy(),
            )

        return self._es_bm25

    def make_query(
        self,
        query: str | VectorStoreQuery,
        topk: int,
        mode: str,
        embed_model: EmbedModel | None = None,
        query_config: dict | None = None,
    ) -> VectorStoreQuery:
        """Construct a query."""
        if isinstance(query, str):
            query = VectorStoreQuery(
                query_str=query,
                similarity_top_k=topk,
                mode=mode,
                **(query_config or {}),
            )

        if query.query_embedding is None and query.mode != VectorStoreQueryMode.TEXT_SEARCH:
            embed_model = embed_model or self.embed_model
            if embed_model is None:
                raise RuntimeError("require embedding model for vector search")

            query.query_embedding = embed_model.embed_query(query.query_str).tolist()

        return query

    def search(
        self,
        query: str | VectorStoreQuery,
        topk: int = 5,
        mode: str | VectorStoreQueryMode = VectorStoreQueryMode.DEFAULT,
        custom_query: Callable[[dict[str, Any], str | None], dict[str, Any]] = None,
        *,
        query_config: dict | None = None,
    ) -> list[TextNode]:
        """Search.

        Args:
            query (str | VectorStoreQuery): Query.
            topk (int, optional): Top K to return. Defaults to 5.
                If `VectorStoreQuery` is given, `VectorStoreQuery.similarity_top_k` will be used instead.
            mode (str | VectorStoreQueryMode, optional): Query mode. Defaults to VectorStoreQueryMode.DEFAULT.
                "default" -> vector search
                "text_search" -> BM25
                "hybrid" -> hybrid search by merging results of vector search and BM25
            custome_query (Callable, optional): Function to customize the Elasticsearch query body. Defaults to None.
            query_config (dict, optional): Extra args to `VectorStoreQuery`. Defaults to None.

        Raises:
            NotImplementedError: Unsupported query mode.

        Returns:
            list[TextNode]: Top K retrieval results.

        """
        return asyncio.get_event_loop().run_until_complete(
            self.async_search(
                query=query,
                topk=topk,
                mode=mode,
                custom_query=custom_query,
                query_config=query_config,
            )
        )

    async def async_search(
        self,
        query: str | VectorStoreQuery,
        topk: int = 5,
        mode: str | VectorStoreQueryMode = VectorStoreQueryMode.DEFAULT,
        custom_query: Callable[[dict[str, Any], str | None], dict[str, Any]] = None,
        query_config: dict | None = None,
    ) -> list[TextNode]:
        """Asynchronous search."""
        query = self.make_query(query, topk=topk, mode=mode, query_config=query_config)

        if query.mode == VectorStoreQueryMode.DEFAULT:
            return (await self.es_dense.aquery(query, custom_query=custom_query)).nodes

        if query.mode == VectorStoreQueryMode.TEXT_SEARCH:
            return (await self.es_bm25.aquery(query, custom_query=custom_query)).nodes

        if query.mode == VectorStoreQueryMode.HYBRID:
            return await self._hybrid_search(query, custom_query=custom_query)

        raise NotImplementedError(f"unsupported {query.mode=}")

    async def _hybrid_search(
        self,
        query: VectorStoreQuery,
        custom_query: Callable[[dict[str, Any], str | None], dict[str, Any]] = None,
    ) -> list[TextNode]:
        _query_mode = query.mode  # backup

        # Run Dense
        query.mode = VectorStoreQueryMode.DEFAULT
        task_dense = asyncio.create_task(self.es_dense.aquery(query, custom_query=custom_query))

        # Run BM25
        _query = copy.deepcopy(query)
        _query.mode = VectorStoreQueryMode.TEXT_SEARCH
        _query.query_embedding = None
        task_bm25 = asyncio.create_task(self.es_bm25.aquery(_query, custom_query=custom_query))

        # Synchronize
        nodes_dense = (await task_dense).nodes
        nodes_bm25 = (await task_bm25).nodes

        query.mode = _query_mode  # restore

        # RRF is not available with free license of Elasticsearch
        return rrf_nodes([nodes_dense, nodes_bm25])[: query.similarity_top_k]
    
    def list_datasets(
        self, 
        name: Optional[str] = None,
        dataset_id: Optional[str] = None,
    ) -> list[Dataset]:
        return [self.dataset] if not name or name == self.dataset.title else []
    
    def list_documents(self, document_id: str) -> list[Document]:
        es = self.es.client
        try:
            doc = asyncio.run(
                es.get(
                    index=self.es.index_name,
                    id=document_id,
                    source_excludes=[self.es.vector_field, "metadata._node_content"],
                )
            )
            doc = doc["_source"]
            doc = Document(
                document_id=document_id, 
                title=doc["metadata"]["title"], 
                uri=self.dataset.uri + "/_doc/" + document_id,
                chunks=[TextChunk(content=doc["content"], similarity_score=1.0)],
                metadata=doc["metadata"],
            )
            return [doc]
        
        except NotFoundError:
            return []

    def search_relevant_documents(
        self, 
        question: str, 
        datasets: list[Dataset] = [],
        top_k: int = 5
    ) -> RetrievalResult:
        dataset_set = {(dataset.title, dataset.uri) for dataset in datasets}
        if dataset_set and (self.dataset.title, self.dataset.uri) not in dataset_set:
            return []
        
        results = self.search(
            query=question,
            topk=top_k,
        )
        result = RetrievalResult(
            query = question,
            datasets = [self.dataset],
            documents = [
                Document(
                    document_id = doc.id_,
                    title = doc.metadata["title"],
                    url = self.dataset.uri + "/_doc/" + doc.id_,
                    chunks = [TextChunk(content=doc.text, similarity_score=1.0)]
                )
                for doc in results
            ]
        )
        return result
        

class BaseChunkRetriever(BaseRetriever):
    """Retriever that matches both title and content when performing BM25 search.

    Note:
        Assume "title" is in "metadata":
            {"metadata": {"title": ...}, "embedding": ..., "content": ...}

    """

    @staticmethod
    def should_match_title(body: dict, query: str) -> dict:
        try:
            bool_query = body["query"]["bool"]
            if not isinstance(bool_query, dict):
                return body

            must_clause = bool_query.pop("must")
            if not isinstance(must_clause, list):
                return body

        except KeyError:
            return body

        must_clause.append({"match": {"metadata.title": query}})
        bool_query["should"] = must_clause
        return body

    async def async_search(
        self,
        query: str | VectorStoreQuery,
        topk: int = 5,
        mode: str | VectorStoreQueryMode = VectorStoreQueryMode.DEFAULT,
        custom_query: Callable[[dict[str, Any], str | None], dict[str, Any]] = None,
        **kwargs: Any,
    ) -> list[TextNode]:
        if custom_query is None:
            if isinstance(query, VectorStoreQuery):
                mode = query.mode

            if mode in [VectorStoreQueryMode.TEXT_SEARCH, VectorStoreQueryMode.HYBRID]:
                custom_query = self.should_match_title

        return await super().async_search(
            query=query,
            topk=topk,
            mode=mode,
            custom_query=custom_query,
            **kwargs,
        )

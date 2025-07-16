# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import asyncio
import itertools
from typing import Any, Literal
from collections.abc import Iterable
from abc import ABCMeta, abstractmethod

from tqdm import tqdm
from llama_index.core.schema import TextNode
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from elasticsearch import AsyncElasticsearch

from src.retrieval.graph_retriever.grag.embed_models import EmbedModel
from src.retrieval.graph_retriever.grag.index.chunk import TextSplitter


class BaseESWrapper:
    """Base class that wraps Elasticsearch and Llamaindex."""

    def __init__(
        self,
        es_index: str,
        es_url: str,
        es_client: AsyncElasticsearch | None = None,
    ) -> None:
        self.es_index = es_index
        self.es_url = es_url
        self.es_client = es_client or AsyncElasticsearch(self.es_url, timeout=600)
        self._es = ElasticsearchStore(index_name=self.es_index, es_client=self.es_client)

    def __del__(self) -> None:
        # to suppress warning: "Unclosed client session"
        asyncio.get_event_loop().run_until_complete(self.es_client.close())

    @property
    def es(self) -> ElasticsearchStore:
        return self._es


class BaseIndexer(BaseESWrapper, metaclass=ABCMeta):
    """Abstract base class for indexing.

    Notes:
        Need to implement data-specific preprocessing and define mappings for metadata.

    """

    def __init__(
        self,
        es_index: str,
        es_url: str,
        embed_model: EmbedModel | None = None,
        splitter: TextSplitter | None = None,
        es_client: AsyncElasticsearch | None = None,
    ) -> None:
        super().__init__(
            es_index=es_index,
            es_url=es_url,
            es_client=es_client,
        )

        if embed_model and not isinstance(embed_model, EmbedModel):
            raise TypeError(f"{type(embed_model)=}")

        self.embed_model = embed_model
        self.splitter = splitter

    @abstractmethod
    def preprocess(self, doc: dict, splitter: TextSplitter) -> list[TextNode]:
        """Preprocess a document and return a list of chunks."""
        pass

    @abstractmethod
    def get_metadata_mappings(self, **kwargs: Any) -> dict:
        """Return mappings for metadata.

        Examples:
            {"properties": {"title": {"type": "text"}}}

        """
        pass

    async def create_es_index(self, distance_strategy: str = "cosine", analyzer: str | None = None) -> None:
        """Create Elasticsearch index.

        Overwrite this method if needed.

        """
        client: AsyncElasticsearch = self.es.client

        metadata_mappings = self.get_metadata_mappings(analyzer=analyzer)["properties"]
        # See `llama_index.vector_stores.elasticsearch.ElasticsearchStore`
        # See also `llama_index.core.vector_stores.utils.node_to_metadata_dict`
        if "doc_id" in metadata_mappings or "ref_doc_id" in metadata_mappings or "document_id" in metadata_mappings:
            raise ValueError(
                f"`doc_id`, `ref_doc_id`, `document_id` are occupied by LlamaIndex. "
                "We should use other field names to avoid potential conficts and/or unexpected behaviour."
            )

        await client.indices.create(
            index=self.es.index_name,
            mappings={
                "properties": {
                    self.es.vector_field: {
                        "type": "dense_vector",
                        "dims": self.embed_model.get_embedding_dimension(),
                        "index": True,
                        "similarity": distance_strategy,
                    },
                    self.es.text_field: ({"type": "text", "analyzer": analyzer} if analyzer else {"type": "text"}),
                    "metadata": {
                        "properties": {
                            # fields reserved by llama_index; these fields will be overwritten.
                            # See `llama_index.vector_stores.elasticsearch.ElasticsearchStore`
                            # See also `llama_index.core.vector_stores.utils.node_to_metadata_dict`
                            "document_id": {"type": "keyword"},
                            "doc_id": {"type": "keyword"},
                            "ref_doc_id": {"type": "keyword"},
                            **metadata_mappings,
                        }
                    },
                },
            },
        )

    def embed_nodes(self, nodes: list[TextNode], batch_size: int = 32) -> list[TextNode]:
        if self.embed_model is None:
            return nodes

        texts = [node.text for node in nodes]
        embeddings = self.embed_model.embed_docs(texts, batch_size=batch_size).tolist()
        for node, embedding in zip(nodes, embeddings):
            node.embedding = embedding

        return nodes

    def build_index(
        self,
        dataset: Iterable[dict],
        batch_size: int = 128,
        distance_strategy: Literal["cosine", "dot_product", "l2_norm"] = "cosine",
        es_analyzer: str | None = None,
        *,
        debug: bool = False,
    ) -> None:
        """Build an Elasticsearch index for the input `dataset`.

        Note:
            1. Adding data to an existing index is not allowed.
            2. Manually delete an existing index if needed.

        Args:
            dataset (Iterable[dict]): Dataset of documents.
            batch_size (int, optional): Batch size for embedding passages. Defaults to 128.
            distance_strategy (str): Similarity metric supported by Elasticsearch. Defaults to cosine.
            es_analyzer (str, optional): Elasticsearch tokenizer for text field. Defaults to None.
                E.g., use "smartcn" for Chinese text.
                See: https://www.elastic.co/guide/en/elasticsearch/reference/current/specify-analyzer.html
            debug (bool, optional): Debug mode. Defaults to False.
                If True, index the first 100 documents only.

        Raises:
            RuntimeError: If the index exists.

        """
        if self.embed_model is None:
            raise NotImplementedError("build both full-text index and vector index by default")

        asyncio.run(
            self._build_index(
                dataset,
                batch_size=batch_size,
                distance_strategy=distance_strategy,
                es_analyzer=es_analyzer,
                debug=debug,
            )
        )

    async def _build_index(
        self,
        dataset: Iterable[dict],
        batch_size: int = 128,
        distance_strategy: str = "cosine",
        es_analyzer: str | None = None,
        *,
        debug: bool = False,
    ) -> None:
        client: AsyncElasticsearch = self.es.client
        if await client.indices.exists(index=self.es.index_name):
            raise RuntimeError(f"index {self.es.index_name} exists")

        await self.create_es_index(distance_strategy=distance_strategy, analyzer=es_analyzer)

        total = None
        datastream = dataset
        if debug:
            total = 100
            datastream = itertools.islice(dataset, total)

        cache = []
        for doc in tqdm(
            datastream,
            desc="indexing documents",
            total=total,
        ):
            cache.extend(self.preprocess(doc, self.splitter))

            if len(cache) > batch_size:
                nodes = self.embed_nodes(cache[:batch_size], batch_size)
                cache = cache[batch_size:]
                await self.es.async_add(nodes=nodes, create_index_if_not_exists=False)

        if cache:
            await self.es.async_add(nodes=self.embed_nodes(cache, batch_size), create_index_if_not_exists=False)

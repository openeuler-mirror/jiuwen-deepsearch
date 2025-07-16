# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import json
import os
from typing import Any

from llama_index.core.schema import TextNode
from elasticsearch import Elasticsearch

from src.retrieval.graph_retriever.grag.index import BaseIndexer
from src.retrieval.graph_retriever.grag.embed_models import SBERT
from src.retrieval.graph_retriever.grag.index.chunk import TextSplitter
from src.retrieval.graph_retriever.grag.utils import DATA_DIR
from src.retrieval.graph_retriever.grag.pipeline.utils import prepare_triples


class TripleIndexer(BaseIndexer):
    def preprocess(self, doc: dict, splitter: TextSplitter) -> list[TextNode]:
        return [TextNode(text=doc["text"], metadata=doc["metadata"])]

    def get_metadata_mappings(self, **kwargs: Any) -> dict:
        return {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "triple": {"type": "text", "index": False},
            }
        }


def main():
    embed_model = SBERT(os.getenv("EMBED_MODEL"), device="cuda:1")
    es_url = os.getenv("TRIPLE_ES_URL")
    es_index = os.getenv("TRIPLE_ES_INDEX")
    text_es_url = os.getenv("CHUNK_ES_URL")
    text_es_index = os.getenv("CHUNK_ES_INDEX")
    data_dir = DATA_DIR / "triple_extraction" / "chunk2triple_completions_0-10.jsonl"
    batch_size = 1024

    es = TripleIndexer(
        es_index=es_index,
        es_url=es_url,
        embed_model=embed_model,
    )

    chunk2triples = {}
    with open(data_dir, "r", encoding="utf-8") as f:
        for line in f:
            chunk2triples.update(json.loads(line))

    datastream = prepare_triples(Elasticsearch(text_es_url), chunk2triples, text_es_index)

    es.build_index(datastream, batch_size=batch_size, debug=False)


if __name__ == "__main__":
    main()

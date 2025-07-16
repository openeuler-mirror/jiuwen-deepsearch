# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import os
from typing import Any

from llama_index.core.schema import Document, TextNode

from src.retrieval.graph_retriever.grag.embed_models import SBERT
from src.retrieval.graph_retriever.grag.index import BaseIndexer
from src.retrieval.graph_retriever.grag.utils import load_jsonl, DATA_DIR
from src.retrieval.graph_retriever.grag.index.chunk import LlamaindexSplitter, TextSplitter


class TextIndexer(BaseIndexer):
    def preprocess(self, doc: dict, splitter: TextSplitter) -> list[TextNode]:
        # global doc id here
        metadata = {"title": doc["title"], "paragraph_id": doc["paragraph_id"]}

        doc = Document(
            text=doc["paragraph_text"],
            metadata=metadata,
            excluded_embed_metadata_keys=list(metadata.keys()),
            excluded_llm_metadata_keys=list(metadata.keys()),
        )

        return splitter.split(doc)

    def get_metadata_mappings(self, **kwargs: Any) -> dict:
        analyzer = kwargs.get("analyzer")
        return {
            "properties": {
                "title": ({"type": "text", "analyzer": analyzer} if analyzer else {"type": "text"}),
                "paragraph_id": {"type": "keyword"},
            }
        }


def main():
    embed_model = SBERT(os.getenv("EMBED_MODEL"), device="cuda:1")
    batch_size = 384
    es_url=os.getenv("CHUNK_ES_URL")
    es_index=os.getenv("CHUNK_ES_INDEX")
    data_dir = DATA_DIR / "test_paragraphs.jsonl"

    splitter = LlamaindexSplitter(
        tokenizer=embed_model.model.tokenizer,
        chunk_size=200,
        chunk_overlap=0,
    )

    es = TextIndexer(
        es_index=es_index,
        es_url=es_url,
        embed_model=embed_model,
        splitter=splitter,
    )

    es.build_index(
        load_jsonl(data_dir),
        batch_size=batch_size,
        debug=False,
    )


if __name__ == "__main__":
    main()

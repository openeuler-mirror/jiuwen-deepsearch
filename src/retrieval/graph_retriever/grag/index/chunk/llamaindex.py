# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from llama_index.core.schema import TextNode
from llama_index.core.node_parser import SentenceSplitter
from transformers import PreTrainedTokenizerBase

from src.retrieval.graph_retriever.grag.index.chunk.base import TextSplitter


class LlamaindexSplitter(TextSplitter):
    def __init__(
        self,
        tokenizer: PreTrainedTokenizerBase,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        splitter_config: dict | None = None,
    ) -> None:
        """Wrapper of llamaindex's splitter.

        Args:
            tokenizer (PreTrainedTokenizerBase): Tokenizer.
            chunk_size (int | None, optional): Chunk size to split documents into passages. Defaults to None.
                Note: this is based on tokens produced by the tokenizer of embedding model.
                If None, set to the maximum sequence length of the embedding model.
            chunk_overlap (int | None, optional): Window size for passage overlap. Defaults to None.
                If None, set to `chunk_size // 5`.
            splitter_config (dict, optional): Other arguments to SentenceSplitter. Defaults to None.

        """
        super().__init__()
        if not isinstance(tokenizer, PreTrainedTokenizerBase):
            raise TypeError(f"{type(tokenizer)=}")

        self._tokenizer = tokenizer

        if not isinstance(splitter_config, dict):
            splitter_config = {
                "paragraph_separator": "\n",
            }

        chunk_size = chunk_size or tokenizer.max_len_single_sentence
        chunk_size = min(chunk_size, tokenizer.max_len_single_sentence)

        self._splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap or chunk_size // 5,
            tokenizer=self._tokenizer.tokenize,
            **splitter_config,
        )

    def split(self, doc: TextNode) -> list[TextNode]:
        # Note: we don't want to consider the length of metadata for chunking
        if not doc.excluded_embed_metadata_keys:
            doc.excluded_embed_metadata_keys = list(doc.metadata.keys())

        if not doc.excluded_llm_metadata_keys:
            doc.excluded_llm_metadata_keys = list(doc.metadata.keys())

        return self._splitter.get_nodes_from_documents([doc])

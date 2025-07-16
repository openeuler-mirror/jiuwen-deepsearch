# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from typing import Any

import torch
from sentence_transformers import SentenceTransformer

from src.retrieval.graph_retriever.grag.embed_models.base import EmbedModel
from src.retrieval.graph_retriever.grag.utils import load_sentence_transformer


class SBERT(EmbedModel):
    def __init__(
        self,
        model: str | SentenceTransformer,
        device: str | None = None,
        **model_args: Any,
    ) -> None:
        self._model = (
            model
            if isinstance(model, SentenceTransformer)
            else load_sentence_transformer(model, device=device, **model_args)
        )

    @property
    def model(self) -> SentenceTransformer:
        return self._model

    def embed_docs(
        self,
        texts: list[str],
        batch_size: int = 32,
        **kwargs: Any,
    ) -> torch.Tensor:
        return self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_tensor=True,
            **kwargs,
        )

    def embed_query(self, text: str, **kwargs: Any) -> torch.Tensor:
        return self._model.encode(text, convert_to_tensor=True, **kwargs)

    def embed_queries(
        self,
        texts: list[str],
        batch_size: int = 32,
        **kwargs: Any,
    ) -> torch.Tensor:
        return self.embed_docs(texts, batch_size=batch_size, **kwargs)

    def get_embedding_dimension(self) -> int:
        dim = self.model.get_sentence_embedding_dimension()
        if not isinstance(dim, int):
            raise RuntimeError(f"{dim=}; expect int")

        return dim



# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from abc import ABCMeta, abstractmethod
from typing import Any

import torch


class EmbedModel(metaclass=ABCMeta):
    @abstractmethod
    def embed_docs(
        self,
        texts: list[str],
        batch_size: int | None = None,
        **kwargs: Any,
    ) -> torch.Tensor:
        """Embed documents."""
        pass

    @abstractmethod
    def embed_query(self, text: str, **kwargs: Any) -> torch.Tensor:
        """Embed a single query."""
        pass

    def embed_queries(self, texts: list[str], **kwargs: Any) -> torch.Tensor:
        """Embed queries.

        Note:
            Overwrite this method if batch computing should be supported.
        """
        return torch.stack([self.embed_query(x, **kwargs) for x in texts])

    def get_embedding_dimension(self) -> int:
        return self.embed_query("X").shape[-1]

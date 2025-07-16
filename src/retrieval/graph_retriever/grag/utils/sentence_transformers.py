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
from weakref import WeakValueDictionary

from sentence_transformers import SentenceTransformer

from src.retrieval.graph_retriever.grag.utils.common import DATA_DIR


_MODEL_CACHE = WeakValueDictionary()


def load_sentence_transformer(
    model_name: str,
    cache_folder: str | os.PathLike = DATA_DIR / "sentence_transformers",
    **kwargs: Any,
) -> SentenceTransformer:
    model = _MODEL_CACHE.get(model_name)
    if model is not None:
        return model

    if os.path.exists(cache_folder):
        model = SentenceTransformer(model_name, cache_folder=cache_folder, **kwargs)
    else:
        model = SentenceTransformer(model_name, **kwargs)

    _MODEL_CACHE[model_name] = model
    return model

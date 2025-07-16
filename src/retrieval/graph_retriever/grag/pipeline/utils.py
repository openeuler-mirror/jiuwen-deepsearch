# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import itertools
import logging
from elasticsearch import Elasticsearch
from typing import Iterator

from src.retrieval.graph_retriever.grag.utils.es import iter_index

_LOGGER = logging.getLogger(__name__)

OPENAI_RATE_LIMIT = 50000

empty_triples_count = 0


def prepare_triples(es: Elasticsearch, chunk2triples: dict[str, list[list[str]]], index_name: str) -> Iterator[dict]:
    """Generate document dictionaries from Elasticsearch index and extracted triples (from API).
       This dictionary is used to then build the triplets index.

    Args:
        es (Elasticsearch): Elasticsearch client
        chunk2triples (dict[str, list[list[str]]]): Dictionary mapping chunks to extracted triples
        index_name (str): Name of the Elasticsearch index

    Yields:
        Iterator[dict]: Document dictionaries containing text and metadata
    """
    global empty_triples_count
    for item in itertools.chain.from_iterable(
        iter_index(
            client=es,
            index=index_name,
            batch_size=256,
        )
    ):

        chunk_id = item["_id"]
        chunk = item["_source"]["content"]
        triples = chunk2triples.get(chunk, None)
        if triples is None:
            _LOGGER.warning(f"{chunk=} not found")
            continue

        if not triples:
            # _LOGGER.warning(f"no triples extracted for {chunk=}")
            empty_triples_count += 1
            continue

        for triple in triples:
            if not isinstance(triple, list):
                raise TypeError(f"{type(triple)=}")

            if len(triple) == 0:
                continue

            triple = [str(x) for x in triple]

            yield {
                "text": " ".join(triple),
                "metadata": {
                    "chunk_id": chunk_id,
                    "triple": triple,
                },
            }
        print("number of empty triples", empty_triples_count)

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

import asyncio
from tqdm import tqdm
from elasticsearch import Elasticsearch

from src.llm.llm_wrapper import LLMWrapper

from src.retrieval.graph_retriever.grag.utils import load_jsonl, DATA_DIR
from src.retrieval.graph_retriever.grag.utils.es import iter_index
from src.retrieval.graph_retriever.grag.reranker.llm_openie import PROMPT as PROMPT_TEMPLATE, LLMOpenIE


ES_HOST = os.getenv("CHUNK_ES_URL")
CHUNK_FILE_PATH = DATA_DIR / "triple_extraction" / "example_chunks.jsonl"


async def process_chunk(chunk, save_path):
    prompt = PROMPT_TEMPLATE.format(passage=chunk["content"], wiki_title=chunk["title"])
    completion = await LLMWrapper("basic").ainvoke(prompt)
    _, triples_list = LLMOpenIE.match_entities_triples(completion.content)
    buffer = {chunk["content"]: triples_list}
    
    with open(save_path, "a") as f:
        f.write(json.dumps(buffer, ensure_ascii=False) + "\n")


async def process_data(data, save_path, start_idx=0):
    tasks = []
    for chunk in tqdm(data[start_idx:], desc="Processing chunks"):
        task = asyncio.create_task(process_chunk(chunk, save_path))
        tasks.append(task)

    await asyncio.gather(*tasks)


def load_index() -> list[dict]:
    es = Elasticsearch(ES_HOST)
    with open(CHUNK_FILE_PATH, "w+") as f:
        for batch in tqdm(iter_index(es, os.getenv("CHUNK_ES_INDEX"),), desc="downloading chunks..."):
            for item in batch:
                content = item["_source"]["content"]
                title = item["_source"]["metadata"]["title"]
                # prompt = PROMPT_TEMPLATE.format(passage=chunk, wiki_title=title)
                f.write(json.dumps({"title": title, "content": content}, ensure_ascii=False))
                f.write("\n")


def main():
    load_index()
    asyncio.run(
        process_data(
            load_jsonl(CHUNK_FILE_PATH),
            DATA_DIR / "triple_extraction" / "chunk2triple_completions.jsonl",
            start_idx=0,
        )
    )


if __name__ == "__main__":
    main()

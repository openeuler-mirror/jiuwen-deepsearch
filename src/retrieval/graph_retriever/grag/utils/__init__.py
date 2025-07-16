# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from src.retrieval.graph_retriever.grag.utils.common import ROOT, DATA_DIR, deduplicate
from src.retrieval.graph_retriever.grag.utils.io import load_json, load_jsonl, save_json, save_jsonl
from src.retrieval.graph_retriever.grag.utils.sentence_transformers import load_sentence_transformer
from src.retrieval.graph_retriever.grag.utils.es import iter_index, iter_index_compat

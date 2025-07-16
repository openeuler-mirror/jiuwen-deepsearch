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
from pathlib import Path


def load_json(fp):
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(fp):
    data = []
    with open(fp, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data


def load_jsonl_as_iterator(fp):
    with open(fp, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def save_json(fp, data):
    if not isinstance(fp, Path):
        fp = Path(fp)

    fp.parent.mkdir(parents=True, exist_ok=True)

    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_jsonl(fp, data):
    if not isinstance(fp, Path):
        fp = Path(fp)

    fp.parent.mkdir(parents=True, exist_ok=True)

    with open(fp, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False))
            f.write("\n")

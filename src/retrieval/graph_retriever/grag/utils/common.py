# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from pathlib import Path
from typing import TypeVar
from collections.abc import Hashable, Iterable, Callable
import hashlib

ROOT = Path(__file__).absolute().parent.parent.parent
DATA_DIR = ROOT / "data"

# Generic
T = TypeVar("T")


def deduplicate(
    data: Iterable[T],
    key: Callable[[T], Hashable] = lambda x: x,
) -> list[T]:
    exist = set()
    ret = []
    for item in data:
        val = key(item)
        if val in exist:
            continue
        exist.add(val)
        ret.append(item)
    return ret


def get_str_hash(s: str) -> str:
    hash_obj = hashlib.sha1(s.encode())
    return hash_obj.hexdigest()

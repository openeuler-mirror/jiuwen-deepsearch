import json
import logging
from typing import Sequence, Any

import json_repair
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


def messages_to_json(messages: Sequence[Any] | BaseMessage) -> str:
    result = []
    if isinstance(messages, BaseMessage):
        result = messages.model_dump()
    else:
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif isinstance(msg, BaseMessage):
                result.append(msg.model_dump())
            else:
                result.append(str(msg))
                logger.error(f"error message type: {msg}")

    return json.dumps(result, ensure_ascii=False, indent=4)


def normalize_json_output(input_data: str) -> str:
    """
    规范化 JSON 输出

    Args:
        input_data: 可能包含 JSON 的字符串内容

    Returns:
        str: 规范化的 JSON 字符串，如果不是 JSON, 则为原始内容
    """
    processed = input_data.strip()
    json_signals = ('{', '[', '```json', '```ts')

    if not any(indicator in processed for indicator in json_signals[:2]) and not any(marker in processed for marker in json_signals[2:]):
        return processed

    # 处理代码块标记
    code_blocks = {
        'prefixes': ('```json', '```ts'),
        'suffix': '```'
    }
    for prefix in code_blocks['prefixes']:
        if processed.startswith(prefix):
            processed = processed[len(prefix):].lstrip('\n')

    if processed.endswith(code_blocks['suffix']):
        processed = processed[:-len(code_blocks['suffix'])].rstrip('\n')

    # 尝试进行JSON修复和序列化
    try:
        reconstructed = json_repair.loads(processed)
        return json.dumps(reconstructed, ensure_ascii=False)
    except Exception as error:
        logger.error(f"JSON normalization error: {error}")
        return input_data.strip()

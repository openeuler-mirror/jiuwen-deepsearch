import json
import logging

import json_repair

logger = logging.getLogger(__name__)


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
        logger.warning(f"JSON normalization error: {error}")
        return input_data.strip()

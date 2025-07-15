from .llm_wrapper import LLMWrapper
from .openai_creator import OpenAICreator
from .deepseek_creator import DeepSeekCreator

LLMWrapper.register("openai", OpenAICreator)
LLMWrapper.register("deepseek", DeepSeekCreator)
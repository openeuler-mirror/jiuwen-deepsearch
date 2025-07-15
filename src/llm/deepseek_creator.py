from langchain_deepseek import ChatDeepSeek

class DeepSeekCreator:
    def __init__(self, llm_conf: dict):
        llm_conf["api_base"] = llm_conf.pop("base_url", None)
        self.llm_conf = llm_conf

    def create(self):
        return ChatDeepSeek(**self.llm_conf)
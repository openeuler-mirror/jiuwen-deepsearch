from langchain_openai import ChatOpenAI

class OpenAICreator:
    def __init__(self, llm_conf: dict):
        self.llm_conf = llm_conf

    def create(self):
        return ChatOpenAI(**self.llm_conf)
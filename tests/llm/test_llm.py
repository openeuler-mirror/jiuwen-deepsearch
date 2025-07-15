from langchain_core.messages import HumanMessage
from src.llm.llm_wrapper import LLMWrapper

if __name__ == "__main__":
    client = LLMWrapper("basic")
    msgs = [HumanMessage(content="Hello")]
    resp = client.invoke(msgs)
    print(resp)
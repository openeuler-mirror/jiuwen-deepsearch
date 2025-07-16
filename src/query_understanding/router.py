import logging
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Annotated

from src.manager.search_context import SearchContext
from src.prompts.template import apply_system_propmt
from src.llm.llm_wrapper import LLMWrapper

logging = logging.getLogger(__name__)


@tool
def send_to_planner(
        query_title: Annotated[str, "The title of the query to be handed off."],
        language: Annotated[str, "The user's detected language locale."]
):
    """
    This tool didn't return anything: it was just used as a way to signal to the LLM that it needed to be handed off to the planner agent.
    """
    return

def classify_query(context: SearchContext, config: RunnableConfig) -> (bool, str):
    """
        Query routing: Determine whether to enter the deep (re)search process.

        Args:
        context: Current agent context
        config: Current runtime configuration

        Returns:
            bool: whether to enter the deep (re)search process.
            str: language locale.
    """
    logging.info(f"Begin query classification operation.")
    prompts = apply_system_propmt("entry", context, config)
    response = (
        LLMWrapper("basic")
        .bind_tools([send_to_planner])
        .invoke(prompts)
    )
    if len(response.tool_calls) > 0:
        return True, response.tool_calls[0].get("args", {}).get("language")
    else:
        return False, "zh-CN"
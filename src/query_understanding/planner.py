import json
import logging
from json import JSONDecodeError

from langchain_core.message import AIMessage
from langchain_core.runnables import RunnableConfig

from src.llm import LLMWrapper
from src.manager.search_context import SearchContext, Plan
from src.prompts import apply_system_prompt
from src.utils.llm_utils import normalize_json_output

logger = logging.getLogger(__name__)

class Planner:
    def __init__(self):
        self.llm = LLMWrapper("basic").with_structured_output(schema=Plan, method="json_mode")

    def generate_plan(self, context: SearchContext, config: RunnableConfig) -> dict:
        """Generating a complete plan."""
        logger.info("Planner starting")
        messages = apply_system_prompt("planner", context, config)

        llm_result = ""
        plan = {}
        try:
            # invoke LLM
            response = self.llm.invoke(messages)
            llm_result = response.model_dump_json(indent=4)
            logger.info(f"Planner LLM result: {llm_result}")

            generated_plan = json.loads(normalize_json_output(llm_result))
            # validation
            plan = Plan.model_validate(generated_plan)
        except JSONDecodeError:
            logger.error("Planner LLM response failed JSON deserialization")
        except Exception as e:
            logger.error(f"Error when Planner generating a plan: {e}")
        
        return {
            "messages": [AIMessage(name="planner", content=llm_result)],
            "current_plan": plan
        }

if __name__  == "__main__":
    context: SearchContext = {
        "messages": [
            {
                "type": "user",
                "content": "中国平均海拔"
            }
        ]
    }

    config = RunnableConfig

    planner = Planner()
    print(planner.generate_plan(context,config))

import json
import logging
from json import JSONDecodeError

from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from src.llm import LLMWrapper
from src.manager.search_context import SearchContext, Plan, TaskType
from src.prompts import apply_system_prompt
from src.utils.llm_utils import normalize_json_output, messages_to_json

logger = logging.getLogger(__name__)


class Planner:
    llm: BaseChatModel

    def __init__(self):
        self.llm = LLMWrapper("basic").with_structured_output(schema=Plan, method="json_mode")

    def generate_plan(self, context: SearchContext, config: RunnableConfig) -> dict:
        """Generating a complete plan."""
        logger.info("Planner starting")
        messages = apply_system_prompt("planner", context, config)

        logger.debug(f"planner invoke messages: {messages_to_json(messages)}")

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
        except OutputParserException as e:
            logger.error(f"LLM does not follow the structured output: {e}")
            llm_result = e.llm_output
            plan = try_repair_plan(llm_result)
        except Exception as e:
            logger.error(f"Error when Planner generating a plan: {e}")

        return {
            "messages": [AIMessage(name="planner", content=llm_result)],
            "current_plan": plan
        }


def try_repair_plan(llm_output: str) -> Plan | dict:
    logger.info("try to repair the plan for LLM output...")
    new_plan = {}
    try:
        data = json.loads(llm_output)
    except:
        logger.error("Unable to repair the plan structure, it is not a correct JSON.")
        return new_plan

    # 修复language字段
    if not data.get("language"):
        data["language"] = "zh-CN"
    if not isinstance(data["language"], str):
        data["language"] = str(data["language"])

    # 修复title字段
    if not data.get("title"):
        data["title"] = ""
    if not isinstance(data["title"], str):
        data["title"] = str(data["title"])

    # 修复thought字段
    if not data.get("thought"):
        data["thought"] = ""
    if not isinstance(data["thought"], str):
        data["thought"] = str(data["thought"])

    # 修复is_research_completed字段
    if "is_research_completed" not in data or not isinstance(data["is_research_completed"], bool):
        data["is_research_completed"] = False

    # 修复tasks字段
    if "tasks" not in data or not isinstance(data["tasks"], list):
        data["tasks"] = []

    tasks = []
    for task in data["tasks"]:
        # 确保每个任务项是字典
        if not isinstance(task, dict):
            continue

        # 修复task.title字段
        if not task.get("title"):
            task["title"] = ""
        if not isinstance(task["title"], str):
            task["title"] = str(task["title"])

        # 修复task.description字段
        if not task.get("description"):
            task["description"] = ""
        if not isinstance(task["description"], str):
            task["description"] = str(task["description"])

        if not task.get("title") and not task.get("description"):
            continue

        # 修复type字段
        if "type" not in task or task["type"] not in (TaskType.INFO_COLLECTING.value, TaskType.PROGRAMMING.value):
            task["type"] = TaskType.INFO_COLLECTING.value

        # 删除task.task_result字段
        task["task_result"] = None

        tasks.append(task)

    data["tasks"] = tasks

    try:
        new_plan = Plan.model_validate(data)
        logger.info("repair the plan for LLM output successfully")
    except Exception as e:
        logger.error(f"repair the plan for LLM output failed: {e}")

    return new_plan


if __name__ == "__main__":
    context: SearchContext = {
        "messages": [
            HumanMessage("中国平均海拔"),
        ]
    }

    config: RunnableConfig = {
        "configurable": {
            "max_task_num": 5,
            "language": "zh-CN"
        }
    }

    planner = Planner()
    print(planner.generate_plan(context, config))

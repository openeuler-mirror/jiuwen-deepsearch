import logging

from langchain_core.runnables import RunnableConfig

from src.manager.search_context import Step, StepType
from src.programmer import Programmer


def setup_logging(log_level: str):
    level = getattr(logging, log_level.upper(), logging.INFO)
    # logging config
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    )


if __name__ == "__main__":
    setup_logging("debug")
    config = RunnableConfig()

    programmer = Programmer(config)

    task = Step(
        title="数学算式计算",
        description="计算241 - (-241) + 1的精确结果，并解释步骤。",
        type=StepType("programming"),
        step_result=None
    )

    result = programmer.run(task)
    print(result)

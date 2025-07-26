import enum
import logging
import json

from fastapi import APIRouter
from langchain_core.runnables import RunnableConfig
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse

from src.manager.workflow import Workflow

workflow = Workflow()
workflow.build_graph()

adapter = APIRouter(
    prefix="/api",
    tags=["api"],
)


class RAGConfigResponse(BaseModel):
    """Response model for RAG config."""

    provider: str | None = Field(
        None, description="The provider of the RAG, default is ragflow"
    )


class ConfigResponse(BaseModel):
    """Response model for server config."""

    rag: RAGConfigResponse = Field(..., description="The config of the RAG")
    models: dict[str, list[str]] = Field(..., description="The configured models")


class ContentItem(BaseModel):
    type: str = Field(..., description="The type of content (text, image, etc.)")
    text: Optional[str] = Field(None, description="The text content if type is 'text'")
    image_url: Optional[str] = Field(
        None, description="The image URL if type is 'image'"
    )


class ChatMessage(BaseModel):
    role: str = Field(
        ..., description="The role of the message sender (user or assistant)"
    )
    content: Union[str, List[ContentItem]] = Field(
        ...,
        description="The content of the message, either a string or a list of content items",
    )


class Resource(BaseModel):
    """
    Resource is a class that represents a resource.
    """

    uri: str = Field(..., description="The URI of the resource")
    title: str = Field(..., description="The title of the resource")
    description: str | None = Field("", description="The description of the resource")


class ReportStyle(enum.Enum):
    ACADEMIC = "academic"
    POPULAR_SCIENCE = "popular_science"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"


class ChatRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = Field(
        [], description="History of messages between the user and the assistant"
    )
    resources: Optional[List[Resource]] = Field(
        [], description="Resources to be used for the research"
    )
    debug: Optional[bool] = Field(False, description="Whether to enable debug logging")
    thread_id: Optional[str] = Field(
        "__default__", description="A specific conversation identifier"
    )
    max_plan_iterations: Optional[int] = Field(
        1, description="The maximum number of plan iterations"
    )
    max_step_num: Optional[int] = Field(
        3, description="The maximum number of steps in a plan"
    )
    max_search_results: Optional[int] = Field(
        3, description="The maximum number of search results"
    )
    auto_accepted_plan: Optional[bool] = Field(
        False, description="Whether to automatically accept the plan"
    )
    interrupt_feedback: Optional[str] = Field(
        None, description="Interrupt feedback from the user on the plan"
    )
    mcp_settings: Optional[dict] = Field(
        None, description="MCP settings for the chat request"
    )
    enable_background_investigation: Optional[bool] = Field(
        True, description="Whether to get background investigation before plan"
    )
    report_style: Optional[ReportStyle] = Field(
        ReportStyle.ACADEMIC, description="The style of the report"
    )
    enable_deep_thinking: Optional[bool] = Field(
        False, description="Whether to enable deep thinking"
    )


def _make_event(event_type: str, data: dict[str, any]):
    if data.get("content") == "":
        data.pop("content")
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


agent_map = {
    "entry": "coordinator",
    "planner": "planner",
    "plan_reasoning": "planner",
    "research_manager": "researcher",
    "info_collector": "researcher",
    "programmer": "coder",
    "reporter": "reporter",
    "tavily_web_search": "researcher",
    "web_crawler": "researcher",
    "python_programmer_tool": "researcher",
}


async def _astream_workflow_adapter(req: ChatRequest):
    if len(req.messages) == 0:
        yield _make_event("message_chunk",
                          {
                              "thread_id": "fake_thread_id123",
                              "agent": "coordinator",
                              "id": "fake_id123",
                              "role": "assistant",
                              "content": "invalid input",
                          })
    async for msg in workflow.run(
            messages=req.messages[0].content,
            session_id=req.thread_id,
            local_datasets=[],
    ):
        logging.debug(f"received workflow message: {msg}")
        json_msg = json.loads(msg)
        old_agent = json_msg["agent"]
        new_agent = agent_map[old_agent]
        logging.debug(f"old agent:{old_agent}, new agent: {new_agent}")

        event_stream_message: dict[str, any] = {
            "thread_id": json_msg["session_id"],
            "agent": new_agent,
            "id": json_msg["id"],
            "role": json_msg["role"],
            "content": json_msg["content"],
        }

        event_msg = _make_event("message_chunk", event_stream_message)
        logging.debug(f"event message: {event_msg}")
        yield event_msg


@adapter.get("/config")
async def config():
    logging.info("get config")
    return ConfigResponse(
        rag=RAGConfigResponse(provider=None),
        models={}
    )


@adapter.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    logging.info("chat stream")
    return StreamingResponse(
        _astream_workflow_adapter(req),
        media_type="text/event-stream",
    )

from typing import AsyncGenerator
from pydantic import BaseModel
import uuid
from langchain_core.messages import SystemMessage, HumanMessage

from synphora.sse import SseEvent, RunStartedEvent, RunFinishedEvent, TextMessageEvent
from synphora.llm import create_llm_client

class AgentRequest(BaseModel):
    text: str


def generate_id() -> str:
    return str(uuid.uuid4())[:8]

async def generate_text_message(content_parts: list[str]) -> AsyncGenerator[SseEvent, None]:
    message_id = generate_id()

    for content in content_parts:
        yield TextMessageEvent.new(message_id=message_id, content=content)

async def generate_llm_message(messages) -> AsyncGenerator[SseEvent, None]:
    message_id = generate_id()

    llm = create_llm_client()
    for chunk in llm.stream(messages):
        if chunk.content:
            yield TextMessageEvent.new(message_id=message_id, content=chunk.content)


async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[SseEvent, None]:

    yield RunStartedEvent.new()

    text_message_parts = request.text.split()
    async for event in generate_text_message(text_message_parts):
        yield event

    llm_messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=request.text),
    ]
    async for event in generate_llm_message(llm_messages):
        yield event

    yield RunFinishedEvent.new()

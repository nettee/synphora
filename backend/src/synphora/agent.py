from typing import AsyncGenerator
from pydantic import BaseModel
import uuid
from langchain_core.messages import SystemMessage, HumanMessage
from enum import Enum

from synphora.sse import ( SseEvent, RunStartedEvent, RunFinishedEvent, TextMessageEvent )
from synphora.llm import create_llm_client
from synphora.tool import ArticleEvaluationTool, DemoTool
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 超时配置
AGENT_TIMEOUT_SECONDS = 30
TOOL_TIMEOUT_SECONDS = 60

class AgentRequest(BaseModel):
    message: str


class Suggestions(Enum):
    EVALUATE_ARTICLE = "评价这篇文章"
    ANALYZE_ARTICLE_POSITION = "分析文章定位"
    WRITE_CANDIDATE_TITLES = "撰写候选标题"


# Agent configuration
USE_AGENT_MODE = True  # 配置开关控制使用模式

def generate_id() -> str:
    return str(uuid.uuid4())[:8]

def get_suggestions():
    suggestions = [suggestion.value for suggestion in Suggestions]
    return suggestions

async def generate_text_message(content_parts: list[str]) -> AsyncGenerator[SseEvent, None]:
    message_id = generate_id()

    for content in content_parts:
        yield TextMessageEvent.new(message_id=message_id, content=content)

async def generate_llm_message(messages) -> AsyncGenerator[SseEvent, None]:
    message_id = generate_id()

    llm = create_llm_client()
    print(f'llm request, messages: {messages}')
    for chunk in llm.stream(messages):
        if chunk.content:
            yield TextMessageEvent.new(message_id=message_id, content=chunk.content)


class State(BaseModel):
    request: AgentRequest
    tool_calls: list

async def start_node(state: State) -> AsyncGenerator[SseEvent, None]:
    print(f'start_node, state: {state}')
    yield RunStartedEvent.new()


async def reason_node(state: State) -> AsyncGenerator[SseEvent, None]:
    print(f'reason_node, state: {state}')
    tools = DemoTool.get_tools()
    llm = create_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    tool_decision_system_prompt = """
你是一个智能助手，可以使用工具来帮助用户处理文章相关的任务。
"""
    
    tool_decision_user_prompt = f"""
根据用户的请求，决定调用哪个工具来完成任务。

用户请求：{state.request.message}
"""
    
    tool_decision_messages = [
        SystemMessage(content=tool_decision_system_prompt),
        HumanMessage(content=tool_decision_user_prompt),
    ]

    response = llm_with_tools.stream(tool_decision_messages)
    tool_calls = []
    message_id = generate_id()
    for chunk in response:
        if chunk.content:
            yield TextMessageEvent.new(
                message_id=message_id,
                content=chunk.content
            )
        if chunk.tool_calls:
            tool_calls.extend(chunk.tool_calls)

    state.tool_calls = tool_calls


async def act_node(state: State) -> AsyncGenerator[SseEvent, None]:
    """
    执行工具并通过事件委托机制处理SSE事件
    """

    print(f'act_node, state: {state}')

    tool_calls = state.tool_calls
    if not tool_calls:
        raise ValueError("没有工具调用")

    tool_name = tool_calls[0]['name']
    
    if tool_name in ['comment_article', 'evaluate_article']:
        tool = ArticleEvaluationTool()
        
        # Note: AsyncGenerator cannot use asyncio.wait_for directly
        # Using a different approach for timeout handling
        async for event in tool.execute():
            yield event
    
    else:
        # 未知工具，返回错误消息
        raise ValueError(f"未知工具: {tool_name}")


async def end_node(state: State) -> AsyncGenerator[SseEvent, None]:
    print(f'end_node, state: {state}')
    yield RunFinishedEvent.new()


async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[SseEvent, None]:
    """
    主要的Agent响应函数
    """

    state = State(request=request, tool_calls=[])
    
    async for event in start_node(state):   
        yield event

    async for event in reason_node(state):
        yield event

    async for event in act_node(state):
        yield event
    
    async for event in end_node(state):
        yield event
        
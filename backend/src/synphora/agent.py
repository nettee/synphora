from typing import AsyncGenerator, TypedDict, List, Any
from pydantic import BaseModel
import uuid
from langchain_core.messages import SystemMessage, HumanMessage
from enum import Enum
from langgraph.graph import StateGraph, START, END

from synphora.sse import ( SseEvent, RunStartedEvent, RunFinishedEvent, TextMessageEvent )
from synphora.langgraph_sse import write_sse_event
from synphora.llm import create_llm_client
from synphora.tool import ArticleEvaluator

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




# LangGraph State Schema
class AgentState(TypedDict):
    request: AgentRequest
    tool_calls: List[Any]
    finished: bool


def start_node(state: AgentState) -> AgentState:
    """开始节点：发送运行开始事件"""
    print(f'start_node, state: {state}')
    
    write_sse_event(RunStartedEvent.new())
    
    return state


def reason_node(state: AgentState) -> AgentState:
    """推理节点：使用LLM决定调用哪个工具"""
    print(f'reason_node, state: {state}')
    
    tools = ArticleEvaluator.get_tools()
    llm = create_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    tool_decision_system_prompt = """
你是一个智能助手，可以使用工具来帮助用户处理文章相关的任务。
"""
    
    tool_decision_user_prompt = f"""
根据用户的请求，决定调用哪个工具来完成任务。

先输出你拥有的工具，然后输出你决定调用的工具。

注意：你无需考虑文章内容来自哪里，工具会自动获取文章内容。

用户请求：{state['request'].message}
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
            write_sse_event(TextMessageEvent.new(message_id=message_id, content=chunk.content))
        if chunk.tool_calls:
            tool_calls.extend(chunk.tool_calls)

    state['tool_calls'] = tool_calls
    return state


def act_node(state: AgentState) -> AgentState:
    """执行节点：执行工具并实时流式发送SSE事件"""
    print(f'act_node, state: {state}')

    tool_calls = state['tool_calls']
    if not tool_calls:
        raise ValueError("没有工具调用")

    tool_name = tool_calls[0]['name']
    
    if tool_name in ['evaluate_article']:
        # 调用类中的标准LangGraph工具函数，传入空的工具输入
        result = ArticleEvaluator.evaluate_article.invoke({})
        print(f"Tool execution result: {result}")
        
    else:
        # 未知工具，返回错误消息
        raise ValueError(f"未知工具: {tool_name}")

    return state


def end_node(state: AgentState) -> AgentState:
    """结束节点：发送运行完成事件"""
    print(f'end_node, state: {state}')
    
    write_sse_event(RunFinishedEvent.new())
    
    state['finished'] = True
    return state


def build_agent_graph() -> StateGraph:
    """构建LangGraph代理图"""
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("start", start_node)
    graph.add_node("reason", reason_node)
    graph.add_node("act", act_node)
    graph.add_node("end", end_node)
    
    # 连接节点
    graph.add_edge(START, "start")
    graph.add_edge("start", "reason")
    graph.add_edge("reason", "act")
    graph.add_edge("act", "end")
    graph.add_edge("end", END)
    
    return graph.compile()


async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[SseEvent, None]:
    """
    主要的Agent响应函数，使用LangGraph流式处理
    """
    
    graph = build_agent_graph()
    initial_state: AgentState = {
        "request": request,
        "tool_calls": [],
        "finished": False
    }
    
    # 使用LangGraph的流式处理，订阅custom事件来获取SSE事件
    async for kind, payload in graph.astream(
        initial_state,
        stream_mode=["custom"]
    ):
        if kind == "custom":
            # 处理自定义事件（SSE事件）
            channel = payload.get("channel")
            if channel == "sse":
                event = payload.get("event")
                if event:
                    yield event
        
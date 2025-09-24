from typing import AsyncGenerator, TypedDict, Annotated
from pydantic import BaseModel
import uuid
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from enum import Enum
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from synphora.sse import ( SseEvent, RunStartedEvent, RunFinishedEvent, TextMessageEvent )
from synphora.langgraph_sse import write_sse_event
from synphora.llm import create_llm_client
from synphora.tool import ArticleEvaluator
from synphora.artifact_manager import artifact_manager

import logging

# 设置日志
logger = logging.getLogger(__name__)

# 超时配置
AGENT_TIMEOUT_SECONDS = 30
TOOL_TIMEOUT_SECONDS = 60

class AgentRequest(BaseModel):
    message: str


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


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
    messages: Annotated[list, add_messages]


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

    # 使用分片归并：累积所有chunk，最后合并成完整AIMessage
    message_id = generate_id()
    
    # 用于归并的累加器
    accumulated_chunks = []
    
    for chunk in llm_with_tools.stream(state["messages"]):
        # 累积分片用于最终归并
        accumulated_chunks.append(chunk)
        
        # 流式输出文本内容到SSE
        if chunk.content:
            write_sse_event(TextMessageEvent.new(message_id=message_id, content=chunk.content))
    
    ai_message = merge_chunks(accumulated_chunks)
    
    return {"messages": [ai_message]}


def should_continue(state: AgentState) -> str:
    """决定是否继续循环的条件函数"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # 如果最后一条消息包含工具调用，则继续到act节点
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "act"
    # 否则结束
    else:
        return "end"


def merge_chunks(accumulated_chunks):
    # 使用LangChain的分片归并机制得到完整AIMessage
    # 这样可以正确处理tool_calls、ID等结构化信息
    final_message = None
    for chunk in accumulated_chunks:
        if final_message is None:
            final_message = chunk
        else:
            # 使用 + 运算符合并分片，这是LangChain推荐的方式
            final_message = final_message + chunk

    return final_message

def end_node(state: AgentState) -> AgentState:
    """结束节点：发送运行完成事件"""
    print(f'end_node, state: {state}')
    
    write_sse_event(RunFinishedEvent.new())
    
    return state


def build_agent_graph() -> StateGraph:
    """构建LangGraph代理图 - 标准 re-act 模式"""
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("start", start_node)
    graph.add_node("reason", reason_node)
    graph.add_node("act", ToolNode(ArticleEvaluator.get_tools()))
    graph.add_node("end", end_node)
    
    # 连接节点 - re-act 模式
    graph.add_edge(START, "start")
    graph.add_edge("start", "reason")
    
    # 从 reason 节点添加条件边，根据是否有工具调用决定下一步
    graph.add_conditional_edges(
        "reason",
        should_continue,
        {
            "act": "act",      # 如果有工具调用，执行工具
            "end": "end"       # 如果没有工具调用，结束
        }
    )
    
    # 从 act 节点返回到 reason 节点，形成循环
    graph.add_edge("act", "reason")
    graph.add_edge("end", END)
    
    return graph.compile()


async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[SseEvent, None]:
    """
    主要的Agent响应函数，使用LangGraph流式处理
    """
    
    graph = build_agent_graph()

    original_artifact = artifact_manager.get_original_artifact()

    system_prompt = """
你是 Synphora，一个智能写作助手。
"""
    
    user_prompt = f"""
## 任务描述

根据用户的请求，优先使用工具来完成任务。如果找不到合适的工具，请直接说明你无法完成任务。

## 注意事项

1. 请勿向用户透露「Artifact」「工具」等内部概念，会引起用户的疑惑。

- 正例：我将为你生成文章评价。
- 反例：根据您提供的 Artifact ID，我将使用评价工具来分析文章质量。
- 正例：评价结果已生成。
- 反例：评价结果已生成，Artifact ID 为：ae259520。

2. 工具的结果会通过 Artifact 的形式展示给用户，所以请勿赘述工具的结果，只需告诉用户结果已生成。

## 任务信息

用户文章原文的 Artifact ID: {original_artifact.id}

用户请求：{request.message}
"""

    initial_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    # 创建初始消息
    initial_state: AgentState = {
        "request": request,
        "messages": initial_messages,
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
        
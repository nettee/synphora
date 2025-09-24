import logging
import uuid
from collections.abc import AsyncGenerator
from enum import Enum
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from synphora.artifact_manager import artifact_manager
from synphora.langgraph_sse import write_sse_event
from synphora.llm import create_llm_client
from synphora.prompt import AgentPrompts
from synphora.sse import RunFinishedEvent, RunStartedEvent, SseEvent, TextMessageEvent
from synphora.tool import ArticleEvaluatorTool

# 设置日志
logger = logging.getLogger(__name__)

# 超时配置
AGENT_TIMEOUT_SECONDS = 30
TOOL_TIMEOUT_SECONDS = 60


class NodeType(str, Enum):
    """代理图节点类型"""

    FIRST = "start"
    REASON = "reason"
    ACT = "act"
    LAST = "end"


class AgentRequest(BaseModel):
    message: str


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


async def generate_text_message(
    content_parts: list[str],
) -> AsyncGenerator[SseEvent]:
    message_id = generate_id()

    for content in content_parts:
        yield TextMessageEvent.new(message_id=message_id, content=content)


async def generate_llm_message(messages) -> AsyncGenerator[SseEvent]:
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

    tools = ArticleEvaluatorTool.get_tools()
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
            write_sse_event(
                TextMessageEvent.new(message_id=message_id, content=chunk.content)
            )

    ai_message = merge_chunks(accumulated_chunks)

    return {"messages": [ai_message]}


def should_continue(state: AgentState) -> NodeType:
    """决定是否继续循环的条件函数"""
    messages = state["messages"]
    last_message = messages[-1]

    # 如果最后一条消息包含工具调用，则继续到act节点
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return NodeType.ACT
    # 否则结束
    else:
        return NodeType.LAST


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
    graph.add_node(NodeType.FIRST, start_node)
    graph.add_node(NodeType.REASON, reason_node)
    graph.add_node(NodeType.ACT, ToolNode(ArticleEvaluatorTool.get_tools()))
    graph.add_node(NodeType.LAST, end_node)

    # 连接节点 - re-act 模式
    graph.add_edge(START, NodeType.FIRST)
    graph.add_edge(NodeType.FIRST, NodeType.REASON)

    # 从 reason 节点添加条件边，根据是否有工具调用决定下一步
    graph.add_conditional_edges(
        NodeType.REASON,
        should_continue,
        {
            NodeType.ACT: NodeType.ACT,  # 如果有工具调用，执行工具
            NodeType.LAST: NodeType.LAST,  # 如果没有工具调用，结束
        },
    )

    # 从 act 节点返回到 reason 节点，形成循环
    graph.add_edge(NodeType.ACT, NodeType.REASON)
    graph.add_edge(NodeType.LAST, END)

    return graph.compile()


async def generate_agent_response(
    request: AgentRequest,
) -> AsyncGenerator[SseEvent]:
    """
    主要的Agent响应函数，使用LangGraph流式处理
    """

    graph = build_agent_graph()

    # 创建初始消息
    original_artifact = artifact_manager.get_original_artifact()
    agent_prompts = AgentPrompts()
    initial_messages = [
        SystemMessage(content=agent_prompts.system()),
        HumanMessage(
            content=agent_prompts.user(
                original_artifact_id=original_artifact.id, user_message=request.message
            )
        ),
    ]

    # 创建初始状态
    initial_state: AgentState = {
        "request": request,
        "messages": initial_messages,
    }

    # 使用LangGraph的流式处理，订阅custom事件来获取SSE事件
    async for kind, payload in graph.astream(initial_state, stream_mode=["custom"]):
        if kind == "custom":
            # 处理自定义事件（SSE事件）
            channel = payload.get("channel")
            if channel == "sse":
                event = payload.get("event")
                if event:
                    yield event

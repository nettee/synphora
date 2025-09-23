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

    # 使用分片归并：累积所有chunk，最后合并成完整AIMessage
    message_id = generate_id()
    
    # 用于归并的累加器
    accumulated_chunks = []
    
    for chunk in llm_with_tools.stream(tool_decision_messages):
        # 累积分片用于最终归并
        accumulated_chunks.append(chunk)
        
        # 流式输出文本内容到SSE
        if chunk.content:
            write_sse_event(TextMessageEvent.new(message_id=message_id, content=chunk.content))
    
    final_message = merge_chunks(accumulated_chunks)
    
    return {"messages": tool_decision_messages + [final_message]}


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
    """构建LangGraph代理图"""
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("start", start_node)
    graph.add_node("reason", reason_node)
    graph.add_node("act", ToolNode(ArticleEvaluator.get_tools()))  # 直接使用 ToolNode
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
    
    # 创建初始消息
    initial_state: AgentState = {
        "request": request,
        "messages": []
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
        
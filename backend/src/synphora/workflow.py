# 这里是一份标准 ReAct Agent 的实现，供参考

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from synphora.llm import create_llm_client
from synphora.tool import DemoTool


class State(TypedDict):
    user_input: str
    model_name: str
    messages: Annotated[list, add_messages]


def init_node(state: State) -> State:
    user_input = state["user_input"]

    return {
        "messages": [
            SystemMessage(
                content="你是一个专业的文章写作助手。对于用户的请求，如果有相关的工具，请调用工具，并直接返回工具的调用结果。如果没有相关的工具，请根据自己的知识回答。"
            ),
            HumanMessage(content=user_input),
        ],
    }


def reason_node(state: State) -> State:
    llm = create_llm_client()
    tools = DemoTool.get_tools()
    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke(state["messages"])

    return {
        "messages": [response],
    }


def reason_node_edges(state: State):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "act"
    else:
        return END


def build_graph():
    graph_builder = StateGraph(State)

    graph_builder.add_node("init", init_node)
    graph_builder.add_node("reason", reason_node)
    graph_builder.add_node("act", ToolNode(DemoTool.get_tools()))

    graph_builder.add_edge(START, "init")
    graph_builder.add_edge("init", "reason")
    graph_builder.add_conditional_edges("reason", reason_node_edges)
    graph_builder.add_edge("act", "reason")

    return graph_builder.compile()


graph = build_graph()


def run_workflow(user_input: str, model_name: str):
    input = State(user_input=user_input, model_name=model_name)

    for event in graph.stream(input):
        for value in event.values():
            last_message = value["messages"][-1]
            if not isinstance(last_message, AIMessage):
                continue
            if last_message.content:
                print(f"AI: {last_message.content}")
            if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
                for tool_call in last_message.tool_calls:
                    print(f'ToolCall({tool_call["name"]}, {tool_call["args"]})')


def main():
    run_workflow(
        "你好，评价下这篇文章，并且帮我撰写文章候选标题。文章内容：哈哈哈",
        "gpt-4o-mini",
    )


if __name__ == "__main__":
    main()

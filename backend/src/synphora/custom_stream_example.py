# run_graph.py
# ---------------------------------------------
# 需求点：
# - LangGraph ReAct 代理(create_react_agent)
# - 自定义「可流式」工具：在工具内部用 get_stream_writer() 连续发事件
# - 直接在控制台观察 graph.astream(...) 的输出效果（无前端）
# ---------------------------------------------

import asyncio
import json
import time
from typing import Any

from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from langgraph.prebuilt import create_react_agent

from synphora.llm import create_llm_client

load_dotenv()


# ---------- 1) 定义：会“流式输出”的工具 ----------
@tool
async def my_long_tool(task: str, steps: int = 6) -> str:
    """
    示例工具：分多步处理任务，并在处理过程中不断发送自定义事件（进度/分片）。
    真实场景可替换为：流式读写、大任务分片、外部 API 拉流、长计算等。
    """
    writer = get_stream_writer()  # 关键：拿到写入器，把事件写回到图的自定义流里
    for i in range(1, steps + 1):
        # 模拟耗时
        await asyncio.sleep(0.35)
        # 进度事件
        writer(
            {
                "channel": "tool",
                "tool": "my_long_tool",
                "type": "progress",
                "step": i,
                "total": steps,
                "progress": round(i / steps, 4),
                "message": f"[{i}/{steps}] 正在处理：{task}",
            }
        )
        # 分片数据（可选）
        writer(
            {
                "channel": "tool",
                "tool": "my_long_tool",
                "type": "chunk",
                "data": f"片段 {i}: {task}",
            }
        )

    writer(
        {
            "channel": "tool",
            "tool": "my_long_tool",
            "type": "done",
            "message": f"任务「{task}」完成。",
        }
    )
    return f"【工具完成】{task}（共 {steps} 步）"


# ---------- 2) 组装 ReAct 图 ----------
def build_graph():
    # 你可以把模型换成任意兼容的 LLM 适配器
    llm = create_llm_client()
    graph = create_react_agent(llm, tools=[my_long_tool])
    return graph


# ---------- 3) 打印辅助 ----------
def jdump(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(obj)


def hrule(title: str = "", ch: str = "─", width: int = 80) -> str:
    if not title:
        return ch * width
    prefix = f" {title} "
    rest = max(0, width - len(prefix))
    return prefix + (ch * rest)


# ---------- 4) 主逻辑：跑图并把流打印到控制台 ----------
async def run_once(prompt: str):
    graph = build_graph()
    t0 = time.time()
    print(hrule("RUN START"))
    print(f"User Prompt: {prompt}\n")

    # 关键：订阅两类流
    # - "custom": 我们在工具中用 get_stream_writer() 发出的自定义事件（进度/分片/日志等）
    # - "updates": 图的状态/消息更新（ReAct 过程），便于观察“reason→act→reason…”
    async for kind, payload in graph.astream(
        {"messages": [{"role": "user", "content": prompt}]},
        stream_mode=["custom", "updates"],
    ):
        if kind == "custom":
            # 你的工具自定义事件会走到这里
            etype = payload.get("type")
            if etype == "progress":
                step = payload.get("step")
                total = payload.get("total")
                prog = payload.get("progress")
                msg = payload.get("message", "")
                print(f"[tool] progress {step}/{total} ({prog:.2%}) - {msg}")
            elif etype == "chunk":
                print(f"[tool] chunk  -> {payload.get('data')}")
            else:
                print(f"[tool] custom -> {jdump(payload)}")

        elif kind == "updates":
            # 为了控制台友好，这里做一个“尽量人类可读”的摘要打印
            # 常见的内容：messages（新增的对话消息）、tool 调用结果等
            # 注意：不同版本/配置下结构可能略有不同，这里做了容错处理
            msg_list = payload.get("messages")
            if isinstance(msg_list, list) and msg_list:
                # 尝试只打印新增的最后一条消息的“role+content”
                last = msg_list[-1]
                role = last.get("role") or last.get("type") or "message"
                content = last.get("content") or last.get("text") or last
                # content 可能是对象/列表，这里统一转字符串
                if isinstance(content, (list, dict)):
                    content_str = jdump(content)
                else:
                    content_str = str(content)
                # 截断太长的输出（控制台更清晰）
                if len(content_str) > 800:
                    content_str = content_str[:800] + " ……(截断)"
                print(f"[updates] {role}: {content_str}\n")
            else:
                # 打印其它更新（如状态片段等）
                print(f"[updates] {jdump(payload)}\n")

    dt = time.time() - t0
    print(hrule(f"RUN END ({dt:.2f}s)"))
    print()


# ---------- 5) CLI ----------
if __name__ == "__main__":
    prompt = '调用工具 my_long_tool 完成任务，任务内容：测试任务'
    asyncio.run(run_once(prompt))

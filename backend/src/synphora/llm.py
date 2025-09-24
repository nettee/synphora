import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

# 加载 .env 文件
load_dotenv()


class LlmConfig(BaseModel):
    base_url: str
    api_key: SecretStr
    model: str


@lru_cache(maxsize=32)
def _get_llm_config() -> LlmConfig:
    return LlmConfig(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL"),
    )


def create_llm_client() -> ChatOpenAI:
    llm_config = _get_llm_config()

    return ChatOpenAI(
        base_url=llm_config.base_url,
        api_key=llm_config.api_key.get_secret_value(),
        model=llm_config.model,
    )


def create_llm_with_tools(tools: list[Tool]) -> ChatOpenAI:
    """创建绑定工具的LLM客户端"""
    llm_config = _get_llm_config()

    llm = ChatOpenAI(
        base_url=llm_config.base_url,
        api_key=llm_config.api_key.get_secret_value(),
        model=llm_config.model,
    )

    return llm.bind_tools(tools) if tools else llm


# 测试
if __name__ == "__main__":
    llm_client = create_llm_client()

    # 简单对话
    print(llm_client.invoke("Hello, how are you?"))

    # 流式对话
    for chunk in llm_client.stream("Hello, how are you?"):
        print(chunk.content, end="", flush=True)
    print()

    # 多轮对话
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Hello, how are you?"),
        AIMessage(content="I'm doing great, thank you!"),
        HumanMessage(content="What is the capital of France?"),
    ]
    print(llm_client.invoke(messages))

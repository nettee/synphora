from langchain_core.tools import tool
from langchain_core.tools import Tool
from typing import Callable, Awaitable, AsyncGenerator
from abc import ABC, abstractmethod
import uuid

from synphora.sse import (
    SseEvent, ArtifactContentStartEvent, ArtifactContentChunkEvent, 
    ArtifactContentCompleteEvent, ArtifactListUpdatedEvent
)
from synphora.llm import create_llm_client
from synphora.artifact_manager import artifact_manager
from synphora.models import ArtifactType, ArtifactRole, ArtifactData


class AsyncStreamingTool(ABC):
    """基础异步流式工具类，支持事件回调机制"""
    
    def __init__(self, event_callback: Callable[[SseEvent], Awaitable[None]] = None):
        self.event_callback = event_callback
    
    async def yield_event(self, event: SseEvent) -> None:
        """辅助方法：发送SSE事件到回调"""
        if self.event_callback:
            await self.event_callback(event)
    
    @abstractmethod
    async def execute(self, **kwargs) -> AsyncGenerator[SseEvent, None]:
        """执行工具逻辑并生成事件流"""
        pass


class DemoTool:

    @classmethod
    def get_tools(cls) -> list[Tool]:
        return [
            cls.comment_article,
            cls.analyze_article_position,
            cls.generate_article_title,
        ]

    @staticmethod
    @tool
    def comment_article() -> str:
        """评价这篇文章"""
        return "这篇文章很好"

    @staticmethod
    @tool
    def analyze_article_position() -> str:
        """分析这篇文章的定位"""
        return "这篇文章的定位很明确"

    @staticmethod
    @tool
    def generate_article_title() -> str:
        """生成文章标题"""
        return "给你一个标题：重新定义数字化转型"


class ArticleEvaluationTool(AsyncStreamingTool):
    """文章评价工具，支持流式生成评价内容"""
    
    def generate_id(self) -> str:
        return str(uuid.uuid4())[:8]
    
    async def execute(self) -> AsyncGenerator[SseEvent, None]:
        """执行文章评价并生成SSE事件流"""
        
        # 1. 发送ARTIFACT_CONTENT_START事件
        artifact_id = self.generate_id()
        artifact_title = "文章评价"
        
        yield ArtifactContentStartEvent.new(
            artifact_id=artifact_id,
            title=artifact_title,
            artifact_type=ArtifactType.COMMENT.value
        )
        
        # 2. 准备评价prompt
        original_artifact = artifact_manager.get_original_artifact()

        def format_artifact(artifact: ArtifactData) -> str:
            return f"""<file>
<name>{artifact.title}</name>
<content>{artifact.content}</content>
</file>"""
        
        article_content = format_artifact(original_artifact)

        system_prompt = """你是一位顶尖的内容分析师和资深编辑。"""
        
        user_prompt = f"""请帮我评价这篇文章。

## 评价步骤

严格遵循以下步骤，你的最终目标是让我清晰地了解这篇文章的综合质量、优势和潜在风险。 

### 第一步：读者画像分析 (Audience Inference) 

请首先通读全文，基于文章的选题、语言风格、使用的案例和探讨的深度，分析并描绘出这篇文章最有可能的核心目标读者是谁？ 请具体描述他们的特征（例如：年龄段、职业、兴趣点、当前可能面临的困惑或需求）。 

### 第二步：六大维度深度评估 (In-depth Evaluation) 

基于你在第一步中分析出的读者画像，请从以下六个维度逐一评估文章的质量。在每个维度下，请直接给出你的评判（例如：优秀、良好、一般、较弱），并详细说明理由。 

1. 核心论点清晰度： 

评判： 文章的核心论点（主旨）对目标读者来说，是清晰易懂还是模糊不清？其呈现方式是直击人心还是晦涩难懂？ 

2. 内容深度与原创性： 

评判： 文章提供的是独特的见解还是陈旧的观点？其内容的深度能否满足目标读者的求知欲，给他们带来"原来如此"的感觉？ 

3. 目标读者匹配度： 

评判： 文章整体（从语气到内容）与目标读者的"频道"是否一致？是否存在某些部分可能会让目标读者感到脱节或失去兴趣？ 

4. 情感共鸣： 

评判： 文章在调动目标读者情绪、引发其共鸣方面的表现如何？是能触动人心，还是仅仅停留在信息的冰冷传递？ 

5. 价值与启发性： 

评判： 读者读完后，能获得的实际价值或思想启发有多大？这个价值是否足够坚实，让读者感到不虚此行？ 

6. 传播潜力： 

评判： 这篇文章在目标读者群体中，自发传播的可能性有多大？是包含了强烈的社交货币（如新奇观点、强烈情绪、实用价值），还是缺乏分享的动力？请分析其关键的驱动或阻碍因素。 

### 第三步：综合结论 (Overall Verdict) 

最后，请综合以上所有分析，给我一个关于这篇文章整体质量的最终结论。并总结出它最大的一个优点和一个最需要警惕的缺点。

## 文章内容

{article_content}
        """
        
        # 3. 调用LLM并流式生成内容
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        llm = create_llm_client()
        llm_result_content = ''
        
        # 4. 流式发送ARTIFACT_CONTENT_CHUNK事件
        for chunk in llm.stream(messages):
            if chunk.content:
                yield ArtifactContentChunkEvent.new(
                    artifact_id=artifact_id, 
                    content=chunk.content
                )
                llm_result_content += chunk.content
        
        # 5. 发送ARTIFACT_CONTENT_COMPLETE事件
        yield ArtifactContentCompleteEvent.new(artifact_id=artifact_id)
        
        # 6. 创建artifact并发送ARTIFACT_LIST_UPDATED事件
        artifact = artifact_manager.create_artifact(
            title=artifact_title,
            content=llm_result_content,
            artifact_type=ArtifactType.COMMENT,
            role=ArtifactRole.ASSISTANT,
        )
        
        yield ArtifactListUpdatedEvent.new(
            artifact_id=artifact.id,
            title=artifact.title,
            artifact_type=artifact.type.value,
            role=artifact.role.value,
        )

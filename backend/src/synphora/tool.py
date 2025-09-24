import uuid

from langchain_core.tools import Tool, tool

from synphora.artifact_manager import artifact_manager
from synphora.prompt import get_article_evaluator_system_prompt, get_article_evaluator_user_prompt
from synphora.langgraph_sse import write_sse_event
from synphora.llm import create_llm_client
from synphora.models import ArtifactData, ArtifactRole, ArtifactType
from synphora.sse import (
    ArtifactContentChunkEvent,
    ArtifactContentCompleteEvent,
    ArtifactContentStartEvent,
    ArtifactListUpdatedEvent,
)


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())[:8]


class ArticleEvaluator:
    """文章评价工具类"""

    @classmethod
    def get_tools(cls) -> list[Tool]:
        return [
            cls.evaluate_article,
        ]

    @staticmethod
    @tool
    def evaluate_article(original_artifact_id: str) -> str:
        """
        评价这篇文章的质量，包括读者画像分析和六大维度评估

        Args:
            original_artifact_id: 原文 Artifact ID

        Returns:
            str: 评价结果的元数据
        """

        print(f'evaluate_article, original_artifact_id: {original_artifact_id}')

        # 1. 发送ARTIFACT_CONTENT_START事件
        generated_artifact_id = artifact_manager.generate_artifact_id()
        artifact_title = "文章评价"

        write_sse_event(
            ArtifactContentStartEvent.new(
                artifact_id=generated_artifact_id,
                title=artifact_title,
                artifact_type=ArtifactType.COMMENT.value,
            )
        )

        # 2. 准备评价prompt
        original_artifact = artifact_manager.get_artifact(original_artifact_id)

        def format_artifact(artifact: ArtifactData) -> str:
            return f"""<file>
<name>{artifact.title}</name>
<content>{artifact.content}</content>
</file>"""

        article_content = format_artifact(original_artifact)

        system_prompt = get_article_evaluator_system_prompt()
        user_prompt = get_article_evaluator_user_prompt(article_content=article_content)

        # 3. 调用LLM并流式生成内容
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        llm = create_llm_client()
        llm_result_content = ''

        # 4. 流式发送ARTIFACT_CONTENT_CHUNK事件 - 实时流式处理
        for chunk in llm.stream(messages):
            if chunk.content:
                write_sse_event(
                    ArtifactContentChunkEvent.new(
                        artifact_id=generated_artifact_id, content=chunk.content
                    )
                )
                llm_result_content += chunk.content

        # 5. 发送ARTIFACT_CONTENT_COMPLETE事件
        write_sse_event(
            ArtifactContentCompleteEvent.new(artifact_id=generated_artifact_id)
        )

        # 6. 创建artifact并发送ARTIFACT_LIST_UPDATED事件
        # 保证artifact_id与生成的一致，避免前端显示错误
        artifact = artifact_manager.create_artifact_with_id(
            artifact_id=generated_artifact_id,
            title=artifact_title,
            content=llm_result_content,
            artifact_type=ArtifactType.COMMENT,
            role=ArtifactRole.ASSISTANT,
        )

        write_sse_event(
            ArtifactListUpdatedEvent.new(
                artifact_id=artifact.id,
                title=artifact.title,
                artifact_type=artifact.type.value,
                role=artifact.role.value,
            )
        )

        return f"【工具完成】文章评价（artifact_id: {artifact.id}）"

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import Tool, tool

from synphora.artifact_manager import artifact_manager
from synphora.langgraph_sse import write_sse_event
from synphora.llm import create_llm_client
from synphora.models import ArtifactRole, ArtifactType, EvaluateType
from synphora.prompt import ArticleEvaluatorPrompts
from synphora.sse import (
    ArtifactContentChunkEvent,
    ArtifactContentCompleteEvent,
    ArtifactContentStartEvent,
    ArtifactListUpdatedEvent,
)


class ArticleEvaluator:
    def __init__(self, evaluate_type: EvaluateType):
        self.evaluate_type = evaluate_type

    def evaluate(self, original_artifact_id: str) -> str:
        print(
            f'evaluate_article, evaluate_type: {self.evaluate_type}, original_artifact_id: {original_artifact_id}'
        )

        if self.evaluate_type == EvaluateType.COMMENT:
            artifact_title = "文章评价"
            artifact_type = ArtifactType.COMMENT
        elif self.evaluate_type == EvaluateType.TITLE:
            artifact_title = "候选标题"
            artifact_type = ArtifactType.COMMENT
        elif self.evaluate_type == EvaluateType.INTRODUCTION:
            artifact_title = "介绍语"
            artifact_type = ArtifactType.COMMENT
        else:
            raise ValueError(f'Unsupported evaluate type: {self.evaluate_type}')

        article_evaluator_prompts = ArticleEvaluatorPrompts()
        original_artifact = artifact_manager.get_artifact(original_artifact_id)
        system_prompt = article_evaluator_prompts.system()
        user_prompt = article_evaluator_prompts.user(
            type=self.evaluate_type, artifact=original_artifact
        )

        # 1. 发送ARTIFACT_CONTENT_START事件
        generated_artifact_id = artifact_manager.generate_artifact_id()

        write_sse_event(
            ArtifactContentStartEvent.new(
                artifact_id=generated_artifact_id,
                title=artifact_title,
                artifact_type=artifact_type.value,
            )
        )

        # 2. 准备评价prompt
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # 3. 调用LLM并流式生成内容
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
            artifact_type=artifact_type,
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

        return json.dumps(
            {
                "evaluate_type": self.evaluate_type.value,
                "artifact_id": artifact.id,
                "title": artifact.title,
            }
        )


class ArticleEvaluatorTool:
    """文章评价工具类"""

    @classmethod
    def get_tools(cls) -> list[Tool]:
        return [
            cls.write_comment,
            cls.write_candidate_titles,
            cls.write_introduction,
        ]

    @staticmethod
    @tool
    def write_comment(original_artifact_id: str) -> str:
        """
        评价这篇文章的质量，包括读者画像分析和六大维度评估

        Args:
            original_artifact_id: 原文 Artifact ID

        Returns:
            str: 评价结果的元数据
        """
        evaluator = ArticleEvaluator(EvaluateType.COMMENT)
        result = evaluator.evaluate(original_artifact_id)
        print(f'tool call finished, tool name: write_comment, result: {result}')
        return result

    @staticmethod
    @tool
    def write_candidate_titles(original_artifact_id: str) -> str:
        """
        根据文章内容，撰写三个候选标题

        Args:
            original_artifact_id: 原文 Artifact ID

        Returns:
            str: 候选标题的元数据
        """
        evaluator = ArticleEvaluator(EvaluateType.TITLE)
        result = evaluator.evaluate(original_artifact_id)
        print(
            f'tool call finished, tool name: write_candidate_titles, result: {result}'
        )
        return result

    @staticmethod
    @tool
    def write_introduction(original_artifact_id: str) -> str:
        """
        根据文章内容，撰写一篇介绍语
        Args:
            original_artifact_id: 原文 Artifact ID

        Returns:
            str: 介绍语的元数据
        """
        evaluator = ArticleEvaluator(EvaluateType.INTRODUCTION)
        result = evaluator.evaluate(original_artifact_id)
        print(f'tool call finished, tool name: write_introduction, result: {result}')
        return result

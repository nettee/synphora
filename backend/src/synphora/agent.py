from typing import AsyncGenerator
from pydantic import BaseModel
import uuid
from langchain_core.messages import SystemMessage, HumanMessage
from enum import Enum

from synphora.sse import (
    SseEvent, RunStartedEvent, RunFinishedEvent, TextMessageEvent, 
    ArtifactListUpdatedEvent, ArtifactContentStartEvent, 
    ArtifactContentChunkEvent, ArtifactContentCompleteEvent
)
from synphora.llm import create_llm_client
from synphora.models import ArtifactData, ArtifactType, ArtifactRole
from synphora.artifact_manager import artifact_manager

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


async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[SseEvent, None]:

    yield RunStartedEvent.new()

    system_prompt = """
    你是一个专业的文章写作助手。
    """

    original_artifact = artifact_manager.get_original_artifact()

    def format_artifact(artifact: ArtifactData) -> str:
        return f"""<file>
          <name>{artifact.title}</name>
          <content>{artifact.content}</content>
        </file>"""

    # Determine artifact title and confirmation message based on request type
    artifact_title = "文章评价"
    confirmation_message = "我将为你生成文章评价"
    
    if request.message == Suggestions.EVALUATE_ARTICLE.value:
        system_prompt = """你是一位顶尖的内容分析师和资深编辑。"""
        artifact_title = "文章评价"
        confirmation_message = "我将为你生成文章评价"

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

用户附加的文件内容：
{format_artifact(original_artifact)}
        """

    elif request.message == Suggestions.ANALYZE_ARTICLE_POSITION.value:
        artifact_title = "文章定位分析"
        confirmation_message = "我将为你分析文章定位"
        user_prompt = f"""请帮助用户分析这篇文章的定位。

        用户附加的文件内容：
        {format_artifact(original_artifact)}
        """

    elif request.message == Suggestions.WRITE_CANDIDATE_TITLES.value:
        artifact_title = "候选标题"
        confirmation_message = "我将为你撰写候选标题"
        user_prompt = f"""请帮助用户为文章撰写 5 个候选标题，并说明每个标题的优缺点。

        用户附加的文件内容：
        {format_artifact(original_artifact)}
        """

    else:
        user_prompt = request.message

    # Step 1: Send confirmation message to chat
    confirmation_message_id = generate_id()
    yield TextMessageEvent.new(message_id=confirmation_message_id, content=confirmation_message)

    # Step 2: Start artifact content streaming
    artifact_id = generate_id()
    yield ArtifactContentStartEvent.new(
        artifact_id=artifact_id,
        title=artifact_title,
        artifact_type=ArtifactType.COMMENT.value
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    llm = create_llm_client()
    print(f'llm request, messages: {messages}')
    llm_result_content = ''
    
    # Step 3: Stream artifact content in chunks
    for chunk in llm.stream(messages):
        if chunk.content:
            yield ArtifactContentChunkEvent.new(artifact_id=artifact_id, content=chunk.content)
            llm_result_content += chunk.content

    # Step 4: Complete artifact content streaming
    yield ArtifactContentCompleteEvent.new(artifact_id=artifact_id)

    # Step 5: Create the artifact in storage and notify frontend
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

    yield RunFinishedEvent.new()

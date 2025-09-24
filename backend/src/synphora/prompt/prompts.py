from synphora.models import ArtifactData, EvaluateType

from .renderer import renderer


class AgentPrompts:
    def system(self) -> str:
        return renderer.render("agent-system-prompt.md")

    def user(self, original_artifact_id: str, user_message: str) -> str:
        return renderer.render(
            "agent-user-prompt.md",
            original_artifact_id=original_artifact_id,
            user_message=user_message,
        )


class ArticleEvaluatorPrompts:
    def system(self) -> str:
        return renderer.render("article-evaluator-system-prompt.md")

    def user(self, type: EvaluateType, artifact: ArtifactData) -> str:
        file_name = f"article-evaluator-{type.value.lower()}-prompt.md"
        return renderer.render(file_name, artifact=artifact)

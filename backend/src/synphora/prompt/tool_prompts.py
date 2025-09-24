from .renderer import renderer


def get_article_evaluator_system_prompt() -> str:
    """Get the article evaluator system prompt from template file."""
    return renderer.render("article_evaluator_system")


def get_article_evaluator_user_prompt(article_content: str) -> str:
    """Get the article evaluator user prompt with rendered variables from template file."""
    return renderer.render("article_evaluator_user", article_content=article_content)
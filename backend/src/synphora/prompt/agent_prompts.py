from .renderer import renderer


def get_system_prompt() -> str:
    """Get the system prompt from template file."""
    return renderer.render("system")


def get_user_prompt(original_artifact_id: str, user_message: str) -> str:
    """Get the user prompt with rendered variables from template file."""
    return renderer.render("user", 
                          original_artifact_id=original_artifact_id,
                          user_message=user_message)
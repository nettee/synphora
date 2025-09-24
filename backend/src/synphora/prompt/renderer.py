from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptRenderer:
    """Jinja2-based prompt template renderer that loads templates from files."""

    def __init__(self, template_dir: str | Path = None):
        if template_dir is None:
            # Default to templates directory relative to this file
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = Path(template_dir)
        self.env = None
        self._setup()

    def _setup(self):
        """Setup the Jinja2 environment with file system loader."""
        if not self.template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {self.template_dir}"
            )

        loader = FileSystemLoader(str(self.template_dir))
        self.env = Environment(
            loader=loader,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, **kwargs) -> str:
        """Render a template with the given context."""
        if self.env is None:
            raise RuntimeError("PromptRenderer not initialized properly.")

        # Add .md extension if not present
        if not template_name.endswith('.md'):
            template_name += '.md'

        template = self.env.get_template(template_name)
        return template.render(**kwargs)


# Global renderer instance
renderer = PromptRenderer()

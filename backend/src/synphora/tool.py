from langchain_core.tools import tool
from langchain_core.tools import Tool


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
        """评论这篇文章"""
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

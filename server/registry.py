"""
Central Registry for MCP Primitives
Consolidates all resources, prompts, and tools to avoid code duplication
"""
from typing import Any, Optional
from server.resources.book_catalog import get_book_catalog, list_catalog_resource
from server.resources.reading_stats import get_reading_stats, list_stats_resource
from server.prompts.prompt_templates import (
    get_recommend_books_prompt,
    get_reading_progress_prompt,
    get_book_review_prompt,
    list_prompts as list_prompt_metadata
)
from server.tools.library_tools import search_books, add_to_reading_list, list_tools as list_tool_metadata


class MCPRegistry:
    """
    Central registry for all MCP primitives.
    Both STDIO and HTTP servers use this to avoid duplication.
    """

    @staticmethod
    def list_resources() -> list[dict[str, Any]]:
        """List all available resources."""
        return [
            list_catalog_resource(),
            list_stats_resource()
        ]

    @staticmethod
    def read_resource(uri: str) -> dict[str, Any]:
        """Read a specific resource by URI."""
        if uri == "library://books/catalog":
            return get_book_catalog()
        elif uri == "library://user/reading-stats":
            return get_reading_stats()
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    @staticmethod
    def list_prompts() -> list[dict[str, Any]]:
        """List all available prompts."""
        return list_prompt_metadata()

    @staticmethod
    def get_prompt(name: str, arguments: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Get a specific prompt by name with optional arguments."""
        arguments = arguments or {}

        if name == "recommend_books":
            return get_recommend_books_prompt(
                genre=arguments.get("genre"),
                mood=arguments.get("mood")
            )
        elif name == "reading_progress_report":
            return get_reading_progress_prompt()
        elif name == "create_book_review":
            book_id = arguments.get("book_id")
            if not book_id:
                raise ValueError("book_id argument is required for create_book_review prompt")
            return get_book_review_prompt(book_id)
        else:
            raise ValueError(f"Unknown prompt: {name}")

    @staticmethod
    def list_tools() -> list[dict[str, Any]]:
        """List all available tools."""
        return list_tool_metadata()

    @staticmethod
    def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a specific tool by name with arguments."""
        if name == "search_books":
            return search_books(
                query=arguments["query"],
                genre=arguments.get("genre"),
                min_rating=arguments.get("min_rating")
            )
        elif name == "add_to_reading_list":
            return add_to_reading_list(book_id=arguments["book_id"])
        else:
            raise ValueError(f"Unknown tool: {name}")

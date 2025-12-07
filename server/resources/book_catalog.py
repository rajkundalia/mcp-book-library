"""
Book Catalog Resource
Demonstrates MCP Resources - structured data that can be read by LLMs
"""
import json
from pathlib import Path
from typing import Any


# Resource: Provides static/dynamic data to LLMs
# Use case: When you want the LLM to access structured information
def get_book_catalog() -> dict[str, Any]:
    """
    Load and return the book catalog.
    This is an MCP Resource - it provides structured data that LLMs can read.
    """
    data_path = Path(__file__).parent.parent / "data" / "books.json"
    with open(data_path, 'r') as f:
        return {
            "uri": "library://books/catalog",
            "mimeType": "application/json",
            "text": f.read()
        }


def list_catalog_resource() -> dict[str, Any]:
    """Return metadata about the book catalog resource."""
    return {
        "uri": "library://books/catalog",
        "name": "Book Catalog",
        "description": "Complete catalog of available books with metadata including title, author, genre, and ratings",
        "mimeType": "application/json"
    }

"""
Library Tools
Demonstrates MCP Tools - executable functions that perform actions
"""
import json
from pathlib import Path
from typing import Any, Optional


# Tools: Executable functions that perform actions and return results
# Use case: When the LLM needs to DO something (search, modify data, call APIs)

def search_books(query: str, genre: Optional[str] = None, min_rating: Optional[float] = None) -> dict[str, Any]:
    """
    Search for books in the catalog.
    This Tool performs a search operation and returns results.

    Args:
        query: Search term to match in title, author, or summary
        genre: Optional genre filter
        min_rating: Optional minimum rating filter
    """
    data_path = Path(__file__).parent.parent / "data" / "books.json"

    with open(data_path, 'r') as f:
        books = json.load(f)

    # Case-insensitive search
    query_lower = query.lower()
    results = []

    for book in books:
        # Check if query matches title, author, or summary
        matches_query = (
                query_lower in book["title"].lower() or
                query_lower in book["author"].lower() or
                query_lower in book["summary"].lower()
        )

        # Apply filters
        if matches_query:
            if genre and book["genre"].lower() != genre.lower():
                continue
            if min_rating and book["rating"] < min_rating:
                continue
            results.append(book)

    # Limit to 10 results
    results = results[:10]

    return {
        "success": True,
        "count": len(results),
        "results": results,
        "query": query,
        "filters": {
            "genre": genre,
            "min_rating": min_rating
        }
    }


def add_to_reading_list(book_id: str) -> dict[str, Any]:
    """
    Add a book to the user's reading list.
    This Tool modifies persistent data on disk.

    Args:
        book_id: ID of the book to add to reading list
    """
    data_dir = Path(__file__).parent.parent / "data"
    books_path = data_dir / "books.json"
    reading_list_path = data_dir / "reading_list.json"

    # Validate book exists
    with open(books_path, 'r') as f:
        books = json.load(f)

    book_exists = any(b["id"] == book_id for b in books)

    if not book_exists:
        return {
            "success": False,
            "error": f"Book with id '{book_id}' not found in catalog",
            "book_id": book_id
        }

    # Load current reading list
    with open(reading_list_path, 'r') as f:
        reading_data = json.load(f)

    # Check if already in list
    if book_id in reading_data["reading_list"]:
        return {
            "success": False,
            "error": f"Book '{book_id}' is already in your reading list",
            "book_id": book_id,
            "reading_list": reading_data["reading_list"]
        }

    # Add to list
    reading_data["reading_list"].append(book_id)

    # Persist to disk
    with open(reading_list_path, 'w') as f:
        json.dump(reading_data, f, indent=2)

    return {
        "success": True,
        "message": f"Book '{book_id}' added to reading list",
        "book_id": book_id,
        "reading_list": reading_data["reading_list"]
    }


def list_tools() -> list[dict[str, Any]]:
    """Return metadata for all available tools."""
    return [
        {
            "name": "search_books",
            "description": "Search for books in the catalog by title, author, or content. Supports filtering by genre and minimum rating.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to match in title, author, or summary"
                    },
                    "genre": {
                        "type": "string",
                        "description": "Optional genre filter (e.g., 'Science Fiction', 'Fantasy')"
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Optional minimum rating filter (0-5)"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "add_to_reading_list",
            "description": "Add a book to your reading list by its ID. The book must exist in the catalog.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "ID of the book to add (e.g., 'dune', '1984')"
                    }
                },
                "required": ["book_id"]
            }
        }
    ]

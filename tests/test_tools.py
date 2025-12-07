"""
Tests for MCP Tools
Verifies that tools execute correctly and persist data
"""
import json
from pathlib import Path

from server.tools.library_tools import search_books, add_to_reading_list, list_tools


def test_search_books_basic():
    """Test basic book search."""
    result = search_books("science")

    assert result["success"] is True
    assert result["count"] > 0
    assert "results" in result

    # Should find Dune
    book_ids = [b["id"] for b in result["results"]]
    assert "dune" in book_ids


def test_search_books_with_genre():
    """Test search with genre filter."""
    result = search_books("fiction", genre="Science Fiction")

    assert result["success"] is True
    for book in result["results"]:
        assert book["genre"] == "Science Fiction"


def test_search_books_with_rating():
    """Test search with minimum rating filter."""
    result = search_books("book", min_rating=4.5)

    assert result["success"] is True
    for book in result["results"]:
        assert book["rating"] >= 4.5


def test_search_books_no_results():
    """Test search that returns no results."""
    result = search_books("xyzabc123nonexistent")

    assert result["success"] is True
    assert result["count"] == 0
    assert len(result["results"]) == 0


def test_search_books_case_insensitive():
    """Test that search is case insensitive."""
    result1 = search_books("DUNE")
    result2 = search_books("dune")

    assert result1["count"] == result2["count"]


def test_search_books_max_results():
    """Test that search limits to 10 results."""
    result = search_books("a")  # Common letter should match many books

    assert len(result["results"]) <= 10


def test_add_to_reading_list_success():
    """Test successfully adding a book to reading list."""
    # First, read current list
    data_path = Path("server/data/reading_list.json")
    with open(data_path, 'r') as f:
        original_data = json.load(f)
    original_list = original_data["reading_list"].copy()

    try:
        # Add a new book
        result = add_to_reading_list("hobbit")

        assert result["success"] is True
        assert "hobbit" in result["reading_list"]

        # Verify it was actually written to file
        with open(data_path, 'r') as f:
            updated_data = json.load(f)

        assert "hobbit" in updated_data["reading_list"]

    finally:
        # Restore original state
        original_data["reading_list"] = original_list
        with open(data_path, 'w') as f:
            json.dump(original_data, f, indent=2)


def test_add_to_reading_list_invalid_book():
    """Test adding a non-existent book."""
    result = add_to_reading_list("nonexistent-book-id")

    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_add_to_reading_list_duplicate():
    """Test adding a book that's already in the list."""
    # Add dune (which is already in the default list)
    result = add_to_reading_list("dune")

    assert result["success"] is False
    assert "already" in result["error"].lower()


def test_list_tools_metadata():
    """Test that tool metadata is correct."""
    tools = list_tools()

    assert len(tools) == 2
    tool_names = [t["name"] for t in tools]

    assert "search_books" in tool_names
    assert "add_to_reading_list" in tool_names

    # Check input schemas
    search_tool = next(t for t in tools if t["name"] == "search_books")
    assert "query" in search_tool["inputSchema"]["properties"]
    assert "query" in search_tool["inputSchema"]["required"]

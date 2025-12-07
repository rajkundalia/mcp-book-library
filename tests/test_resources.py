"""
Tests for MCP Resources
Verifies that resources return correct data structure and content
"""
import json

from server.resources.book_catalog import get_book_catalog, list_catalog_resource
from server.resources.reading_stats import get_reading_stats, list_stats_resource


def test_book_catalog_structure():
    """Test that book catalog has correct structure."""
    catalog = get_book_catalog()

    assert catalog["uri"] == "library://books/catalog"
    assert catalog["mimeType"] == "application/json"
    assert "text" in catalog

    # Parse JSON content
    books = json.loads(catalog["text"])
    assert isinstance(books, list)
    assert len(books) >= 10  # Should have at least 10 books

    # Check first book structure
    book = books[0]
    required_fields = ["id", "title", "author", "year", "genre", "pages", "rating", "summary"]
    for field in required_fields:
        assert field in book, f"Book missing required field: {field}"


def test_book_catalog_content():
    """Test that specific books are in the catalog."""
    catalog = get_book_catalog()
    books = json.loads(catalog["text"])

    book_ids = [b["id"] for b in books]
    assert "dune" in book_ids
    assert "1984" in book_ids

    # Find Dune and check details
    dune = next(b for b in books if b["id"] == "dune")
    assert dune["title"] == "Dune"
    assert dune["author"] == "Frank Herbert"
    assert dune["year"] == 1965


def test_reading_stats_structure():
    """Test that reading stats have correct structure."""
    stats = get_reading_stats()

    assert stats["uri"] == "library://user/reading-stats"
    assert stats["mimeType"] == "application/json"

    # Parse JSON content
    data = json.loads(stats["text"])

    required_fields = [
        "total_books_read",
        "current_year_count",
        "favorite_genres",
        "reading_list",
        "recently_read",
        "reading_goal"
    ]

    for field in required_fields:
        assert field in data, f"Stats missing required field: {field}"

    # Check reading_goal structure
    assert "yearly_target" in data["reading_goal"]
    assert "current_progress" in data["reading_goal"]


def test_resource_metadata():
    """Test that resource metadata is correct."""
    catalog_meta = list_catalog_resource()
    assert catalog_meta["uri"] == "library://books/catalog"
    assert "description" in catalog_meta

    stats_meta = list_stats_resource()
    assert stats_meta["uri"] == "library://user/reading-stats"
    assert "description" in stats_meta

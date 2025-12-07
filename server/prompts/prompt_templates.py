"""
Prompt Templates
Demonstrates MCP Prompts - pre-built instruction templates that inject resource data
"""
import json
from typing import Any, Optional
from pathlib import Path


# Prompts: Structured templates that combine instructions with resource data
# Use case: Guide LLMs with specific tasks using real-time data

def get_recommend_books_prompt(genre: Optional[str] = None, mood: Optional[str] = None) -> dict[str, Any]:
    """
    Generate book recommendation prompt with live data.
    This Prompt fetches Resources internally before returning the template.
    """
    # Load resources to inject into the prompt
    data_dir = Path(__file__).parent.parent / "data"

    with open(data_dir / "reading_list.json", 'r') as f:
        reading_stats = json.load(f)

    with open(data_dir / "books.json", 'r') as f:
        book_catalog = json.load(f)

    # Build the prompt template with injected data
    template = f"""You are a knowledgeable librarian. Based on the user's reading history and preferences, recommend 3 books from the catalog.

Reading Stats: {json.dumps(reading_stats, indent=2)}

Book Catalog: {json.dumps(book_catalog, indent=2)}

User preferences:
Genre: {genre or "any"}
Mood: {mood or "any"}

Provide:
1. Three specific book recommendations
2. Brief explanation why each book fits
3. Note any books they've already read"""

    return {
        "name": "recommend_books",
        "description": "Generate personalized book recommendations",
        "arguments": [
            {"name": "genre", "description": "Preferred genre", "required": False},
            {"name": "mood", "description": "Current mood or reading preference", "required": False}
        ],
        "prompt": template
    }


def get_reading_progress_prompt() -> dict[str, Any]:
    """
    Generate reading progress report prompt.
    Fetches current stats and creates motivational report template.
    """
    data_dir = Path(__file__).parent.parent / "data"

    with open(data_dir / "reading_list.json", 'r') as f:
        reading_stats = json.load(f)

    template = f"""Generate a comprehensive reading progress report for the user.

Reading Stats: {json.dumps(reading_stats, indent=2)}

Include:
- Total books read this year vs goal
- Goal percentage and remaining books needed
- Favorite genres analysis
- A personalized motivational message
- Suggestions to reach their yearly goal"""

    return {
        "name": "reading_progress_report",
        "description": "Generate a summary of reading progress toward goals",
        "arguments": [],
        "prompt": template
    }


def get_book_review_prompt(book_id: str) -> dict[str, Any]:
    """
    Create a structured book review template for a specific book.
    Looks up the book details and provides a review framework.
    """
    data_dir = Path(__file__).parent.parent / "data"

    with open(data_dir / "books.json", 'r') as f:
        book_catalog = json.load(f)

    # Find the specific book
    book = next((b for b in book_catalog if b["id"] == book_id), None)

    if not book:
        raise ValueError(f"Book with id '{book_id}' not found")

    template = f"""Help the user write a structured review for: {book['title']} by {book['author']}

Book Details: {json.dumps(book, indent=2)}

Guide them through writing a review with these sections:

1. Overall Impression (1-5 stars and one sentence summary)
2. Plot Summary (2-3 sentences, NO SPOILERS)
3. What Worked (themes, characters, writing style)
4. What Didn't Work (constructive criticism)
5. Recommendation (who would enjoy this book?)

Keep the tone thoughtful and balanced."""

    return {
        "name": "create_book_review",
        "description": "Template for writing a structured book review",
        "arguments": [
            {"name": "book_id", "description": "ID of the book to review", "required": True}
        ],
        "prompt": template
    }


def list_prompts() -> list[dict[str, Any]]:
    """Return metadata for all available prompts."""
    return [
        {
            "name": "recommend_books",
            "description": "Generate personalized book recommendations based on user preferences",
            "arguments": [
                {"name": "genre", "description": "Preferred genre", "required": False},
                {"name": "mood", "description": "Current mood or reading preference", "required": False}
            ]
        },
        {
            "name": "reading_progress_report",
            "description": "Generate a summary of reading progress toward yearly goals",
            "arguments": []
        },
        {
            "name": "create_book_review",
            "description": "Template for writing a structured book review for a specific book",
            "arguments": [
                {"name": "book_id", "description": "ID of the book to review", "required": True}
            ]
        }
    ]
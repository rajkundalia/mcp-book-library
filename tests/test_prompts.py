"""
Tests for MCP Prompts
Verifies that prompts render correctly with data injection
"""
import pytest

from server.prompts.prompt_templates import (
    get_recommend_books_prompt,
    get_reading_progress_prompt,
    get_book_review_prompt,
    list_prompts
)


def test_recommend_books_prompt():
    """Test book recommendation prompt generation."""
    prompt = get_recommend_books_prompt(genre="Fantasy", mood="epic")

    assert prompt["name"] == "recommend_books"
    assert "prompt" in prompt

    # Check that data is injected
    prompt_text = prompt["prompt"]
    assert "Reading Stats:" in prompt_text
    assert "Book Catalog:" in prompt_text
    assert "Genre: Fantasy" in prompt_text
    assert "Mood: epic" in prompt_text


def test_recommend_books_prompt_defaults():
    """Test recommendation prompt with no arguments."""
    prompt = get_recommend_books_prompt()

    prompt_text = prompt["prompt"]
    assert "Genre: any" in prompt_text
    assert "Mood: any" in prompt_text


def test_reading_progress_prompt():
    """Test reading progress report prompt."""
    prompt = get_reading_progress_prompt()

    assert prompt["name"] == "reading_progress_report"
    prompt_text = prompt["prompt"]

    # Should contain stats data
    assert "Reading Stats:" in prompt_text
    assert "reading_goal" in prompt_text.lower() or "goal" in prompt_text.lower()


def test_book_review_prompt():
    """Test book review template prompt."""
    prompt = get_book_review_prompt("dune")

    assert prompt["name"] == "create_book_review"
    prompt_text = prompt["prompt"]

    # Should contain book details
    assert "Dune" in prompt_text
    assert "Frank Herbert" in prompt_text
    assert "Book Details:" in prompt_text


def test_book_review_prompt_invalid_id():
    """Test that invalid book ID raises error."""
    with pytest.raises(ValueError, match="not found"):
        get_book_review_prompt("nonexistent-book")


def test_list_prompts_metadata():
    """Test that prompt metadata is correct."""
    prompts = list_prompts()

    assert len(prompts) == 3
    prompt_names = [p["name"] for p in prompts]

    assert "recommend_books" in prompt_names
    assert "reading_progress_report" in prompt_names
    assert "create_book_review" in prompt_names

    # Check that arguments are documented
    recommend = next(p for p in prompts if p["name"] == "recommend_books")
    assert len(recommend["arguments"]) == 2

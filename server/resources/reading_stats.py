"""
Reading Statistics Resource
Demonstrates user-specific data resources
"""
import json
from pathlib import Path
from typing import Any


def get_reading_stats() -> dict[str, Any]:
    """
    Load and return user's reading statistics.
    This Resource tracks user progress and preferences.
    """
    data_path = Path(__file__).parent.parent / "data" / "reading_list.json"
    with open(data_path, 'r') as f:
        return {
            "uri": "library://user/reading-stats",
            "mimeType": "application/json",
            "text": f.read()
        }


def list_stats_resource() -> dict[str, Any]:
    """Return metadata about the reading stats resource."""
    return {
        "uri": "library://user/reading-stats",
        "name": "Reading Statistics",
        "description": "User's reading history, progress, and statistics including goals and favorite genres",
        "mimeType": "application/json"
    }

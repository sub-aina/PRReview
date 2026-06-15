import pytest
from unittest.mock import patch, MagicMock


# ── build_prompt ─────────────────────────────────────────────────────────────

def test_build_prompt_includes_diff_and_context():
    from reviewer import build_prompt

    diff = "- old line\n+ new line"
    context = [
        {"filepath": "auth.py", "content": "def login(): pass"}
    ]

    prompt = build_prompt(diff, context)

    assert "- old line" in prompt
    assert "+ new line" in prompt
    assert "auth.py" in prompt
    assert "def login(): pass" in prompt


def test_build_prompt_handles_empty_context():
    from reviewer import build_prompt

    prompt = build_prompt("some diff", [])

    assert "some diff" in prompt
    # No crash, context section just empty
    assert "PULL REQUEST DIFF" in prompt


# ── review_pr ────────────────────────────────────────────────────────────────

def test_review_pr_returns_string():
    """Mock Groq + ChromaDB — verify review_pr returns a non-empty string."""

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "1. Missing error handling in line 5."

    with patch("reviewer.search_codebase", return_value=[]) as mock_search, \
         patch("reviewer.client.chat.completions.create", return_value=mock_response):

        from reviewer import review_pr
        result = review_pr("some diff text")

    assert isinstance(result, str)
    assert len(result) > 0
    mock_search.assert_called_once()


def test_review_pr_passes_diff_to_search():
    """Diff should be used as the ChromaDB search query."""

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "All good."

    with patch("reviewer.search_codebase", return_value=[]) as mock_search, \
         patch("reviewer.client.chat.completions.create", return_value=mock_response):

        from reviewer import review_pr
        review_pr("my specific diff")

    mock_search.assert_called_once_with("my specific diff", n_results=5)
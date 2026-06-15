import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock


# ── get_all_files ────────────────────────────────────────────────────────────

def test_get_all_files_returns_supported_extensions():
    from indexer import get_all_files

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create supported files
        (open(os.path.join(tmpdir, "app.py"), "w")).close()
        (open(os.path.join(tmpdir, "index.js"), "w")).close()
        # Create unsupported file (should be ignored)
        (open(os.path.join(tmpdir, "image.png"), "w")).close()

        files = get_all_files(tmpdir)
        basenames = [os.path.basename(f) for f in files]

        assert "app.py" in basenames
        assert "index.js" in basenames
        assert "image.png" not in basenames


def test_get_all_files_ignores_venv_and_node_modules():
    from indexer import get_all_files

    with tempfile.TemporaryDirectory() as tmpdir:
        # Files inside ignored dirs
        venv_dir = os.path.join(tmpdir, "venv")
        os.makedirs(venv_dir)
        (open(os.path.join(venv_dir, "helper.py"), "w")).close()

        # File at root level (should be found)
        (open(os.path.join(tmpdir, "main.py"), "w")).close()

        files = get_all_files(tmpdir)
        basenames = [os.path.basename(f) for f in files]

        assert "main.py" in basenames
        assert "helper.py" not in basenames


# ── search_codebase ──────────────────────────────────────────────────────────

def test_search_codebase_returns_formatted_results():
    """Mock ChromaDB and verify search_codebase formats output correctly."""
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["def foo(): pass", "class Bar: ..."]],
        "metadatas": [[{"filepath": "foo.py"}, {"filepath": "bar.py"}]]
    }

    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection

    with patch("indexer.chromadb.PersistentClient", return_value=mock_client), \
         patch("indexer.embedding_functions.SentenceTransformerEmbeddingFunction"):

        from indexer import search_codebase
        results = search_codebase("some query", n_results=2)

    assert len(results) == 2
    assert results[0]["content"] == "def foo(): pass"
    assert results[0]["filepath"] == "foo.py"
    assert results[1]["filepath"] == "bar.py"
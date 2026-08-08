import sys
import pytest
from unittest.mock import MagicMock, patch


# =========================================================================
# CLI Command Tests
# =========================================================================

def test_cli_status_command(capsys):
    """Test that the status command prints collection name and chunk count."""
    with patch("src.cli.get_db") as mock_get_db:
        mock_vs = MagicMock()
        mock_vs.collection.name = "payment_docs"
        mock_vs.collection.count.return_value = 142
        mock_get_db.return_value = mock_vs

        # Import after patching to avoid real ChromaDB initialization
        from src.cli import run_status
        run_status(args=None)

    captured = capsys.readouterr()
    assert "payment_docs" in captured.out
    assert "142" in captured.out


def test_cli_wipe_command_with_documents(capsys):
    """Test wipe command deletes all IDs from a non-empty collection."""
    with patch("src.cli.get_db") as mock_get_db:
        mock_vs = MagicMock()
        mock_vs.collection.name = "payment_docs"
        mock_vs.collection.count.return_value = 10
        mock_vs.collection.get.return_value = {"ids": ["id_1", "id_2", "id_3"]}
        mock_get_db.return_value = mock_vs

        from src.cli import run_wipe
        run_wipe(args=None)

        # Validate that delete was called with the ids from the collection
        mock_vs.collection.delete.assert_called_once_with(ids=["id_1", "id_2", "id_3"])

    captured = capsys.readouterr()
    assert "successfully wiped" in captured.out.lower()


def test_cli_wipe_command_empty_collection(capsys):
    """Test wipe command on an already empty collection does not call delete."""
    with patch("src.cli.get_db") as mock_get_db:
        mock_vs = MagicMock()
        mock_vs.collection.name = "payment_docs"
        mock_vs.collection.count.return_value = 0
        mock_get_db.return_value = mock_vs

        from src.cli import run_wipe
        run_wipe(args=None)

        # Delete should NOT be called for an empty collection
        mock_vs.collection.delete.assert_not_called()


def test_cli_query_command_prints_results(capsys):
    """Test that the query command outputs the correct result structure."""
    with patch("src.cli.get_db") as mock_get_db:
        from src.document import Document

        mock_doc = Document(
            page_content="La firma SHA256 se calcula con el secreto de integridad de Wompi.",
            metadata={
                "api_provider": "wompi",
                "header_path": "Wompi > Firmas",
                "source_url": "https://docs.wompi.co/signatures"
            }
        )

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 384

        mock_vs = MagicMock()
        mock_vs.embedder = mock_embedder
        mock_vs.search.return_value = [mock_doc]
        mock_get_db.return_value = mock_vs

        args = MagicMock()
        args.text = "firma SHA256 Wompi"
        args.k = 1

        from src.cli import run_query
        run_query(args)

    captured = capsys.readouterr()
    assert "WOMPI" in captured.out
    assert "Wompi > Firmas" in captured.out

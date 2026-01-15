"""
Tests for IndexerService.
"""

import sqlite3
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.indexer import IndexerService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create test tables
    cursor.execute("""
        CREATE TABLE kb_animals (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE kb_sources (
            id INTEGER PRIMARY KEY,
            animal_id INTEGER,
            title TEXT,
            url TEXT,
            content TEXT,
            chunk_count INTEGER DEFAULT 0,
            last_indexed DATETIME
        )
    """)

    # Insert test data
    cursor.execute("INSERT INTO kb_animals (id, name) VALUES (1, 'Lion')")
    cursor.execute("""
        INSERT INTO kb_sources (id, animal_id, title, url, content)
        VALUES (1, 1, 'Lion Facts', 'https://example.com', 'Lions are large cats.')
    """)

    conn.commit()
    return conn


def test_get_all_sources(mock_db):
    """Test retrieving all sources from database."""
    indexer = IndexerService(mock_db)
    sources = indexer.get_all_sources()

    assert len(sources) == 1
    assert sources[0]["animal_name"] == "Lion"
    assert sources[0]["title"] == "Lion Facts"
    assert sources[0]["content"] == "Lions are large cats."


def test_chunk_content():
    """Test chunking text content."""
    indexer = IndexerService(Mock())

    # Short content (< 500 chars)
    short_text = "This is a short text."
    chunks = indexer.chunk_content(short_text)
    assert len(chunks) == 1
    assert chunks[0] == "This is a short text."

    # Long content (> 500 chars)
    long_text = "A" * 1000
    chunks = indexer.chunk_content(long_text)
    assert len(chunks) > 1  # Should create multiple chunks


def test_prepare_chunks_for_db():
    """Test preparing chunks for LanceDB."""
    indexer = IndexerService(Mock())

    sources = [{
        "id": 1,
        "animal_id": 1,
        "animal_name": "Lion",
        "title": "Lion Facts",
        "url": "https://example.com",
        "content": "Lions are large cats."
    }]

    chunk_texts = [["Lions are large cats."]]

    prepared = indexer.prepare_chunks_for_db(sources, chunk_texts)

    assert len(prepared) == 1
    assert prepared[0]["text"] == "Lions are large cats."
    assert prepared[0]["metadata"]["animal_name"] == "Lion"
    assert prepared[0]["metadata"]["title"] == "Lion Facts"
    assert prepared[0]["metadata"]["url"] == "https://example.com"


def test_update_source_chunk_counts(mock_db):
    """Test updating source chunk counts."""
    indexer = IndexerService(mock_db)

    sources = [{"id": 1, "animal_name": "Lion"}]
    chunk_counts = [5]

    indexer.update_source_chunk_counts(sources, chunk_counts)

    cursor = mock_db.cursor()
    cursor.execute("SELECT chunk_count FROM kb_sources WHERE id = 1")
    result = cursor.fetchone()

    assert result[0] == 5


@patch('services.indexer.lancedb.connect')
def test_write_to_lancedb(mock_lancedb_connect):
    """Test writing chunks to LanceDB."""
    # Mock LanceDB objects
    mock_table = MagicMock()
    mock_table.count_rows.return_value = 10

    mock_db = MagicMock()
    mock_db.create_table.return_value = mock_table

    mock_lancedb_connect.return_value = mock_db

    # Mock the embedding function
    with patch('services.indexer.get_registry') as mock_registry:
        mock_func = MagicMock()
        mock_func.ndims.return_value = 1536
        mock_registry.return_value.get.return_value.create.return_value = mock_func

        indexer = IndexerService(Mock())

        processed_chunks = [{
            "text": "Test chunk",
            "metadata": {
                "animal_name": "Lion",
                "filename": None,
                "title": "Test",
                "url": "https://example.com"
            }
        }]

        count = indexer.write_to_lancedb(processed_chunks)

        assert count == 10
        assert mock_table.add.called

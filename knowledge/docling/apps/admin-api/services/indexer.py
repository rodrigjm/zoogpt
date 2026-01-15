"""
Vector indexer service for rebuilding LanceDB from SQLite sources.
"""

import os
import sqlite3
from typing import List, Dict
import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector


# LanceDB settings
DB_PATH = os.environ.get("LANCEDB_PATH", "data/zoo_lancedb")
TABLE_NAME = "animals"


class IndexerService:
    """Service for rebuilding the vector index from SQLite sources."""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

    def get_all_sources(self) -> List[Dict]:
        """
        Query all sources from kb_sources with animal names.

        Returns:
            List of dictionaries with source data
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                s.id,
                s.animal_id,
                s.title,
                s.url,
                s.content,
                a.name as animal_name
            FROM kb_sources s
            JOIN kb_animals a ON s.animal_id = a.id
            ORDER BY s.id
        """)

        sources = []
        for row in cursor.fetchall():
            sources.append({
                "id": row[0],
                "animal_id": row[1],
                "title": row[2],
                "url": row[3],
                "content": row[4],
                "animal_name": row[5],
            })

        return sources

    def chunk_content(self, content: str) -> List[str]:
        """
        Chunk text content using simple overlapping chunks.

        Args:
            content: Raw text content to chunk

        Returns:
            List of chunk text strings
        """
        chunks = []

        # Simple chunking: ~500 character chunks with 100 char overlap
        # This matches the approximate behavior of HybridChunker
        chunk_size = 500
        overlap = 100

        for i in range(0, len(content), chunk_size - overlap):
            chunk_text = content[i:i + chunk_size].strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks

    def prepare_chunks_for_db(
        self,
        sources: List[Dict],
        chunk_texts_per_source: List[List[str]]
    ) -> List[dict]:
        """
        Prepare chunks for LanceDB insertion.

        Args:
            sources: List of source dictionaries
            chunk_texts_per_source: List of chunk lists, one per source

        Returns:
            List of dictionaries ready for LanceDB
        """
        processed_chunks = []

        for source, chunk_texts in zip(sources, chunk_texts_per_source):
            for chunk_text in chunk_texts:
                processed_chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "animal_name": source["animal_name"],
                        "filename": None,  # Not applicable for DB sources
                        "title": source["title"],
                        "url": source["url"],
                    },
                })

        return processed_chunks

    def write_to_lancedb(self, processed_chunks: List[dict]) -> int:
        """
        Write chunks to LanceDB with embeddings.

        Args:
            processed_chunks: List of chunk dictionaries

        Returns:
            Number of chunks written
        """
        # Create database connection
        db = lancedb.connect(DB_PATH)

        # Get OpenAI embedding function (text-embedding-3-large as per zoo_build_knowledge.py)
        func = get_registry().get("openai").create(name="text-embedding-3-large")

        # Define metadata schema
        class ChunkMetadata(LanceModel):
            """Metadata for each chunk."""
            animal_name: str | None
            filename: str | None
            title: str | None
            url: str | None

        # Define main schema
        class AnimalChunks(LanceModel):
            text: str = func.SourceField()
            vector: Vector(func.ndims()) = func.VectorField()  # type: ignore
            metadata: ChunkMetadata

        # Create table (overwrite mode handles concurrent access)
        table = db.create_table(TABLE_NAME, schema=AnimalChunks, mode="overwrite")

        # Add chunks in batches to avoid rate limits
        batch_size = 50
        for i in range(0, len(processed_chunks), batch_size):
            batch = processed_chunks[i:i + batch_size]
            table.add(batch)

        return table.count_rows()

    def update_source_chunk_counts(
        self,
        sources: List[Dict],
        chunk_counts: List[int]
    ):
        """
        Update chunk_count and last_indexed for each source.

        Args:
            sources: List of source dictionaries
            chunk_counts: List of chunk counts per source
        """
        cursor = self.conn.cursor()

        for source, chunk_count in zip(sources, chunk_counts):
            cursor.execute(
                """UPDATE kb_sources
                   SET chunk_count = ?,
                       last_indexed = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (chunk_count, source["id"])
            )

        self.conn.commit()

    def rebuild_index(self) -> tuple[int, int]:
        """
        Complete index rebuild process.

        Returns:
            Tuple of (total_documents, total_chunks)
        """
        # 1. Read all sources
        sources = self.get_all_sources()
        total_documents = len(sources)

        if total_documents == 0:
            return (0, 0)

        # 2. Chunk all content
        all_chunk_texts = []
        chunk_counts = []

        for source in sources:
            chunks = self.chunk_content(source["content"])
            all_chunk_texts.append(chunks)
            chunk_counts.append(len(chunks))

        # 3. Prepare chunks for LanceDB
        processed_chunks = self.prepare_chunks_for_db(sources, all_chunk_texts)
        total_chunks = len(processed_chunks)

        # 4. Write to LanceDB (with embeddings)
        self.write_to_lancedb(processed_chunks)

        # 5. Update source records
        self.update_source_chunk_counts(sources, chunk_counts)

        return (total_documents, total_chunks)

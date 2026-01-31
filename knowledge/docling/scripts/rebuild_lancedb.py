#!/usr/bin/env python3
"""
Rebuild LanceDB vector index from SQLite sources.

Usage:
    # Local (from project root):
    python3 scripts/rebuild_lancedb.py

    # Docker:
    docker exec zoocari-admin-api python3 /app/scripts/rebuild_lancedb.py
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "admin-api"))

# Determine paths based on environment
if os.environ.get("LANCEDB_PATH"):
    # Docker environment
    LANCEDB_PATH = os.environ["LANCEDB_PATH"]
    SESSION_DB_PATH = os.environ.get("SESSION_DB_PATH", "/app/data/sessions.db")
else:
    # Local environment
    PROJECT_ROOT = Path(__file__).parent.parent
    LANCEDB_PATH = str(PROJECT_ROOT / "data" / "zoo_lancedb")
    SESSION_DB_PATH = str(PROJECT_ROOT / "data" / "sessions.db")


def main():
    print("=" * 60)
    print("LANCEDB INDEX REBUILD")
    print("=" * 60)

    # Check OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not set!")
        print("   Set it in your environment or .env file")
        return 1
    print(f"✓ OpenAI API key found: {api_key[:10]}...{api_key[-4:]}")

    # Check database
    print(f"\n--- Database ---")
    print(f"SQLite path: {SESSION_DB_PATH}")
    print(f"LanceDB path: {LANCEDB_PATH}")

    if not Path(SESSION_DB_PATH).exists():
        print(f"\n❌ ERROR: Database not found at {SESSION_DB_PATH}")
        return 1
    print(f"✓ Database exists")

    # Connect and check sources
    conn = sqlite3.connect(SESSION_DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM kb_animals")
    animal_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM kb_sources")
    source_count = cursor.fetchone()[0]

    print(f"✓ Found {animal_count} animals, {source_count} sources")

    if source_count == 0:
        print("\n⚠️  No sources to index!")
        return 0

    # Import and run indexer
    print(f"\n--- Running indexer ---")

    try:
        # Set LanceDB path for indexer
        os.environ["LANCEDB_PATH"] = LANCEDB_PATH

        from services.indexer import IndexerService

        indexer = IndexerService(conn)

        print("Reading sources...")
        sources = indexer.get_all_sources()
        print(f"✓ Read {len(sources)} sources")

        print("Chunking content...")
        all_chunks = []
        chunk_counts = []
        for source in sources:
            chunks = indexer.chunk_content(source["content"])
            all_chunks.append(chunks)
            chunk_counts.append(len(chunks))
        total_chunks = sum(chunk_counts)
        print(f"✓ Created {total_chunks} chunks")

        print("Preparing for LanceDB...")
        processed = indexer.prepare_chunks_for_db(sources, all_chunks)
        print(f"✓ Prepared {len(processed)} records")

        print("Writing to LanceDB (generating embeddings)...")
        print("   This may take a few minutes...")
        rows_written = indexer.write_to_lancedb(processed)
        print(f"✓ Wrote {rows_written} rows to LanceDB")

        print("Updating source records...")
        indexer.update_source_chunk_counts(sources, chunk_counts)
        print(f"✓ Updated chunk counts")

        print("\n" + "=" * 60)
        print("✅ INDEX REBUILD COMPLETE")
        print("=" * 60)
        print(f"   Documents: {len(sources)}")
        print(f"   Chunks:    {total_chunks}")
        print(f"   LanceDB:   {LANCEDB_PATH}")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

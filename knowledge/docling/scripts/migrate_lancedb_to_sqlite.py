#!/usr/bin/env python3
"""
Migration script: LanceDB → SQLite KB tables

This script extracts animals and sources from the existing LanceDB
and populates the kb_animals and kb_sources tables for admin portal management.
"""

import sqlite3
import lancedb
from pathlib import Path
from collections import defaultdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
LANCEDB_PATH = PROJECT_ROOT / "data" / "zoo_lancedb"
SQLITE_PATH = PROJECT_ROOT / "data" / "sessions.db"

# Noise entries to skip
NOISE_ENTRIES = {
    'Contents', 'orca gallery', 'The Elephant', 'The Hippopotamus', 'The Lion',
    '', None
}


def normalize_animal_name(name: str) -> str:
    """Normalize animal name to title case."""
    if not name:
        return ""
    return name.strip().title().replace('-Billed', '-billed')


def extract_from_lancedb():
    """Extract animals and their content from LanceDB."""
    print(f"Connecting to LanceDB at {LANCEDB_PATH}...")
    db = lancedb.connect(str(LANCEDB_PATH))
    table = db.open_table("animals")
    df = table.to_pandas()

    print(f"Found {len(df)} chunks in LanceDB")

    # Group chunks by animal
    animals_content = defaultdict(list)

    for _, row in df.iterrows():
        metadata = row.get('metadata', {})
        if not isinstance(metadata, dict):
            continue

        animal_name = metadata.get('animal_name', '')
        if animal_name in NOISE_ENTRIES:
            continue

        normalized_name = normalize_animal_name(animal_name)
        if not normalized_name:
            continue

        chunk_data = {
            'text': row.get('text', ''),
            'title': metadata.get('title', ''),
            'url': metadata.get('url', ''),
        }
        animals_content[normalized_name].append(chunk_data)

    print(f"Extracted {len(animals_content)} unique animals")
    return animals_content


def migrate_to_sqlite(animals_content: dict):
    """Migrate extracted data to SQLite KB tables."""
    print(f"Connecting to SQLite at {SQLITE_PATH}...")
    conn = sqlite3.connect(str(SQLITE_PATH))
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM kb_sources")
    cursor.execute("DELETE FROM kb_animals")
    conn.commit()
    print("Cleared existing KB tables")

    animals_inserted = 0
    sources_inserted = 0

    for animal_name, chunks in sorted(animals_content.items()):
        # Insert animal
        cursor.execute("""
            INSERT INTO kb_animals (name, display_name, category, source_count, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (
            animal_name.lower().replace(' ', '_'),  # name (slug)
            animal_name,  # display_name
            'General',  # category
            1,  # source_count (we'll combine all chunks into one source)
            True  # is_active
        ))
        animal_id = cursor.lastrowid
        animals_inserted += 1

        # Combine all chunks into one source per animal
        # Group by title if available, otherwise combine all
        combined_content = "\n\n".join(chunk['text'] for chunk in chunks if chunk['text'])
        title = chunks[0].get('title') or f"About {animal_name}"
        url = chunks[0].get('url') or ''

        cursor.execute("""
            INSERT INTO kb_sources (animal_id, title, url, content, chunk_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            animal_id,
            title,
            url,
            combined_content,
            len(chunks)
        ))
        sources_inserted += 1

        # Update source_count
        cursor.execute("""
            UPDATE kb_animals SET source_count = 1 WHERE id = ?
        """, (animal_id,))

    conn.commit()
    conn.close()

    print(f"Inserted {animals_inserted} animals")
    print(f"Inserted {sources_inserted} sources")
    return animals_inserted, sources_inserted


def verify_migration():
    """Verify the migration was successful."""
    conn = sqlite3.connect(str(SQLITE_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM kb_animals")
    animal_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM kb_sources")
    source_count = cursor.fetchone()[0]

    cursor.execute("SELECT display_name FROM kb_animals ORDER BY display_name LIMIT 10")
    sample_animals = [row[0] for row in cursor.fetchall()]

    conn.close()

    print(f"\n✅ Migration verified:")
    print(f"   Animals: {animal_count}")
    print(f"   Sources: {source_count}")
    print(f"   Sample: {', '.join(sample_animals)}...")

    return animal_count, source_count


def main():
    print("=" * 60)
    print("LanceDB → SQLite KB Migration")
    print("=" * 60)

    # Extract from LanceDB
    animals_content = extract_from_lancedb()

    # Migrate to SQLite
    migrate_to_sqlite(animals_content)

    # Verify
    verify_migration()

    print("\n" + "=" * 60)
    print("Migration complete! You can now use the Admin Portal to manage KB.")
    print("=" * 60)


if __name__ == "__main__":
    main()

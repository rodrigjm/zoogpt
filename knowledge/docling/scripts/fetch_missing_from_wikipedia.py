#!/usr/bin/env python3
"""
Fetch missing park animal content from Wikipedia.
"""

import sqlite3
import json
import time
import re
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False

DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"

# Missing species with Wikipedia article titles
MISSING_ANIMALS = [
    {
        "name": "laughing_kookaburra",
        "display_name": "Laughing Kookaburra",
        "category": "park_animal",
        "wikipedia_title": "Laughing_kookaburra"
    },
    {
        "name": "zebu",
        "display_name": "Zebu (Indian Humped Cattle)",
        "category": "park_animal",
        "wikipedia_title": "Zebu"
    },
    {
        "name": "grey_crowned_crane",
        "display_name": "Grey Crowned Crane",
        "category": "park_animal",
        "wikipedia_title": "Grey_crowned_crane"
    },
    {
        "name": "common_raven",
        "display_name": "Common Raven",
        "category": "park_animal",
        "wikipedia_title": "Common_raven"
    },
    {
        "name": "whites_tree_frog",
        "display_name": "White's Tree Frog",
        "category": "park_animal",
        "wikipedia_title": "Australian_green_tree_frog"
    },
    {
        "name": "blue_tongued_skink",
        "display_name": "Blue-tongued Skink",
        "category": "park_animal",
        "wikipedia_title": "Blue-tongued_skink"
    },
    {
        "name": "argentine_tegu",
        "display_name": "Argentine Black and White Tegu",
        "category": "park_animal",
        "wikipedia_title": "Argentine_black_and_white_tegu"
    },
    {
        "name": "emperor_scorpion",
        "display_name": "Emperor Scorpion",
        "category": "park_animal",
        "wikipedia_title": "Emperor_scorpion"
    },
    {
        "name": "ring_tailed_lemur",
        "display_name": "Ring-tailed Lemur",
        "category": "park_animal",
        "wikipedia_title": "Ring-tailed_lemur"
    },
    {
        "name": "black_and_white_ruffed_lemur",
        "display_name": "Black-and-white Ruffed Lemur",
        "category": "park_animal",
        "wikipedia_title": "Black-and-white_ruffed_lemur"
    },
]


def fetch_wikipedia_extract(title: str) -> str | None:
    """Fetch Wikipedia article extract using the API."""
    api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title

    try:
        if HAS_REQUESTS:
            headers = {'User-Agent': 'ZoocariBot/1.0 (Educational zoo chatbot)'}
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        else:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'ZoocariBot/1.0 (Educational zoo chatbot)'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

        # Get the extract
        extract = data.get("extract", "")

        # If extract is short, try to get more content from the full page
        if len(extract) < 500:
            return fetch_wikipedia_full(title)

        return extract

    except Exception as e:
        print(f"    ✗ API failed: {e}")
        return fetch_wikipedia_full(title)


def fetch_wikipedia_full(title: str) -> str | None:
    """Fetch full Wikipedia page content via API."""
    api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=extracts&explaintext=1&format=json"

    try:
        if HAS_REQUESTS:
            headers = {'User-Agent': 'ZoocariBot/1.0 (Educational zoo chatbot)'}
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        else:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'ZoocariBot/1.0 (Educational zoo chatbot)'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

        # Extract content from response
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1":  # -1 means page not found
                content = page_data.get("extract", "")
                if content:
                    # Clean up and limit size
                    content = clean_wikipedia_content(content)
                    return content[:8000]

        return None

    except Exception as e:
        print(f"    ✗ Full page fetch failed: {e}")
        return None


def clean_wikipedia_content(content: str) -> str:
    """Clean Wikipedia content for kid-friendly use."""
    # Remove reference markers like [1], [2], etc.
    content = re.sub(r'\[\d+\]', '', content)

    # Remove excessive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Remove "See also", "References", "External links" sections
    for section in ['== See also ==', '== References ==', '== External links ==',
                    '== Further reading ==', '== Notes ==']:
        if section in content:
            content = content.split(section)[0]

    return content.strip()


def get_db_connection() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def animal_exists(conn: sqlite3.Connection, name: str) -> bool:
    """Check if animal already exists in KB."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM kb_animals WHERE name = ?", (name,))
    return cursor.fetchone() is not None


def insert_animal(conn: sqlite3.Connection, animal: dict) -> int:
    """Insert animal into kb_animals, return id."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO kb_animals (name, display_name, category, source_count)
        VALUES (?, ?, ?, 0)
    """, (animal["name"], animal["display_name"], animal["category"]))
    conn.commit()
    return cursor.lastrowid


def insert_source(conn: sqlite3.Connection, animal_id: int, title: str, url: str, content: str):
    """Insert source into kb_sources."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO kb_sources (animal_id, title, url, content)
        VALUES (?, ?, ?, ?)
    """, (animal_id, title, url, content))

    cursor.execute("""
        UPDATE kb_animals SET source_count = source_count + 1 WHERE id = ?
    """, (animal_id,))
    conn.commit()


def main():
    print("=" * 60)
    print("FETCHING MISSING ANIMALS FROM WIKIPEDIA")
    print("=" * 60)

    conn = get_db_connection()

    added = 0
    skipped = 0
    failed = 0

    for animal in MISSING_ANIMALS:
        name = animal["name"]
        display_name = animal["display_name"]
        wiki_title = animal["wikipedia_title"]

        print(f"\n[{added + skipped + failed + 1}/{len(MISSING_ANIMALS)}] {display_name}")

        # Check if exists
        if animal_exists(conn, name):
            print(f"  → Already exists, skipping")
            skipped += 1
            continue

        # Fetch from Wikipedia
        print(f"  Fetching from Wikipedia ({wiki_title})...")
        content = fetch_wikipedia_extract(wiki_title)

        if content and len(content) > 200:
            print(f"    ✓ Got {len(content)} chars")

            # Insert into DB
            animal_id = insert_animal(conn, animal)
            wiki_url = f"https://en.wikipedia.org/wiki/{wiki_title}"
            insert_source(conn, animal_id, "Wikipedia", wiki_url, content)

            print(f"  ✓ Added to KB (id={animal_id})")
            added += 1
        else:
            print(f"  ✗ No content or too short")
            failed += 1

        time.sleep(0.5)  # Rate limiting

    conn.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Added:   {added}")
    print(f"  Skipped: {skipped} (already exist)")
    print(f"  Failed:  {failed}")
    print(f"\nNext step: Rebuild LanceDB index")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())

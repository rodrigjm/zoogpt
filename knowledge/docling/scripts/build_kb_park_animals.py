#!/usr/bin/env python3
"""
Build KB entries for park animals missing from the knowledge base.
Fetches content from multiple sources and inserts into SQLite.
"""

import sqlite3
import json
import time
import re
from pathlib import Path
from urllib.parse import quote

# Try to import requests, fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"

# Park inventory for location data
PARK_INVENTORY_PATH = Path(__file__).parent.parent / "data" / "park_inventory.json"


# Species to add - group name, display name, specific types, source slugs
PARK_ANIMALS_TO_ADD = [
    # Priority 1: Interactive/Popular
    {
        "name": "cotton_top_tamarin",
        "display_name": "Cotton-top Tamarin",
        "category": "park_animal",
        "group": "monkey",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/cotton-top-tamarin"),
            ("A-Z Animals", "https://a-z-animals.com/animals/cotton-top-tamarin/"),
        ]
    },
    {
        "name": "common_marmoset",
        "display_name": "Common Marmoset",
        "category": "park_animal",
        "group": "monkey",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/marmoset/"),
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/marmoset"),
        ]
    },
    {
        "name": "squirrel_monkey",
        "display_name": "Squirrel Monkey",
        "category": "park_animal",
        "group": "monkey",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/squirrel-monkey"),
            ("A-Z Animals", "https://a-z-animals.com/animals/squirrel-monkey/"),
        ]
    },
    {
        "name": "african_crested_porcupine",
        "display_name": "African Crested Porcupine",
        "category": "park_animal",
        "group": "porcupine",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/porcupine"),
            ("A-Z Animals", "https://a-z-animals.com/animals/crested-porcupine/"),
        ]
    },
    {
        "name": "serval",
        "display_name": "Serval",
        "category": "park_animal",
        "group": "cat",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/serval"),
            ("A-Z Animals", "https://a-z-animals.com/animals/serval/"),
        ]
    },
    {
        "name": "lar_gibbon",
        "display_name": "Lar Gibbon (White-handed Gibbon)",
        "category": "park_animal",
        "group": "primate",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/gibbon"),
            ("A-Z Animals", "https://a-z-animals.com/animals/gibbon/"),
        ]
    },
    {
        "name": "chinchilla",
        "display_name": "Chinchilla",
        "category": "park_animal",
        "group": "rodent",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/chinchilla/"),
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/chinchilla"),
        ]
    },
    # Priority 2: Unique/Interesting
    {
        "name": "laughing_kookaburra",
        "display_name": "Laughing Kookaburra",
        "category": "park_animal",
        "group": "bird",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/kookaburra"),
            ("A-Z Animals", "https://a-z-animals.com/animals/kookaburra/"),
        ]
    },
    {
        "name": "patagonian_mara",
        "display_name": "Patagonian Mara (Cavy)",
        "category": "park_animal",
        "group": "rodent",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/patagonian-mara/"),
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/patagonian-mara"),
        ]
    },
    {
        "name": "coatimundi",
        "display_name": "Coatimundi (Coati)",
        "category": "park_animal",
        "group": "mammal",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/coati"),
            ("A-Z Animals", "https://a-z-animals.com/animals/coatimundi/"),
        ]
    },
    {
        "name": "nilgai",
        "display_name": "Nilgai (Blue Bull Antelope)",
        "category": "park_animal",
        "group": "antelope",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/nilgai/"),
        ]
    },
    {
        "name": "zebu",
        "display_name": "Zebu (Indian Humped Cattle)",
        "category": "park_animal",
        "group": "cattle",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/zebu-cattle/"),
        ]
    },
    # Priority 3: Birds
    {
        "name": "crowned_crane",
        "display_name": "East African Crowned Crane",
        "category": "park_animal",
        "group": "bird",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/crowned-crane"),
            ("A-Z Animals", "https://a-z-animals.com/animals/crowned-crane/"),
        ]
    },
    {
        "name": "indian_peafowl",
        "display_name": "Indian Peafowl (Peacock)",
        "category": "park_animal",
        "group": "bird",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/peafowl"),
            ("A-Z Animals", "https://a-z-animals.com/animals/peacock/"),
        ]
    },
    {
        "name": "wild_turkey",
        "display_name": "Wild Turkey",
        "category": "park_animal",
        "group": "bird",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/turkey/"),
        ]
    },
    {
        "name": "common_raven",
        "display_name": "Common Raven",
        "category": "park_animal",
        "group": "bird",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/raven/"),
        ]
    },
    {
        "name": "fallow_deer",
        "display_name": "Fallow Deer",
        "category": "park_animal",
        "group": "deer",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/fallow-deer/"),
        ]
    },
    {
        "name": "four_toed_hedgehog",
        "display_name": "Four-toed Hedgehog",
        "category": "park_animal",
        "group": "mammal",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/hedgehog"),
            ("A-Z Animals", "https://a-z-animals.com/animals/hedgehog/"),
        ]
    },
    # Reptiles & Amphibians
    {
        "name": "ball_python",
        "display_name": "Ball Python (Royal Python)",
        "category": "park_animal",
        "group": "snake",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/ball-python"),
            ("A-Z Animals", "https://a-z-animals.com/animals/ball-python/"),
        ]
    },
    {
        "name": "indigo_snake",
        "display_name": "Eastern Indigo Snake",
        "category": "park_animal",
        "group": "snake",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/indigo-snake/"),
        ]
    },
    {
        "name": "whites_tree_frog",
        "display_name": "White's Tree Frog",
        "category": "park_animal",
        "group": "amphibian",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/whites-tree-frog/"),
        ]
    },
    {
        "name": "leaf_tailed_gecko",
        "display_name": "Leaf-tailed Gecko",
        "category": "park_animal",
        "group": "reptile",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/leaf-tailed-gecko/"),
        ]
    },
    {
        "name": "blue_tongued_skink",
        "display_name": "Blue-tongued Skink",
        "category": "park_animal",
        "group": "reptile",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/blue-tongued-skink"),
            ("A-Z Animals", "https://a-z-animals.com/animals/blue-tongued-skink/"),
        ]
    },
    {
        "name": "argentine_tegu",
        "display_name": "Argentine Black and White Tegu",
        "category": "park_animal",
        "group": "reptile",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/tegu-lizard/"),
        ]
    },
    {
        "name": "emperor_scorpion",
        "display_name": "Emperor Scorpion",
        "category": "park_animal",
        "group": "arachnid",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/emperor-scorpion/"),
        ]
    },
    # Livestock guardian dog
    {
        "name": "anatolian_shepherd",
        "display_name": "Anatolian Shepherd Dog",
        "category": "park_animal",
        "group": "dog",
        "sources": [
            ("A-Z Animals", "https://a-z-animals.com/animals/anatolian-shepherd-dog/"),
        ]
    },
    # Ring-tailed lemur (may already exist but adding species-specific)
    {
        "name": "ring_tailed_lemur",
        "display_name": "Ring-tailed Lemur",
        "category": "park_animal",
        "group": "lemur",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/ring-tailed-lemur"),
            ("A-Z Animals", "https://a-z-animals.com/animals/ring-tailed-lemur/"),
        ]
    },
    {
        "name": "black_and_white_ruffed_lemur",
        "display_name": "Black-and-white Ruffed Lemur",
        "category": "park_animal",
        "group": "lemur",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/ruffed-lemur"),
            ("A-Z Animals", "https://a-z-animals.com/animals/black-and-white-ruffed-lemur/"),
        ]
    },
    # Tortoises (species-specific)
    {
        "name": "red_footed_tortoise",
        "display_name": "Red-footed Tortoise",
        "category": "park_animal",
        "group": "tortoise",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/red-footed-tortoise"),
            ("A-Z Animals", "https://a-z-animals.com/animals/red-footed-tortoise/"),
        ]
    },
    {
        "name": "african_spurred_tortoise",
        "display_name": "African Spurred Tortoise (Sulcata)",
        "category": "park_animal",
        "group": "tortoise",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/african-spurred-tortoise"),
            ("A-Z Animals", "https://a-z-animals.com/animals/sulcata-tortoise/"),
        ]
    },
    {
        "name": "aldabra_giant_tortoise",
        "display_name": "Aldabra Giant Tortoise",
        "category": "park_animal",
        "group": "tortoise",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/aldabra-tortoise"),
            ("A-Z Animals", "https://a-z-animals.com/animals/aldabra-giant-tortoise/"),
        ]
    },
    # Two-toed sloth (specific)
    {
        "name": "two_toed_sloth",
        "display_name": "Linnaeus's Two-toed Sloth",
        "category": "park_animal",
        "group": "sloth",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/two-toed-sloth"),
            ("A-Z Animals", "https://a-z-animals.com/animals/two-toed-sloth/"),
        ]
    },
    # Bennetts wallaby
    {
        "name": "bennetts_wallaby",
        "display_name": "Bennett's Wallaby (Red-necked Wallaby)",
        "category": "park_animal",
        "group": "wallaby",
        "sources": [
            ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/wallaby"),
            ("A-Z Animals", "https://a-z-animals.com/animals/wallaby/"),
        ]
    },
]


def fetch_url(url: str, timeout: int = 30) -> str | None:
    """Fetch URL content."""
    try:
        if HAS_REQUESTS:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        else:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8')
    except Exception as e:
        print(f"    ✗ Failed to fetch {url}: {e}")
        return None


def extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML, focusing on main content."""
    # Remove script and style elements
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Convert common elements to text
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<p[^>]*>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<h[1-6][^>]*>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</h[1-6]>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<li[^>]*>', '\n• ', html, flags=re.IGNORECASE)

    # Remove all remaining tags
    html = re.sub(r'<[^>]+>', ' ', html)

    # Clean up whitespace
    html = re.sub(r'&nbsp;', ' ', html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'&lt;', '<', html)
    html = re.sub(r'&gt;', '>', html)
    html = re.sub(r'&#\d+;', '', html)
    html = re.sub(r'&\w+;', '', html)
    html = re.sub(r'\s+', ' ', html)
    html = re.sub(r'\n\s*\n', '\n\n', html)

    return html.strip()


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

    # Update source count
    cursor.execute("""
        UPDATE kb_animals SET source_count = source_count + 1 WHERE id = ?
    """, (animal_id,))
    conn.commit()


def update_existing_park_animals(conn: sqlite3.Connection, park_inventory: dict):
    """Mark existing KB animals that are at the park with category='park_animal'."""
    cursor = conn.cursor()

    park_species = set(park_inventory.get("animals_by_species", {}).keys())

    # Get all KB animals
    cursor.execute("SELECT id, name FROM kb_animals")
    kb_animals = cursor.fetchall()

    updated = 0
    for row in kb_animals:
        animal_name = row["name"].lower().replace("_", " ")

        # Check if this animal is at the park
        is_at_park = False
        for species in park_species:
            if species in animal_name or animal_name in species:
                is_at_park = True
                break

        if is_at_park:
            cursor.execute("""
                UPDATE kb_animals SET category = 'park_animal' WHERE id = ?
            """, (row["id"],))
            updated += 1

    conn.commit()
    return updated


def main():
    print("=" * 60)
    print("PARK ANIMALS KB BUILDER")
    print("=" * 60)

    # Load park inventory for location data
    park_inventory = {}
    if PARK_INVENTORY_PATH.exists():
        with open(PARK_INVENTORY_PATH) as f:
            park_inventory = json.load(f)
        print(f"✓ Loaded park inventory: {len(park_inventory.get('animals_by_species', {}))} species")

    conn = get_db_connection()

    # First, update existing animals
    print("\n--- Updating existing park animals ---")
    updated = update_existing_park_animals(conn, park_inventory)
    print(f"✓ Updated {updated} existing animals to category='park_animal'")

    # Process new animals
    print(f"\n--- Adding {len(PARK_ANIMALS_TO_ADD)} new park animals ---")

    added = 0
    skipped = 0
    failed = 0

    for animal in PARK_ANIMALS_TO_ADD:
        name = animal["name"]
        display_name = animal["display_name"]

        print(f"\n[{added + skipped + failed + 1}/{len(PARK_ANIMALS_TO_ADD)}] {display_name}")

        # Check if exists
        if animal_exists(conn, name):
            print(f"  → Already exists, skipping")
            skipped += 1
            continue

        # Try to fetch content from sources
        content = None
        source_title = None
        source_url = None

        for title, url in animal["sources"]:
            print(f"  Trying {title}...")
            html = fetch_url(url)
            if html:
                text = extract_text_from_html(html)
                if len(text) > 200:  # Minimum viable content
                    content = text[:8000]  # Limit size
                    source_title = title
                    source_url = url
                    print(f"    ✓ Got {len(content)} chars")
                    break
                else:
                    print(f"    ✗ Content too short ({len(text)} chars)")

            time.sleep(0.5)  # Rate limiting

        if content:
            # Insert animal and source
            animal_id = insert_animal(conn, animal)
            insert_source(conn, animal_id, source_title, source_url, content)
            print(f"  ✓ Added to KB (id={animal_id})")
            added += 1
        else:
            print(f"  ✗ No content found from any source")
            failed += 1

    conn.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Added:   {added}")
    print(f"  Skipped: {skipped} (already exist)")
    print(f"  Failed:  {failed} (no content)")
    print(f"\nNext step: Rebuild LanceDB index via admin API")
    print("  curl -X POST http://localhost:8001/kb/rebuild-index")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Build park inventory JSON from CSV data.
Parses the animal inventory CSV and outputs structured JSON for RAG enrichment.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict


def normalize_species(group_name: str) -> str:
    """Normalize species/group name to lowercase singular form."""
    name = group_name.lower().strip()
    # Handle plurals
    if name.endswith('s') and name not in ['zebu', 'nilgai']:
        name = name.rstrip('s')
    return name


def simplify_location(section_path: str) -> str:
    """Extract simplified location from section path."""
    # "Barn - Barn Stalls 1-5" -> "Barn"
    # "Contact - Contact Area" -> "Contact Area"
    # "Barnyard Circle - Llama" -> "Barnyard Circle"
    # "Building - Window Exhibits" -> "Building - Window Exhibits"
    parts = section_path.split(' - ', 1)
    if len(parts) == 2:
        area, specific = parts
        # For contact area, use the specific name
        if area.lower() == 'contact':
            return specific
        # For building exhibits, keep full path
        if area.lower() == 'building':
            return section_path
        # For barnyard circle, just use the area
        if 'barnyard' in area.lower():
            return area
        # For fields, include the specific area
        if area.lower() == 'fields':
            return specific
        # For back of barn, simplify
        if 'back of barn' in area.lower():
            return "Back of Barn"
        # Default: use area name
        return area
    return section_path


def build_aliases() -> dict:
    """Build species aliases mapping."""
    return {
        "monkey": ["tamarin", "marmoset", "squirrel monkey"],
        "tortoise": ["turtle"],
        "peacock": ["peafowl"],
        "chicken": ["rooster", "hen"],
        "pig": ["hog", "swine"],
        "donkey": ["burro", "ass"],
        "cow": ["cattle", "zebu", "brahma"],
        "deer": ["fallow deer"],
        "bird": ["parrot", "macaw", "kookaburra", "raven", "hawk", "crane", "emu", "turkey", "peacock", "chicken"],
        "cat": ["serval"],
        "snake": ["python", "indigo snake", "kingsnake", "hognose"],
        "lizard": ["tegu", "skink", "gecko"],
        "frog": ["tree frog"],
        "bug": ["beetle", "cockroach", "millipede", "scorpion", "tarantula", "vinegaroon"],
    }


def main():
    # Paths
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    csv_path = data_dir / "Metadata_Animal_Inventory - Animal Inventory.csv"
    output_path = data_dir / "park_inventory.json"

    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        return 1

    # Data structures
    animals_by_species = defaultdict(lambda: {
        "at_park": True,
        "count": 0,
        "locations": set(),
        "individuals": []
    })
    animals_by_name = {}

    # Parse CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            section_path = row.get('SectionPath', '')
            canonical_name2 = row.get('CanonicalName2', '')  # Breed/type info
            animal_name = row.get('AnimalName', '').strip()
            group_name = row.get('AnimalGroupsName', '').strip()
            gender = row.get('GenderName', 'Unknown')

            # Skip rows without group name (some invertebrates)
            if not group_name:
                # Try to infer from canonical name
                if 'scorpion' in canonical_name2.lower():
                    group_name = 'Scorpion'
                elif 'tarantula' in canonical_name2.lower() or 'spider' in canonical_name2.lower():
                    group_name = 'Tarantula'
                elif 'gecko' in canonical_name2.lower():
                    group_name = 'Gecko'
                elif 'skink' in canonical_name2.lower():
                    group_name = 'Skink'
                elif 'tegu' in canonical_name2.lower():
                    group_name = 'Tegu'
                elif 'python' in canonical_name2.lower():
                    group_name = 'Snake'
                elif 'snake' in canonical_name2.lower():
                    group_name = 'Snake'
                elif 'frog' in canonical_name2.lower():
                    group_name = 'Frog'
                elif 'hedgehog' in canonical_name2.lower():
                    group_name = 'Hedgehog'
                elif 'porcupine' in canonical_name2.lower():
                    group_name = 'Porcupine'
                elif 'sloth' in canonical_name2.lower():
                    group_name = 'Sloth'
                elif 'horse' in canonical_name2.lower() or 'pony' in canonical_name2.lower():
                    group_name = 'Horse'
                else:
                    continue  # Skip if we can't categorize

            species_key = normalize_species(group_name)
            location = simplify_location(section_path)

            # Update species data
            species_data = animals_by_species[species_key]
            species_data["count"] += 1
            species_data["locations"].add(location)

            # Get birthdate
            birthdate = row.get('BirthDate', '').strip()

            # Add individual if named
            if animal_name and animal_name.lower() not in ['beetle colony', 'millepedes', 'madagascar hissing cockroach 1']:
                individual = {
                    "name": animal_name,
                    "breed": canonical_name2 if canonical_name2 else None,
                    "location": location,
                    "gender": gender,
                    "birthdate": birthdate if birthdate else None
                }
                species_data["individuals"].append(individual)

                # Add to name lookup (lowercase for matching)
                name_key = animal_name.lower()
                animals_by_name[name_key] = {
                    "species": species_key,
                    "type": canonical_name2 if canonical_name2 else group_name,
                    "location": location,
                    "gender": gender,
                    "birthdate": birthdate if birthdate else None
                }

    # Convert sets to sorted lists for JSON serialization
    output_species = {}
    for species, data in animals_by_species.items():
        output_species[species] = {
            "at_park": data["at_park"],
            "count": data["count"],
            "locations": sorted(list(data["locations"])),
            "individuals": data["individuals"]
        }

    # Build final output
    output = {
        "animals_by_species": output_species,
        "animals_by_name": animals_by_name,
        "aliases": build_aliases()
    }

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    # Print summary
    print(f"Park inventory built successfully!")
    print(f"  Species: {len(output_species)}")
    print(f"  Named individuals: {len(animals_by_name)}")
    print(f"  Output: {output_path}")

    # Print some examples
    print("\nSample species:")
    for species in list(output_species.keys())[:5]:
        data = output_species[species]
        names = [i["name"] for i in data["individuals"][:3]]
        print(f"  {species}: {data['count']} animals ({', '.join(names)}...)")

    return 0


if __name__ == "__main__":
    exit(main())

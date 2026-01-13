"""
Zoo Q&A Chatbot - Curated Knowledge Sources
Trusted sources for animal content (6-12 year old audience)

Sources verified working as of January 2026:
- National Geographic Kids (primary)
- Ducksters (kid-focused, ages 8-14)
- Simple Wikipedia (reliable backup)
- SeaWorld (marine animals)
- San Diego Zoo (verified URLs only)
"""

# ============================================================
# NATIONAL GEOGRAPHIC KIDS - Primary Source (Kid-focused)
# ============================================================
NAT_GEO_KIDS = [
    # Mammals - African
    "https://kids.nationalgeographic.com/animals/mammals/facts/african-elephant",
    "https://kids.nationalgeographic.com/animals/mammals/facts/lion",
    "https://kids.nationalgeographic.com/animals/mammals/facts/giraffe",
    "https://kids.nationalgeographic.com/animals/mammals/facts/cheetah",
    "https://kids.nationalgeographic.com/animals/mammals/facts/gorilla",
    "https://kids.nationalgeographic.com/animals/mammals/facts/hippopotamus",
    "https://kids.nationalgeographic.com/animals/mammals/facts/zebra",
    "https://kids.nationalgeographic.com/animals/mammals/facts/rhinoceros",
    "https://kids.nationalgeographic.com/animals/mammals/facts/african-wild-dog",
    "https://kids.nationalgeographic.com/animals/mammals/facts/hyena",
    # Mammals - Asian
    "https://kids.nationalgeographic.com/animals/mammals/facts/giant-panda",
    "https://kids.nationalgeographic.com/animals/mammals/facts/tiger",
    "https://kids.nationalgeographic.com/animals/mammals/facts/asian-elephant",
    "https://kids.nationalgeographic.com/animals/mammals/facts/orangutan",
    "https://kids.nationalgeographic.com/animals/mammals/facts/red-panda",
    "https://kids.nationalgeographic.com/animals/mammals/facts/snow-leopard",
    # Mammals - Australian
    "https://kids.nationalgeographic.com/animals/mammals/facts/koala",
    "https://kids.nationalgeographic.com/animals/mammals/facts/kangaroo",
    "https://kids.nationalgeographic.com/animals/mammals/facts/platypus",
    "https://kids.nationalgeographic.com/animals/mammals/facts/tasmanian-devil",
    "https://kids.nationalgeographic.com/animals/mammals/facts/wombat",
    # Mammals - Arctic/Antarctic
    "https://kids.nationalgeographic.com/animals/mammals/facts/polar-bear",
    "https://kids.nationalgeographic.com/animals/mammals/facts/arctic-fox",
    "https://kids.nationalgeographic.com/animals/mammals/facts/wolf",
    # Mammals - Americas
    "https://kids.nationalgeographic.com/animals/mammals/facts/jaguar",
    "https://kids.nationalgeographic.com/animals/mammals/facts/sloth",
    "https://kids.nationalgeographic.com/animals/mammals/facts/grizzly-bear",
    "https://kids.nationalgeographic.com/animals/mammals/facts/black-bear",
    "https://kids.nationalgeographic.com/animals/mammals/facts/moose",
    "https://kids.nationalgeographic.com/animals/mammals/facts/beaver",
    "https://kids.nationalgeographic.com/animals/mammals/facts/raccoon",
    # Mammals - Marine
    "https://kids.nationalgeographic.com/animals/mammals/facts/dolphin",
    "https://kids.nationalgeographic.com/animals/mammals/facts/orca",
    "https://kids.nationalgeographic.com/animals/mammals/facts/humpback-whale",
    "https://kids.nationalgeographic.com/animals/mammals/facts/sea-otter",
    "https://kids.nationalgeographic.com/animals/mammals/facts/sea-lion",
    "https://kids.nationalgeographic.com/animals/mammals/facts/walrus",
    # Birds
    "https://kids.nationalgeographic.com/animals/birds/facts/penguin",
    "https://kids.nationalgeographic.com/animals/birds/facts/bald-eagle",
    "https://kids.nationalgeographic.com/animals/birds/facts/flamingo",
    "https://kids.nationalgeographic.com/animals/birds/facts/owl",
    "https://kids.nationalgeographic.com/animals/birds/facts/parrot",
    "https://kids.nationalgeographic.com/animals/birds/facts/peacock",
    "https://kids.nationalgeographic.com/animals/birds/facts/toucan",
    "https://kids.nationalgeographic.com/animals/birds/facts/ostrich",
    "https://kids.nationalgeographic.com/animals/birds/facts/hummingbird",
    # Reptiles
    "https://kids.nationalgeographic.com/animals/reptiles/facts/sea-turtle",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/komodo-dragon",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/crocodile",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/alligator",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/chameleon",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/iguana",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/anaconda",
    # Fish
    "https://kids.nationalgeographic.com/animals/fish/facts/great-white-shark",
    "https://kids.nationalgeographic.com/animals/fish/facts/clownfish",
    "https://kids.nationalgeographic.com/animals/fish/facts/seahorse",
    # Invertebrates
    "https://kids.nationalgeographic.com/animals/invertebrates/facts/octopus",
    "https://kids.nationalgeographic.com/animals/invertebrates/facts/jellyfish",
    "https://kids.nationalgeographic.com/animals/invertebrates/facts/butterfly",
    "https://kids.nationalgeographic.com/animals/invertebrates/facts/spider",
]

# ============================================================
# DUCKSTERS - Secondary Source (Kid-focused, Ages 8-14)
# ============================================================
DUCKSTERS = [
    # Popular Zoo Animals
    "https://www.ducksters.com/animals/elephant.php",
    "https://www.ducksters.com/animals/lion.php",
    "https://www.ducksters.com/animals/giraffe.php",
    "https://www.ducksters.com/animals/tiger.php",
    "https://www.ducksters.com/animals/bear.php",
    "https://www.ducksters.com/animals/monkey.php",
    "https://www.ducksters.com/animals/gorilla.php",
    "https://www.ducksters.com/animals/chimpanzee.php",
    "https://www.ducksters.com/animals/zebra.php",
    "https://www.ducksters.com/animals/hippo.php",
    "https://www.ducksters.com/animals/rhino.php",
    "https://www.ducksters.com/animals/cheetah.php",
    "https://www.ducksters.com/animals/leopard.php",
    "https://www.ducksters.com/animals/jaguar.php",
    "https://www.ducksters.com/animals/wolf.php",
    "https://www.ducksters.com/animals/fox.php",
    # Australian
    "https://www.ducksters.com/animals/koala.php",
    "https://www.ducksters.com/animals/kangaroo.php",
    "https://www.ducksters.com/animals/platypus.php",
    # Marine
    "https://www.ducksters.com/animals/dolphin.php",
    "https://www.ducksters.com/animals/whale.php",
    "https://www.ducksters.com/animals/shark.php",
    "https://www.ducksters.com/animals/octopus.php",
    "https://www.ducksters.com/animals/penguin.php",
    "https://www.ducksters.com/animals/seal.php",
    # Birds
    "https://www.ducksters.com/animals/eagle.php",
    "https://www.ducksters.com/animals/owl.php",
    "https://www.ducksters.com/animals/parrot.php",
    "https://www.ducksters.com/animals/flamingo.php",
    # Reptiles
    "https://www.ducksters.com/animals/snake.php",
    "https://www.ducksters.com/animals/crocodile.php",
    "https://www.ducksters.com/animals/turtle.php",
    "https://www.ducksters.com/animals/lizard.php",
    # Farm/Pets
    "https://www.ducksters.com/animals/horse.php",
    "https://www.ducksters.com/animals/dog.php",
    "https://www.ducksters.com/animals/cat.php",
    "https://www.ducksters.com/animals/rabbit.php",
]

# ============================================================
# SEAWORLD - Marine & Arctic Animals
# ============================================================
SEAWORLD = [
    # Marine Mammals
    "https://seaworld.org/animals/facts/mammals/bottlenose-dolphin/",
    "https://seaworld.org/animals/facts/mammals/orca/",
    "https://seaworld.org/animals/facts/mammals/california-sea-lion/",
    "https://seaworld.org/animals/facts/mammals/harbor-seal/",
    "https://seaworld.org/animals/facts/mammals/walrus/",
    "https://seaworld.org/animals/facts/mammals/beluga-whale/",
    "https://seaworld.org/animals/facts/mammals/polar-bear/",
    "https://seaworld.org/animals/facts/mammals/sea-otter/",
    "https://seaworld.org/animals/facts/mammals/manatee/",
    # Birds
    "https://seaworld.org/animals/facts/birds/penguins/",
    "https://seaworld.org/animals/facts/birds/flamingos/",
    # Sharks & Fish
    "https://seaworld.org/animals/facts/bony-fish/seahorses/",
    # Reptiles
    "https://seaworld.org/animals/facts/reptiles/sea-turtles/",
]

# ============================================================
# SIMPLE WIKIPEDIA - Reliable Backup (Simple English)
# ============================================================
SIMPLE_WIKIPEDIA = [
    # African Animals
    "https://simple.wikipedia.org/wiki/Elephant",
    "https://simple.wikipedia.org/wiki/Lion",
    "https://simple.wikipedia.org/wiki/Giraffe",
    "https://simple.wikipedia.org/wiki/Zebra",
    "https://simple.wikipedia.org/wiki/Hippopotamus",
    "https://simple.wikipedia.org/wiki/Cheetah",
    "https://simple.wikipedia.org/wiki/Gorilla",
    "https://simple.wikipedia.org/wiki/Meerkat",
    "https://simple.wikipedia.org/wiki/Rhinoceros",
    "https://simple.wikipedia.org/wiki/Lemur",
    # Asian Animals
    "https://simple.wikipedia.org/wiki/Giant_panda",
    "https://simple.wikipedia.org/wiki/Tiger",
    "https://simple.wikipedia.org/wiki/Red_panda",
    "https://simple.wikipedia.org/wiki/Orangutan",
    "https://simple.wikipedia.org/wiki/Komodo_dragon",
    "https://simple.wikipedia.org/wiki/Camel",
    # Australian Animals
    "https://simple.wikipedia.org/wiki/Koala",
    "https://simple.wikipedia.org/wiki/Kangaroo",
    "https://simple.wikipedia.org/wiki/Platypus",
    "https://simple.wikipedia.org/wiki/Emu",
    "https://simple.wikipedia.org/wiki/Wallaby",
    # Arctic Animals
    "https://simple.wikipedia.org/wiki/Polar_bear",
    "https://simple.wikipedia.org/wiki/Penguin",
    "https://simple.wikipedia.org/wiki/Arctic_fox",
    # Americas
    "https://simple.wikipedia.org/wiki/Jaguar",
    "https://simple.wikipedia.org/wiki/Sloth",
    "https://simple.wikipedia.org/wiki/Capybara",
    "https://simple.wikipedia.org/wiki/Llama",
    "https://simple.wikipedia.org/wiki/Alpaca",
    "https://simple.wikipedia.org/wiki/Bald_eagle",
    # Marine
    "https://simple.wikipedia.org/wiki/Dolphin",
    "https://simple.wikipedia.org/wiki/Shark",
    "https://simple.wikipedia.org/wiki/Octopus",
    "https://simple.wikipedia.org/wiki/Sea_turtle",
    # Birds
    "https://simple.wikipedia.org/wiki/Flamingo",
    "https://simple.wikipedia.org/wiki/Owl",
    "https://simple.wikipedia.org/wiki/Parrot",
    "https://simple.wikipedia.org/wiki/Peacock",
    "https://simple.wikipedia.org/wiki/Macaw",
    # Reptiles
    "https://simple.wikipedia.org/wiki/Crocodile",
    "https://simple.wikipedia.org/wiki/Chameleon",
    "https://simple.wikipedia.org/wiki/Tortoise",
    # Petting Zoo / Farm
    "https://simple.wikipedia.org/wiki/Goat",
    "https://simple.wikipedia.org/wiki/Sheep",
    "https://simple.wikipedia.org/wiki/Rabbit",
    "https://simple.wikipedia.org/wiki/Guinea_pig",
    "https://simple.wikipedia.org/wiki/Chicken",
    "https://simple.wikipedia.org/wiki/Duck",
    "https://simple.wikipedia.org/wiki/Horse",
    "https://simple.wikipedia.org/wiki/Donkey",
    "https://simple.wikipedia.org/wiki/Pig",
    "https://simple.wikipedia.org/wiki/Pony",
]

# ============================================================
# SAN DIEGO ZOO - Verified Working URLs Only
# ============================================================
SAN_DIEGO_ZOO = [
    # Verified working (200 status)
    "https://animals.sandiegozoo.org/animals/lion",
    "https://animals.sandiegozoo.org/animals/giraffe",
    "https://animals.sandiegozoo.org/animals/zebra",
    "https://animals.sandiegozoo.org/animals/cheetah",
    "https://animals.sandiegozoo.org/animals/gorilla",
    "https://animals.sandiegozoo.org/animals/giant-panda",
    "https://animals.sandiegozoo.org/animals/tiger",
    "https://animals.sandiegozoo.org/animals/orangutan",
    "https://animals.sandiegozoo.org/animals/red-panda",
    "https://animals.sandiegozoo.org/animals/koala",
    "https://animals.sandiegozoo.org/animals/kangaroo",
    "https://animals.sandiegozoo.org/animals/polar-bear",
    "https://animals.sandiegozoo.org/animals/penguin",
    "https://animals.sandiegozoo.org/animals/flamingo",
    "https://animals.sandiegozoo.org/animals/owl",
    "https://animals.sandiegozoo.org/animals/parrot",
    "https://animals.sandiegozoo.org/animals/lemur",
    "https://animals.sandiegozoo.org/animals/meerkat",
    "https://animals.sandiegozoo.org/animals/sloth",
    "https://animals.sandiegozoo.org/animals/capybara",
    "https://animals.sandiegozoo.org/animals/llama",
    "https://animals.sandiegozoo.org/animals/alpaca",
    "https://animals.sandiegozoo.org/animals/camel",
    "https://animals.sandiegozoo.org/animals/emu",
    "https://animals.sandiegozoo.org/animals/macaw",
    "https://animals.sandiegozoo.org/animals/tortoise",
]

# ============================================================
# LEESBURG ANIMAL PARK - Specific Animals at the Park
# Uses Simple Wikipedia as reliable source
# ============================================================
LEESBURG_PARK_ANIMALS = [
    "https://simple.wikipedia.org/wiki/Lemur",
    "https://simple.wikipedia.org/wiki/Zebra",
    "https://simple.wikipedia.org/wiki/Serval",
    "https://simple.wikipedia.org/wiki/Porcupine",
    "https://simple.wikipedia.org/wiki/Crowned_crane",
    "https://simple.wikipedia.org/wiki/Camel",
    "https://simple.wikipedia.org/wiki/Coati",
    "https://simple.wikipedia.org/wiki/Llama",
    "https://simple.wikipedia.org/wiki/Alpaca",
    "https://simple.wikipedia.org/wiki/Red-tailed_hawk",
    "https://simple.wikipedia.org/wiki/Gibbon",
    "https://simple.wikipedia.org/wiki/Emu",
    "https://simple.wikipedia.org/wiki/Wallaby",
    "https://simple.wikipedia.org/wiki/Pony",
    "https://simple.wikipedia.org/wiki/Raven",
    "https://simple.wikipedia.org/wiki/Guinea_pig",
    "https://simple.wikipedia.org/wiki/Aldabra_giant_tortoise",
    "https://simple.wikipedia.org/wiki/Macaw",
    "https://simple.wikipedia.org/wiki/Goat",
    "https://simple.wikipedia.org/wiki/Sheep",
    "https://simple.wikipedia.org/wiki/Rabbit",
    "https://simple.wikipedia.org/wiki/Chicken",
    "https://simple.wikipedia.org/wiki/Duck",
]

# ============================================================
# COMBINED SOURCES
# ============================================================

# Primary: Kid-focused sources (Nat Geo Kids + Ducksters)
PRIMARY_SOURCES = NAT_GEO_KIDS + DUCKSTERS

# Marine-focused: SeaWorld for ocean animals
MARINE_SOURCES = SEAWORLD

# Backup: Simple Wikipedia (always available)
BACKUP_SOURCES = SIMPLE_WIKIPEDIA

# Park-specific: Animals at Leesburg Animal Park
PARK_SOURCES = LEESBURG_PARK_ANIMALS

# All sources combined (deduplicated by animal name would need processing)
ALL_SOURCES = (
    NAT_GEO_KIDS +
    DUCKSTERS +
    SEAWORLD +
    SAN_DIEGO_ZOO +
    SIMPLE_WIKIPEDIA
)

# Recommended for initial build: Nat Geo Kids (most reliable, kid-focused)
RECOMMENDED_SOURCES = NAT_GEO_KIDS

# Phase 1: Start with Nat Geo Kids (authoritative, kid-focused)
PHASE_1_SOURCES = NAT_GEO_KIDS

# Phase 2: Add Ducksters and SeaWorld
PHASE_2_SOURCES = DUCKSTERS + SEAWORLD

# Phase 3: Add Simple Wikipedia for broader coverage
PHASE_3_SOURCES = SIMPLE_WIKIPEDIA


def get_recommended_urls():
    """Return recommended URLs for initial knowledge base build."""
    return RECOMMENDED_SOURCES


def get_phase1_urls():
    """Return URLs for Phase 1 (Nat Geo Kids - ~60 animals)."""
    return PHASE_1_SOURCES


def get_phase2_urls():
    """Return URLs for Phase 2 (adds Ducksters + SeaWorld)."""
    return PHASE_1_SOURCES + PHASE_2_SOURCES


def get_all_urls():
    """Return all curated animal source URLs."""
    return ALL_SOURCES


def get_park_urls():
    """Return URLs for Leesburg Animal Park specific animals."""
    return PARK_SOURCES


if __name__ == "__main__":
    print(f"Recommended sources (Nat Geo Kids): {len(RECOMMENDED_SOURCES)} URLs")
    print(f"Phase 1 sources: {len(PHASE_1_SOURCES)} URLs")
    print(f"Phase 2 sources: {len(PHASE_1_SOURCES + PHASE_2_SOURCES)} URLs")
    print(f"All sources: {len(ALL_SOURCES)} URLs")
    print(f"Park-specific: {len(PARK_SOURCES)} URLs")
    print("\nSample URLs:")
    for url in RECOMMENDED_SOURCES[:5]:
        print(f"  - {url}")

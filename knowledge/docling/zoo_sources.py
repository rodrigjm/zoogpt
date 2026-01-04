"""
Zoo Q&A Chatbot - Curated Knowledge Sources
Trusted sources for animal content (6-12 year old audience)
"""

# ============================================================
# TRUSTED ANIMAL KNOWLEDGE SOURCES
# ============================================================
# These sources are selected for:
# - Accuracy and authority
# - Age-appropriate content
# - Good structure for extraction
# ============================================================

# San Diego Zoo - Authoritative animal facts
SAN_DIEGO_ZOO_ANIMALS = [
    # African Animals
    "https://animals.sandiegozoo.org/animals/african-elephant",
    "https://animals.sandiegozoo.org/animals/lion",
    "https://animals.sandiegozoo.org/animals/giraffe",
    "https://animals.sandiegozoo.org/animals/zebra",
    "https://animals.sandiegozoo.org/animals/hippopotamus",
    "https://animals.sandiegozoo.org/animals/cheetah",
    "https://animals.sandiegozoo.org/animals/gorilla",
    "https://animals.sandiegozoo.org/animals/african-wild-dog",
    "https://animals.sandiegozoo.org/animals/meerkat",
    "https://animals.sandiegozoo.org/animals/rhinoceros",
    # Asian Animals
    "https://animals.sandiegozoo.org/animals/giant-panda",
    "https://animals.sandiegozoo.org/animals/asian-elephant",
    "https://animals.sandiegozoo.org/animals/tiger",
    "https://animals.sandiegozoo.org/animals/orangutan",
    "https://animals.sandiegozoo.org/animals/red-panda",
    "https://animals.sandiegozoo.org/animals/snow-leopard",
    "https://animals.sandiegozoo.org/animals/komodo-dragon",
    # Australian Animals
    "https://animals.sandiegozoo.org/animals/koala",
    "https://animals.sandiegozoo.org/animals/kangaroo",
    "https://animals.sandiegozoo.org/animals/platypus",
    "https://animals.sandiegozoo.org/animals/tasmanian-devil",
    # Arctic & Antarctic Animals
    "https://animals.sandiegozoo.org/animals/polar-bear",
    "https://animals.sandiegozoo.org/animals/penguin",
    "https://animals.sandiegozoo.org/animals/arctic-fox",
    # North/South American Animals
    "https://animals.sandiegozoo.org/animals/jaguar",
    "https://animals.sandiegozoo.org/animals/sloth",
    "https://animals.sandiegozoo.org/animals/capybara",
    "https://animals.sandiegozoo.org/animals/llama",
    "https://animals.sandiegozoo.org/animals/bald-eagle",
    "https://animals.sandiegozoo.org/animals/grizzly-bear",
    # Ocean Animals
    "https://animals.sandiegozoo.org/animals/sea-otter",
    "https://animals.sandiegozoo.org/animals/sea-lion",
    "https://animals.sandiegozoo.org/animals/dolphin",
    "https://animals.sandiegozoo.org/animals/shark",
    "https://animals.sandiegozoo.org/animals/octopus",
    # Reptiles & Amphibians
    "https://animals.sandiegozoo.org/animals/crocodile",
    "https://animals.sandiegozoo.org/animals/chameleon",
    "https://animals.sandiegozoo.org/animals/anaconda",
    "https://animals.sandiegozoo.org/animals/poison-frog",
    "https://animals.sandiegozoo.org/animals/sea-turtle",
    # Birds
    "https://animals.sandiegozoo.org/animals/flamingo",
    "https://animals.sandiegozoo.org/animals/owl",
    "https://animals.sandiegozoo.org/animals/toucan",
    "https://animals.sandiegozoo.org/animals/parrot",
    "https://animals.sandiegozoo.org/animals/peacock",
    # Insects & Small Creatures
    "https://animals.sandiegozoo.org/animals/butterfly",
    "https://animals.sandiegozoo.org/animals/bee",
    # Pets (for relatability)
    "https://animals.sandiegozoo.org/animals/domestic-dog",
    "https://animals.sandiegozoo.org/animals/domestic-cat",
]

# National Geographic Kids - Already age-appropriate
NAT_GEO_KIDS_ANIMALS = [
    "https://kids.nationalgeographic.com/animals/mammals/facts/african-elephant",
    "https://kids.nationalgeographic.com/animals/mammals/facts/lion",
    "https://kids.nationalgeographic.com/animals/mammals/facts/giraffe",
    "https://kids.nationalgeographic.com/animals/mammals/facts/giant-panda",
    "https://kids.nationalgeographic.com/animals/mammals/facts/polar-bear",
    "https://kids.nationalgeographic.com/animals/mammals/facts/dolphin",
    "https://kids.nationalgeographic.com/animals/mammals/facts/cheetah",
    "https://kids.nationalgeographic.com/animals/mammals/facts/gorilla",
    "https://kids.nationalgeographic.com/animals/mammals/facts/koala",
    "https://kids.nationalgeographic.com/animals/mammals/facts/kangaroo",
    "https://kids.nationalgeographic.com/animals/mammals/facts/tiger",
    "https://kids.nationalgeographic.com/animals/mammals/facts/wolf",
    "https://kids.nationalgeographic.com/animals/mammals/facts/sloth",
    "https://kids.nationalgeographic.com/animals/birds/facts/penguin",
    "https://kids.nationalgeographic.com/animals/birds/facts/bald-eagle",
    "https://kids.nationalgeographic.com/animals/birds/facts/flamingo",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/sea-turtle",
    "https://kids.nationalgeographic.com/animals/reptiles/facts/komodo-dragon",
    "https://kids.nationalgeographic.com/animals/fish/facts/great-white-shark",
    "https://kids.nationalgeographic.com/animals/invertebrates/facts/octopus",
]

# Smithsonian National Zoo - Additional authoritative facts
SMITHSONIAN_ZOO_ANIMALS = [
    "https://nationalzoo.si.edu/animals/african-lion",
    "https://nationalzoo.si.edu/animals/asian-elephant",
    "https://nationalzoo.si.edu/animals/giant-panda",
    "https://nationalzoo.si.edu/animals/great-ape",
    "https://nationalzoo.si.edu/animals/cheetah",
    "https://nationalzoo.si.edu/animals/sloth-bear",
    "https://nationalzoo.si.edu/animals/sea-lion",
    "https://nationalzoo.si.edu/animals/red-panda",
    "https://nationalzoo.si.edu/animals/orangutan",
    "https://nationalzoo.si.edu/animals/flamingo",
]

# Petting Zoo Animals - Farm favorites kids can interact with
PETTING_ZOO_ANIMALS = [
    # Goats & Sheep
    "https://animals.sandiegozoo.org/animals/goat",
    "https://animals.sandiegozoo.org/animals/sheep",
    # Rabbits & Small Animals
    "https://animals.sandiegozoo.org/animals/rabbit",
    "https://animals.sandiegozoo.org/animals/guinea-pig",
    # Farm Birds
    "https://animals.sandiegozoo.org/animals/chicken",
    "https://animals.sandiegozoo.org/animals/duck",
    "https://animals.sandiegozoo.org/animals/turkey",
    # Horses & Ponies
    "https://animals.sandiegozoo.org/animals/horse",
    "https://animals.sandiegozoo.org/animals/donkey",
    # Pigs
    "https://animals.sandiegozoo.org/animals/pig",
    # Cows
    "https://animals.sandiegozoo.org/animals/cow",
    # Alpacas & Llamas (already in main list)
]

# Animals from Leesburg Animal Park map
LEESBURG_PARK_ANIMALS = [
    "https://animals.sandiegozoo.org/animals/lemur",
    "https://animals.sandiegozoo.org/animals/zebra",
    "https://animals.sandiegozoo.org/animals/serval",
    "https://animals.sandiegozoo.org/animals/porcupine",
    "https://animals.sandiegozoo.org/animals/crowned-crane",
    "https://animals.sandiegozoo.org/animals/camel",
    "https://animals.sandiegozoo.org/animals/coatimundi",
    "https://animals.sandiegozoo.org/animals/llama",
    "https://animals.sandiegozoo.org/animals/alpaca",
    "https://animals.sandiegozoo.org/animals/red-tailed-hawk",
    "https://animals.sandiegozoo.org/animals/gibbon",
    "https://animals.sandiegozoo.org/animals/emu",
    "https://animals.sandiegozoo.org/animals/wallaby",
    "https://animals.sandiegozoo.org/animals/pony",
    "https://animals.sandiegozoo.org/animals/raven",
    "https://animals.sandiegozoo.org/animals/guinea-pig",
    "https://animals.sandiegozoo.org/animals/aldabra-tortoise",
    "https://animals.sandiegozoo.org/animals/macaw",
]

# Exotic Animals - Unique species from specialty zoos
EXOTIC_ANIMALS = [
    # Primates
    "https://animals.sandiegozoo.org/animals/lemur",
    "https://animals.sandiegozoo.org/animals/tamarin",
    "https://animals.sandiegozoo.org/animals/capuchin",
    "https://animals.sandiegozoo.org/animals/gibbon",
    # Exotic Cats
    "https://animals.sandiegozoo.org/animals/serval",
    "https://animals.sandiegozoo.org/animals/ocelot",
    "https://animals.sandiegozoo.org/animals/caracal",
    "https://animals.sandiegozoo.org/animals/lynx",
    # Bears
    "https://animals.sandiegozoo.org/animals/sun-bear",
    "https://animals.sandiegozoo.org/animals/spectacled-bear",
    # Unique Mammals
    "https://animals.sandiegozoo.org/animals/binturong",
    "https://animals.sandiegozoo.org/animals/coatimundi",
    "https://animals.sandiegozoo.org/animals/kinkajou",
    "https://animals.sandiegozoo.org/animals/fennec-fox",
    "https://animals.sandiegozoo.org/animals/wallaby",
    "https://animals.sandiegozoo.org/animals/wombat",
    # Reptiles
    "https://animals.sandiegozoo.org/animals/iguana",
    "https://animals.sandiegozoo.org/animals/python",
    "https://animals.sandiegozoo.org/animals/boa",
    "https://animals.sandiegozoo.org/animals/gecko",
    "https://animals.sandiegozoo.org/animals/tortoise",
    "https://animals.sandiegozoo.org/animals/alligator",
    # Exotic Birds
    "https://animals.sandiegozoo.org/animals/macaw",
    "https://animals.sandiegozoo.org/animals/cockatoo",
    "https://animals.sandiegozoo.org/animals/hornbill",
    "https://animals.sandiegozoo.org/animals/kookaburra",
    "https://animals.sandiegozoo.org/animals/emu",
    "https://animals.sandiegozoo.org/animals/ostrich",
    "https://animals.sandiegozoo.org/animals/cassowary",
    # Aquatic/Semi-aquatic
    "https://animals.sandiegozoo.org/animals/otter",
    "https://animals.sandiegozoo.org/animals/beaver",
    "https://animals.sandiegozoo.org/animals/hippo",
    # African Wildlife
    "https://animals.sandiegozoo.org/animals/hyena",
    "https://animals.sandiegozoo.org/animals/warthog",
    "https://animals.sandiegozoo.org/animals/okapi",
    "https://animals.sandiegozoo.org/animals/aardvark",
    # South American
    "https://animals.sandiegozoo.org/animals/anteater",
    "https://animals.sandiegozoo.org/animals/armadillo",
    "https://animals.sandiegozoo.org/animals/tapir",
    # Wolves & Canids
    "https://animals.sandiegozoo.org/animals/wolf",
    "https://animals.sandiegozoo.org/animals/coyote",
    "https://animals.sandiegozoo.org/animals/dingo",
]

# Combine all sources
ALL_ANIMAL_SOURCES = (
    SAN_DIEGO_ZOO_ANIMALS +
    NAT_GEO_KIDS_ANIMALS +
    SMITHSONIAN_ZOO_ANIMALS +
    PETTING_ZOO_ANIMALS +
    LEESBURG_PARK_ANIMALS +
    EXOTIC_ANIMALS
)

# Phase 1: Start with ~50 most popular animals (remove duplicates by topic)
PHASE_1_SOURCES = SAN_DIEGO_ZOO_ANIMALS[:50]

# Phase 2: Add petting zoo, Leesburg park animals, and exotics
PHASE_2_SOURCES = PETTING_ZOO_ANIMALS + LEESBURG_PARK_ANIMALS + EXOTIC_ANIMALS

# Expanded sources for full knowledge base
EXPANDED_SOURCES = list(set(
    SAN_DIEGO_ZOO_ANIMALS +
    PETTING_ZOO_ANIMALS +
    LEESBURG_PARK_ANIMALS +
    EXOTIC_ANIMALS
))

# Animal categories for organizing content
ANIMAL_CATEGORIES = {
    "african": ["elephant", "lion", "giraffe", "zebra", "hippo", "cheetah", "gorilla"],
    "asian": ["panda", "tiger", "orangutan", "red-panda", "snow-leopard"],
    "australian": ["koala", "kangaroo", "platypus"],
    "arctic": ["polar-bear", "penguin", "arctic-fox"],
    "ocean": ["dolphin", "shark", "octopus", "sea-turtle", "sea-otter"],
    "birds": ["eagle", "flamingo", "owl", "toucan", "parrot", "peacock"],
    "reptiles": ["crocodile", "chameleon", "snake", "komodo-dragon"],
    "pets": ["dog", "cat", "hamster", "rabbit"],
}


def get_phase1_urls():
    """Return URLs for Phase 1 knowledge base (50 animals)."""
    return PHASE_1_SOURCES


def get_expanded_urls():
    """Return expanded URLs including petting zoo, Leesburg park, and exotics."""
    return EXPANDED_SOURCES


def get_all_urls():
    """Return all curated animal source URLs."""
    return ALL_ANIMAL_SOURCES


if __name__ == "__main__":
    print(f"Phase 1 sources: {len(PHASE_1_SOURCES)} URLs")
    print(f"Total sources: {len(ALL_ANIMAL_SOURCES)} URLs")
    print("\nPhase 1 URLs:")
    for url in PHASE_1_SOURCES[:5]:
        print(f"  - {url}")
    print("  ...")

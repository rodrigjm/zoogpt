"""
Content fetcher service for populating KB sources from web and local park data.
"""

import os
import re
import json
import time
import logging
import sqlite3
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

# Park inventory path
PARK_INVENTORY_PATH = os.environ.get(
    "PARK_INVENTORY_PATH",
    str(Path(__file__).parent.parent.parent.parent / "data" / "park_inventory.json")
)

# Popular animals kids love (not at park but educational)
# Sources are tried in order - add kid-friendly fallbacks
POPULAR_ANIMALS = [
    # Big Cats
    {"name": "lion", "display_name": "Lion", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/lion"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/lion/"),
                 ("National Geographic Kids", "https://kids.nationalgeographic.com/animals/mammals/facts/lion"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Lion")]},
    {"name": "tiger", "display_name": "Tiger", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/tiger"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/tiger/"),
                 ("National Geographic Kids", "https://kids.nationalgeographic.com/animals/mammals/facts/tiger"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Tiger")]},
    {"name": "cheetah", "display_name": "Cheetah", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/cheetah"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/cheetah/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Cheetah")]},
    {"name": "leopard", "display_name": "Leopard", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/leopard"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/leopard/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Leopard")]},
    {"name": "jaguar", "display_name": "Jaguar", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/jaguar"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/jaguar/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Jaguar")]},
    # Large Mammals
    {"name": "elephant", "display_name": "Elephant", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/elephant"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/elephant/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Elephant")]},
    {"name": "giraffe", "display_name": "Giraffe", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/giraffe"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/giraffe/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Giraffe")]},
    {"name": "hippopotamus", "display_name": "Hippopotamus", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/hippo"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/hippopotamus/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Hippopotamus")]},
    {"name": "rhinoceros", "display_name": "Rhinoceros", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/rhinoceros"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/rhinoceros/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Rhinoceros")]},
    {"name": "zebra", "display_name": "Zebra", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/zebra"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/zebra/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Zebra")]},
    # Bears
    {"name": "polar_bear", "display_name": "Polar Bear", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/polar-bear"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/polar-bear/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Polar_bear")]},
    {"name": "grizzly_bear", "display_name": "Grizzly Bear", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/grizzly-bear"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/grizzly-bear/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Grizzly_bear")]},
    {"name": "panda", "display_name": "Giant Panda", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/giant-panda"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/giant-panda/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Giant_panda")]},
    # Primates
    {"name": "gorilla", "display_name": "Gorilla", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/gorilla"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/gorilla/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Gorilla")]},
    {"name": "chimpanzee", "display_name": "Chimpanzee", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/chimpanzee"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/chimpanzee/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Chimpanzee")]},
    {"name": "orangutan", "display_name": "Orangutan", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/orangutan"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/orangutan/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Orangutan")]},
    # Marine/Aquatic
    {"name": "dolphin", "display_name": "Dolphin", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/dolphin"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/dolphin/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Dolphin")]},
    {"name": "whale", "display_name": "Whale", "category": "popular",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/whale/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Whale")]},
    {"name": "shark", "display_name": "Shark", "category": "popular",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/shark/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Shark")]},
    {"name": "sea_turtle", "display_name": "Sea Turtle", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/sea-turtle"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/sea-turtle/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Sea_turtle")]},
    {"name": "penguin", "display_name": "Penguin", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/penguin"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/penguin/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Penguin")]},
    {"name": "seal", "display_name": "Seal", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/seal-sea-lion"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/seal/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Pinniped")]},
    {"name": "otter", "display_name": "Otter", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/otter"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/otter/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Otter")]},
    # Other Kid Favorites
    {"name": "wolf", "display_name": "Wolf", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/wolf"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/wolf/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Wolf")]},
    {"name": "fox", "display_name": "Fox", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/fox"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/fox/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Fox")]},
    {"name": "kangaroo", "display_name": "Kangaroo", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/kangaroo"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/kangaroo/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Kangaroo")]},
    {"name": "koala", "display_name": "Koala", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/koala"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/koala/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Koala")]},
    {"name": "crocodile", "display_name": "Crocodile", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/crocodilian"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/crocodile/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Crocodile")]},
    {"name": "alligator", "display_name": "Alligator", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/american-alligator"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/alligator/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Alligator")]},
    {"name": "snake", "display_name": "Snake", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/snake"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/snake/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Snake")]},
    {"name": "owl", "display_name": "Owl", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/owl"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/owl/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Owl")]},
    # Fixed: San Diego Zoo uses "bald-eagle" not "eagle"
    {"name": "eagle", "display_name": "Eagle", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/bald-eagle"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/bald-eagle/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Eagle")]},
    {"name": "flamingo", "display_name": "Flamingo", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/flamingo"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/flamingo/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Flamingo")]},
    {"name": "parrot", "display_name": "Parrot", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/parrot"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/parrot/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Parrot")]},
    # Dinosaur-adjacent (kids love these)
    {"name": "komodo_dragon", "display_name": "Komodo Dragon", "category": "popular",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/komodo-dragon"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/komodo-dragon/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Komodo_dragon")]},
]

# Park animals with their web sources (Wikipedia added as reliable fallback)
PARK_ANIMALS = [
    {"name": "cotton_top_tamarin", "display_name": "Cotton-top Tamarin", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/cotton-top-tamarin"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/cotton-top-tamarin/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Cotton-top_tamarin")]},
    {"name": "common_marmoset", "display_name": "Common Marmoset", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/marmoset/"),
                 ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/marmoset"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Common_marmoset")]},
    {"name": "squirrel_monkey", "display_name": "Squirrel Monkey", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/squirrel-monkey"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/squirrel-monkey/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Squirrel_monkey")]},
    {"name": "african_crested_porcupine", "display_name": "African Crested Porcupine", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/porcupine"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/crested-porcupine/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Crested_porcupine")]},
    {"name": "serval", "display_name": "Serval", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/serval"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/serval/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Serval")]},
    {"name": "lar_gibbon", "display_name": "Lar Gibbon (White-handed Gibbon)", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/gibbon"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/gibbon/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Lar_gibbon")]},
    {"name": "chinchilla", "display_name": "Chinchilla", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/chinchilla/"),
                 ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/chinchilla"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Chinchilla")]},
    {"name": "laughing_kookaburra", "display_name": "Laughing Kookaburra", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/kookaburra"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/kookaburra/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Laughing_kookaburra")]},
    {"name": "patagonian_mara", "display_name": "Patagonian Mara (Cavy)", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/patagonian-mara/"),
                 ("San Diego Zoo", "https://animals.sandiegozoo.org/animals/patagonian-mara"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Patagonian_mara")]},
    {"name": "coatimundi", "display_name": "Coatimundi (Coati)", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/coati"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/coatimundi/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Coati")]},
    {"name": "nilgai", "display_name": "Nilgai (Blue Bull Antelope)", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/nilgai/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Nilgai")]},
    {"name": "zebu", "display_name": "Zebu (Indian Humped Cattle)", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/zebu-cattle/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Zebu")]},
    {"name": "crowned_crane", "display_name": "East African Crowned Crane", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/crowned-crane"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/crowned-crane/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Grey_crowned_crane")]},
    {"name": "indian_peafowl", "display_name": "Indian Peafowl (Peacock)", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/peafowl"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/peacock/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Indian_peafowl")]},
    {"name": "wild_turkey", "display_name": "Wild Turkey", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/turkey/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Wild_turkey")]},
    {"name": "common_raven", "display_name": "Common Raven", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/raven/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Common_raven")]},
    {"name": "fallow_deer", "display_name": "Fallow Deer", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/fallow-deer/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Fallow_deer")]},
    {"name": "four_toed_hedgehog", "display_name": "Four-toed Hedgehog", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/hedgehog"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/hedgehog/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Four-toed_hedgehog")]},
    {"name": "ball_python", "display_name": "Ball Python (Royal Python)", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/ball-python"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/ball-python/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Ball_python")]},
    {"name": "indigo_snake", "display_name": "Eastern Indigo Snake", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/indigo-snake/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Eastern_indigo_snake")]},
    {"name": "whites_tree_frog", "display_name": "White's Tree Frog", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/whites-tree-frog/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Australian_green_tree_frog")]},
    {"name": "leaf_tailed_gecko", "display_name": "Leaf-tailed Gecko", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/leaf-tailed-gecko/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Uroplatus")]},
    {"name": "blue_tongued_skink", "display_name": "Blue-tongued Skink", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/blue-tongued-skink"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/blue-tongued-skink/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Blue-tongued_skink")]},
    {"name": "argentine_tegu", "display_name": "Argentine Black and White Tegu", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/tegu-lizard/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Argentine_black_and_white_tegu")]},
    {"name": "emperor_scorpion", "display_name": "Emperor Scorpion", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/emperor-scorpion/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Emperor_scorpion")]},
    {"name": "anatolian_shepherd", "display_name": "Anatolian Shepherd Dog", "category": "park_animal",
     "sources": [("A-Z Animals", "https://a-z-animals.com/animals/anatolian-shepherd-dog/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Anatolian_Shepherd")]},
    {"name": "ring_tailed_lemur", "display_name": "Ring-tailed Lemur", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/ring-tailed-lemur"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/ring-tailed-lemur/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Ring-tailed_lemur")]},
    {"name": "black_and_white_ruffed_lemur", "display_name": "Black-and-white Ruffed Lemur", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/ruffed-lemur"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/black-and-white-ruffed-lemur/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Black-and-white_ruffed_lemur")]},
    {"name": "red_footed_tortoise", "display_name": "Red-footed Tortoise", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/red-footed-tortoise"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/red-footed-tortoise/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Red-footed_tortoise")]},
    {"name": "african_spurred_tortoise", "display_name": "African Spurred Tortoise (Sulcata)", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/african-spurred-tortoise"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/sulcata-tortoise/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/African_spurred_tortoise")]},
    {"name": "aldabra_giant_tortoise", "display_name": "Aldabra Giant Tortoise", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/aldabra-tortoise"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/aldabra-giant-tortoise/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Aldabra_giant_tortoise")]},
    {"name": "two_toed_sloth", "display_name": "Linnaeus's Two-toed Sloth", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/two-toed-sloth"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/two-toed-sloth/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Linnaeus%27s_two-toed_sloth")]},
    {"name": "bennetts_wallaby", "display_name": "Bennett's Wallaby (Red-necked Wallaby)", "category": "park_animal",
     "sources": [("San Diego Zoo", "https://animals.sandiegozoo.org/animals/wallaby"),
                 ("A-Z Animals", "https://a-z-animals.com/animals/wallaby/"),
                 ("Wikipedia", "https://en.wikipedia.org/wiki/Red-necked_wallaby")]},
]


def fetch_url(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch URL content."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8')
    except (URLError, HTTPError) as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML."""
    # Remove script, style, nav, header, footer
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Convert elements to text
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<p[^>]*>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<h[1-6][^>]*>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</h[1-6]>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<li[^>]*>', '\n• ', html, flags=re.IGNORECASE)

    # Remove remaining tags
    html = re.sub(r'<[^>]+>', ' ', html)

    # Clean up entities and whitespace
    html = re.sub(r'&nbsp;', ' ', html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'&lt;', '<', html)
    html = re.sub(r'&gt;', '>', html)
    html = re.sub(r'&#\d+;', '', html)
    html = re.sub(r'&\w+;', '', html)
    html = re.sub(r'\s+', ' ', html)
    html = re.sub(r'\n\s*\n', '\n\n', html)

    return html.strip()


class ContentFetcher:
    """Service for fetching and populating KB content from web and local sources."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.park_inventory = self._load_park_inventory()

    def _load_park_inventory(self) -> dict:
        """Load park inventory JSON if available."""
        try:
            # Try multiple paths
            paths_to_try = [
                PARK_INVENTORY_PATH,
                "/app/data/park_inventory.json",  # Docker path
                Path(__file__).parent.parent.parent.parent / "data" / "park_inventory.json",
            ]
            logger.info(f"Looking for park inventory in: {paths_to_try}")
            for path in paths_to_try:
                p = Path(path) if isinstance(path, str) else path
                if p.exists():
                    with open(p) as f:
                        data = json.load(f)
                        species_count = len(data.get("animals_by_species", {}))
                        logger.info(f"Loaded park inventory from {p} ({species_count} species)")
                        return data
                else:
                    logger.debug(f"Park inventory not found at: {p}")
            logger.error("CRITICAL: Park inventory not found in any path - personalized animal info will be missing!")
            return {}
        except Exception as e:
            logger.error(f"Failed to load park inventory: {e}")
            return {}

    def generate_park_animal_content(self, species: str, species_data: dict) -> str:
        """
        Generate rich content about a species from park inventory data.
        Includes individual animal names, birthdays, locations.
        """
        individuals = species_data.get("individuals", [])
        locations = species_data.get("locations", [])
        count = species_data.get("count", len(individuals))

        lines = [
            f"# {species.title()} at Leesburg Animal Park",
            f"",
            f"Leesburg Animal Park has {count} {species}(s) that visitors can see and interact with.",
            f"",
        ]

        if locations:
            lines.append(f"## Where to Find {species.title()}s")
            lines.append(f"You can find {species}s at: {', '.join(locations)}.")
            lines.append("")

        if individuals:
            lines.append(f"## Meet Our {species.title()}s")
            lines.append("")

            for animal in individuals:
                name = animal.get("name", "Unknown")
                gender = animal.get("gender", "")
                birthdate = animal.get("birthdate", "")
                breed = animal.get("breed", "")
                location = animal.get("location", "")

                lines.append(f"### {name}")
                if gender:
                    lines.append(f"- Gender: {gender}")
                if birthdate:
                    lines.append(f"- Birthday: {birthdate}")
                if breed:
                    lines.append(f"- Breed: {breed}")
                if location:
                    lines.append(f"- Location: {location}")
                lines.append("")

        return "\n".join(lines)

    def sync_park_inventory(self) -> tuple[int, int]:
        """
        Sync park inventory data into kb_sources.
        Creates/updates animals and adds park-specific content.

        Returns:
            Tuple of (animals_synced, sources_added)
        """
        if not self.park_inventory:
            logger.warning("No park inventory to sync")
            return (0, 0)

        animals_by_species = self.park_inventory.get("animals_by_species", {})
        logger.info(f"Syncing {len(animals_by_species)} species from park inventory...")

        synced = 0
        sources_added = 0

        for species, species_data in animals_by_species.items():
            if not species_data.get("at_park", False):
                continue

            # Normalize species name
            animal_name = species.lower().replace(" ", "_").replace("-", "_")
            display_name = species.title()

            # Ensure animal exists
            animal_id = self._ensure_animal_exists_simple(animal_name, display_name, "park_animal")

            # Check if we already have park inventory source
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id FROM kb_sources WHERE animal_id = ? AND title = 'Leesburg Animal Park'",
                (animal_id,)
            )
            existing = cursor.fetchone()

            # Generate content from park data
            content = self.generate_park_animal_content(species, species_data)

            if existing:
                # Update existing source
                cursor.execute(
                    "UPDATE kb_sources SET content = ? WHERE id = ?",
                    (content, existing[0])
                )
            else:
                # Add new source
                cursor.execute(
                    "INSERT INTO kb_sources (animal_id, title, url, content) VALUES (?, ?, ?, ?)",
                    (animal_id, "Leesburg Animal Park", None, content)
                )
                cursor.execute(
                    "UPDATE kb_animals SET source_count = source_count + 1 WHERE id = ?",
                    (animal_id,)
                )
                sources_added += 1

            self.conn.commit()
            synced += 1
            logger.info(f"  Synced: {display_name} ({len(species_data.get('individuals', []))} individuals)")

        return (synced, sources_added)

    def _ensure_animal_exists_simple(self, name: str, display_name: str, category: str) -> int:
        """Ensure animal exists, return ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM kb_animals WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            "INSERT INTO kb_animals (name, display_name, category, source_count) VALUES (?, ?, ?, 0)",
            (name, display_name, category)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_animals_without_external_sources(self) -> list[dict]:
        """Get animals from PARK_ANIMALS + POPULAR_ANIMALS that need external sources."""
        cursor = self.conn.cursor()

        # Get existing animals with external sources (not park inventory)
        cursor.execute("""
            SELECT a.name, COUNT(s.id) as source_count
            FROM kb_animals a
            LEFT JOIN kb_sources s ON a.id = s.animal_id AND s.title != 'Leesburg Animal Park'
            GROUP BY a.name
        """)
        existing = {row[0]: row[1] for row in cursor.fetchall()}

        # Combine park animals and popular animals
        all_animals = PARK_ANIMALS + POPULAR_ANIMALS

        # Find animals that need external content
        animals_to_fetch = []
        for animal in all_animals:
            name = animal["name"]
            if name not in existing or existing[name] == 0:
                animals_to_fetch.append(animal)

        return animals_to_fetch

    def ensure_animal_exists(self, animal: dict) -> int:
        """Ensure animal exists in kb_animals, return ID."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT id FROM kb_animals WHERE name = ?", (animal["name"],))
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            "INSERT INTO kb_animals (name, display_name, category, source_count) VALUES (?, ?, ?, 0)",
            (animal["name"], animal["display_name"], animal["category"])
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_source(self, animal_id: int, title: str, url: str, content: str):
        """Add source to kb_sources."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO kb_sources (animal_id, title, url, content) VALUES (?, ?, ?, ?)",
            (animal_id, title, url, content)
        )
        cursor.execute(
            "UPDATE kb_animals SET source_count = source_count + 1 WHERE id = ?",
            (animal_id,)
        )
        self.conn.commit()

    def fetch_all_content(self) -> dict:
        """
        Complete content sync: park inventory + external sources.

        Returns:
            Dict with stats: {park_synced, park_sources, external_added, external_failed}
        """
        stats = {
            "park_synced": 0,
            "park_sources": 0,
            "external_added": 0,
            "external_failed": 0,
        }

        # 1. Sync park inventory (individual animals with names, birthdays, locations)
        logger.info("=== Syncing Park Inventory ===")
        park_synced, park_sources = self.sync_park_inventory()
        stats["park_synced"] = park_synced
        stats["park_sources"] = park_sources

        # 2. Fetch external sources for general species info
        logger.info("=== Fetching External Sources ===")
        ext_added, ext_failed = self.fetch_missing_content()
        stats["external_added"] = ext_added
        stats["external_failed"] = ext_failed

        return stats

    def fetch_missing_content(self) -> tuple[int, int]:
        """
        Fetch content for animals without external sources.

        Returns:
            Tuple of (animals_added, animals_failed)
        """
        animals_to_fetch = self.get_animals_without_external_sources()

        if not animals_to_fetch:
            logger.info("All animals already have external sources")
            return (0, 0)

        logger.info(f"Fetching external content for {len(animals_to_fetch)} animals...")

        added = 0
        failed = 0

        for animal in animals_to_fetch:
            logger.info(f"Fetching: {animal['display_name']}")

            content = None
            source_title = None
            source_url = None

            for title, url in animal["sources"]:
                html = fetch_url(url)
                if html:
                    text = extract_text_from_html(html)
                    if len(text) > 200:
                        content = text[:8000]  # Limit size
                        source_title = title
                        source_url = url
                        logger.info(f"  Got {len(content)} chars from {title}")
                        break

                time.sleep(0.3)  # Rate limiting

            if content:
                animal_id = self.ensure_animal_exists(animal)
                self.add_source(animal_id, source_title, source_url, content)
                added += 1
            else:
                logger.warning(f"  No content found for {animal['display_name']}")
                failed += 1

        return (added, failed)

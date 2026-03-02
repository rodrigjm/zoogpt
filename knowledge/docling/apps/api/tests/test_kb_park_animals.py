"""Integration tests for new park animal KB entries.

Tests that new species added to park_inventory.json and LanceDB work correctly
with the RAG system, including:
- New species queries (cotton-top tamarins, servals, African porcupines)
- Location integration (PARK INFO includes location)
- Individual name recognition (Ziggy, Rosie Rey, etc.)
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.rag import RAGService


@pytest.fixture
def sample_kb_data():
    """Sample park inventory with new species."""
    return {
        "animals_by_species": {
            "cotton-top tamarin": {
                "at_park": True,
                "count": 2,
                "locations": ["Building - Window Exhibits"],
                "individuals": [
                    {"name": "Ziggy", "breed": "Cotton-top Tamarin", "location": "Building - Window Exhibits", "gender": "Male"}
                ]
            },
            "serval": {
                "at_park": True,
                "count": 1,
                "locations": ["Building - Window Exhibits"],
                "individuals": [
                    {"name": "Leo", "breed": "Serval", "location": "Building - Window Exhibits", "gender": "Male"}
                ]
            },
            "african porcupine": {
                "at_park": True,
                "count": 2,
                "locations": ["Building - Upper Level"],
                "individuals": [
                    {"name": "Rosie Rey", "breed": "African Porcupine", "location": "Building - Upper Level", "gender": "Female"}
                ]
            }
        },
        "animals_by_name": {
            "ziggy": {"species": "cotton-top tamarin", "type": "Cotton-top Tamarin", "location": "Building - Window Exhibits"},
            "leo": {"species": "serval", "type": "Serval", "location": "Building - Window Exhibits"},
            "rosie rey": {"species": "african porcupine", "type": "African Porcupine", "location": "Building - Upper Level"}
        },
        "aliases": {
            "cotton-top tamarin": ["tamarin"],
            "african porcupine": ["porcupine"]
        }
    }


@pytest.fixture
def mock_lancedb_results():
    """Mock LanceDB search results for new species."""
    return {
        "cotton-top tamarin": [
            {
                "text": "Cotton-top tamarins are small primates native to Colombia. They have distinctive white crests.",
                "metadata": {"animal_name": "Cotton-top Tamarin", "title": "Primates", "url": ""},
                "_distance": 0.2
            },
            {
                "text": "These tamarins live in family groups and communicate with high-pitched whistles.",
                "metadata": {"animal_name": "Cotton-top Tamarin", "title": "Behavior", "url": ""},
                "_distance": 0.25
            }
        ],
        "serval": [
            {
                "text": "Servals are medium-sized African wild cats with distinctive large ears and spotted coats.",
                "metadata": {"animal_name": "Serval", "title": "Wild Cats", "url": ""},
                "_distance": 0.18
            },
            {
                "text": "Servals primarily hunt rodents and birds, using their excellent hearing to locate prey.",
                "metadata": {"animal_name": "Serval", "title": "Diet", "url": ""},
                "_distance": 0.22
            }
        ],
        "african porcupine": [
            {
                "text": "African porcupines can grow up to 3 feet long and weigh up to 60 pounds.",
                "metadata": {"animal_name": "African Porcupine", "title": "Size", "url": ""},
                "_distance": 0.15
            },
            {
                "text": "Porcupines are herbivores that eat roots, bark, and fallen fruits.",
                "metadata": {"animal_name": "African Porcupine", "title": "Diet", "url": ""},
                "_distance": 0.2
            }
        ]
    }


@pytest.fixture
def mock_rag_service(sample_kb_data, mock_lancedb_results):
    """Create a RAGService with mocked dependencies."""
    with patch('app.services.rag.lancedb.connect') as mock_connect, \
         patch('app.services.rag.OpenAI') as mock_openai, \
         patch('builtins.open', create=True) as mock_file, \
         patch('pathlib.Path.exists', return_value=True):

        # Mock LanceDB table
        mock_table = MagicMock()
        mock_db = MagicMock()
        mock_db.open_table.return_value = mock_table
        mock_connect.return_value = mock_db

        # Mock file read for park_inventory.json
        mock_file.return_value.__enter__.return_value.read.return_value = ""

        # Create RAG service
        service = RAGService()
        service._park_inventory = sample_kb_data
        service._table = mock_table

        # Store mock results for dynamic lookup
        service._mock_results = mock_lancedb_results

        yield service, mock_table


def test_new_species_cotton_top_tamarin(mock_rag_service):
    """Test that cotton-top tamarin queries return relevant KB content."""
    service, mock_table = mock_rag_service
    query = "Tell me about cotton-top tamarins"

    # Mock LanceDB search
    mock_search = MagicMock()
    mock_table.search.return_value = mock_search
    mock_search.limit.return_value.to_list.return_value = service._mock_results["cotton-top tamarin"]

    # Execute search
    context, sources, confidence = service.search_context(query, num_results=5)

    # Verify search was called
    mock_table.search.assert_called_once_with(query)

    # Verify results contain expected content
    assert len(sources) == 2
    assert sources[0]["animal"] == "Cotton-top Tamarin"
    assert "primates" in context.lower() or "white crests" in context.lower()
    assert confidence > 0.0

    # Verify park context is included
    assert "[PARK INFO:" in context
    assert "Building - Window Exhibits" in context


def test_new_species_serval_diet(mock_rag_service):
    """Test that serval diet queries return relevant KB content."""
    service, mock_table = mock_rag_service
    query = "What do servals eat?"

    # Mock LanceDB search
    mock_search = MagicMock()
    mock_table.search.return_value = mock_search
    mock_search.limit.return_value.to_list.return_value = service._mock_results["serval"]

    # Execute search
    context, sources, confidence = service.search_context(query, num_results=5)

    # Verify results contain diet information
    assert len(sources) == 2
    assert "serval" in context.lower()
    assert "rodents" in context.lower() or "birds" in context.lower()

    # Verify park context
    assert "[PARK INFO:" in context
    assert "Building - Window Exhibits" in context


def test_new_species_african_porcupine_size(mock_rag_service):
    """Test that African porcupine size queries return relevant KB content."""
    service, mock_table = mock_rag_service
    query = "How big do African porcupines get?"

    # Mock LanceDB search
    mock_search = MagicMock()
    mock_table.search.return_value = mock_search
    mock_search.limit.return_value.to_list.return_value = service._mock_results["african porcupine"]

    # Execute search
    context, sources, confidence = service.search_context(query, num_results=5)

    # Verify results contain size information
    assert len(sources) == 2
    assert "porcupine" in context.lower()
    assert "feet" in context.lower() or "pounds" in context.lower()

    # Verify park context
    assert "[PARK INFO:" in context
    assert "Building - Upper Level" in context


def test_location_included_in_park_info(mock_rag_service):
    """Test that PARK INFO includes location for park animals."""
    service, _ = mock_rag_service

    # Test species-level context
    park_context = service._get_park_context("cotton-top tamarin")

    assert park_context is not None
    assert "[PARK INFO:" in park_context
    assert "Leesburg Animal Park" in park_context
    assert "Building - Window Exhibits" in park_context
    assert "Ziggy" in park_context


def test_individual_name_ziggy(mock_rag_service):
    """Test that individual name 'Ziggy' resolves with location."""
    service, _ = mock_rag_service
    query = "Who is Ziggy?"

    # Check individual name lookup
    name_context = service._check_individual_name(query)

    assert name_context is not None
    assert "[PARK INFO:" in name_context
    assert "Ziggy" in name_context
    assert "Cotton-top Tamarin" in name_context or "Cotton-top tamarin" in name_context
    assert "Building - Window Exhibits" in name_context


def test_individual_name_rosie_rey(mock_rag_service):
    """Test that individual name 'Rosie Rey' resolves with location."""
    service, _ = mock_rag_service
    query = "Tell me about Rosie Rey"

    # Check individual name lookup
    name_context = service._check_individual_name(query)

    assert name_context is not None
    assert "[PARK INFO:" in name_context
    assert "Rosie Rey" in name_context
    assert "African Porcupine" in name_context or "porcupine" in name_context.lower()
    assert "Building - Upper Level" in name_context


def test_alias_recognition_tamarin(mock_rag_service):
    """Test that species aliases (e.g., 'tamarin') resolve correctly."""
    service, _ = mock_rag_service

    # Test alias lookup
    park_context = service._get_park_context("tamarin")

    assert park_context is not None
    assert "[PARK INFO:" in park_context
    assert "cotton-top tamarin" in park_context.lower()
    assert "Building - Window Exhibits" in park_context


def test_alias_recognition_porcupine(mock_rag_service):
    """Test that 'porcupine' alias resolves to 'african porcupine'."""
    service, _ = mock_rag_service

    # Test alias lookup
    park_context = service._get_park_context("porcupine")

    assert park_context is not None
    assert "[PARK INFO:" in park_context
    assert "african porcupine" in park_context.lower()
    assert "Building - Upper Level" in park_context


def test_species_not_at_park(mock_rag_service):
    """Test that species not in park_inventory.json return None for park context."""
    service, _ = mock_rag_service

    # Test non-existent species
    park_context = service._get_park_context("elephant")

    assert park_context is None


def test_individual_name_not_found(mock_rag_service):
    """Test that unknown individual names return None."""
    service, _ = mock_rag_service
    query = "Who is Bob?"

    # Check individual name lookup
    name_context = service._check_individual_name(query)

    assert name_context is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for park inventory integration in RAG service."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from app.services.rag import RAGService


# Test data fixture
@pytest.fixture
def sample_park_inventory():
    """Sample park inventory data for testing."""
    return {
        "animals_by_species": {
            "goat": {
                "at_park": True,
                "count": 16,
                "locations": ["Contact Area", "Barn"],
                "individuals": [
                    {"name": "Rue", "breed": "African Pygmy", "location": "Contact Area", "gender": "Female"},
                    {"name": "Taffy", "breed": "Goat", "location": "Contact Area", "gender": "Female"},
                    {"name": "Morgan", "breed": "Goat", "location": "Barn", "gender": "Female"}
                ]
            },
            "monkey": {
                "at_park": True,
                "count": 4,
                "locations": ["Building - Window Exhibits"],
                "individuals": [
                    {"name": "Ziggy", "breed": "Cotton-top Tamarin", "location": "Building - Window Exhibits", "gender": "Male"}
                ]
            },
            "donkey": {
                "at_park": True,
                "count": 7,
                "locations": ["Barn", "Upper Field", "Zebu Yard"],
                "individuals": [
                    {"name": "Anthony", "breed": "African ass", "location": "Barn", "gender": "Male"},
                    {"name": "Peony", "breed": "Sicilian Dwarf", "location": "Upper Field", "gender": "Female"}
                ]
            }
        },
        "animals_by_name": {
            "ziggy": {"species": "monkey", "type": "Cotton-top Tamarin", "location": "Building - Window Exhibits"},
            "rue": {"species": "goat", "type": "African Pygmy", "location": "Contact Area"},
            "anthony": {"species": "donkey", "type": "African ass", "location": "Barn"}
        },
        "aliases": {
            "monkey": ["tamarin", "marmoset", "squirrel monkey"],
            "goat": ["pygmy goat", "dwarf goat"]
        }
    }


@pytest.fixture
def mock_rag_service(sample_park_inventory):
    """Create a RAGService instance with mocked dependencies."""
    with patch.object(RAGService, 'db', new_callable=lambda: MagicMock()), \
         patch.object(RAGService, 'table', new_callable=lambda: MagicMock()):

        rag = RAGService()
        # Inject test data
        rag._park_inventory = sample_park_inventory
        return rag


class TestGetParkContext:
    """Tests for _get_park_context method."""

    def test_species_match_goat(self, mock_rag_service):
        """Test that species name 'goat' returns correct park context."""
        result = mock_rag_service._get_park_context("goat")

        assert result is not None
        assert "[PARK INFO:" in result
        assert "Leesburg Animal Park has 16 goats" in result
        assert "Rue, Taffy, Morgan" in result
        assert "Contact Area, Barn" in result

    def test_species_match_monkey(self, mock_rag_service):
        """Test that species name 'monkey' returns correct park context."""
        result = mock_rag_service._get_park_context("monkey")

        assert result is not None
        assert "[PARK INFO:" in result
        assert "Leesburg Animal Park has 4 monkeys" in result
        assert "Ziggy" in result
        assert "Building - Window Exhibits" in result

    def test_species_match_case_insensitive(self, mock_rag_service):
        """Test that species matching is case-insensitive."""
        result_lower = mock_rag_service._get_park_context("goat")
        result_upper = mock_rag_service._get_park_context("GOAT")
        result_mixed = mock_rag_service._get_park_context("GoAt")

        assert result_lower == result_upper == result_mixed

    def test_species_match_with_whitespace(self, mock_rag_service):
        """Test that species matching handles whitespace."""
        result = mock_rag_service._get_park_context("  goat  ")

        assert result is not None
        assert "16 goats" in result

    def test_alias_match_tamarin(self, mock_rag_service):
        """Test that alias 'tamarin' resolves to 'monkey'."""
        result = mock_rag_service._get_park_context("tamarin")

        assert result is not None
        assert "[PARK INFO:" in result
        assert "4 monkeys" in result
        assert "Ziggy" in result

    def test_alias_match_multiple_aliases(self, mock_rag_service):
        """Test that multiple aliases for same species work."""
        result_tamarin = mock_rag_service._get_park_context("tamarin")
        result_marmoset = mock_rag_service._get_park_context("marmoset")

        # Both should resolve to monkey and return same context
        assert result_tamarin == result_marmoset
        assert "monkey" in result_tamarin.lower()

    def test_no_match_elephant(self, mock_rag_service):
        """Test that unknown species returns None."""
        result = mock_rag_service._get_park_context("elephant")

        assert result is None

    def test_no_match_empty_string(self, mock_rag_service):
        """Test that empty string returns None."""
        result = mock_rag_service._get_park_context("")

        assert result is None

    def test_singular_count(self, mock_rag_service):
        """Test that singular count doesn't pluralize incorrectly."""
        # Modify inventory to have single monkey
        mock_rag_service._park_inventory["animals_by_species"]["monkey"]["count"] = 1

        result = mock_rag_service._get_park_context("monkey")

        assert "1 monkey!" in result  # Should be singular, not "monkeys"

    def test_names_truncated_to_five(self, mock_rag_service):
        """Test that only first 5 names are included."""
        # Add 10 goats to test truncation
        goat_data = mock_rag_service._park_inventory["animals_by_species"]["goat"]
        goat_data["individuals"] = [
            {"name": f"Goat{i}", "breed": "Test", "location": "Barn", "gender": "Female"}
            for i in range(10)
        ]
        goat_data["count"] = 10

        result = mock_rag_service._get_park_context("goat")

        # Should only include first 5 names
        assert "Goat0" in result
        assert "Goat4" in result
        assert "Goat5" not in result


class TestCheckIndividualName:
    """Tests for _check_individual_name method."""

    def test_individual_name_ziggy(self, mock_rag_service):
        """Test that individual name 'Ziggy' is found in query."""
        result = mock_rag_service._check_individual_name("Who is Ziggy?")

        assert result is not None
        assert "[PARK INFO:" in result
        assert "Ziggy is a Cotton-top Tamarin" in result
        assert "Building - Window Exhibits" in result

    def test_individual_name_rue(self, mock_rag_service):
        """Test that individual name 'Rue' is found in query."""
        result = mock_rag_service._check_individual_name("Tell me about Rue")

        assert result is not None
        assert "Rue is a African Pygmy" in result
        assert "Contact Area" in result

    def test_individual_name_case_insensitive(self, mock_rag_service):
        """Test that name matching is case-insensitive."""
        result_lower = mock_rag_service._check_individual_name("where is ziggy")
        result_upper = mock_rag_service._check_individual_name("WHERE IS ZIGGY")
        result_mixed = mock_rag_service._check_individual_name("Where is ZiGgY")

        # All should find Ziggy
        assert result_lower is not None
        assert result_upper is not None
        assert result_mixed is not None

    def test_individual_name_in_middle_of_query(self, mock_rag_service):
        """Test that name is found even in middle of query."""
        result = mock_rag_service._check_individual_name("I heard Anthony is really friendly!")

        assert result is not None
        assert "Anthony is a African ass" in result

    def test_individual_name_not_found(self, mock_rag_service):
        """Test that unknown name returns None."""
        result = mock_rag_service._check_individual_name("Who is Dumbo?")

        assert result is None

    def test_individual_name_empty_query(self, mock_rag_service):
        """Test that empty query returns None."""
        result = mock_rag_service._check_individual_name("")

        assert result is None

    def test_individual_name_partial_match_not_found(self, mock_rag_service):
        """Test that partial name match doesn't trigger false positive."""
        result = mock_rag_service._check_individual_name("Who is Zig?")

        # "zig" is not in animals_by_name, only "ziggy" is
        assert result is None

    def test_individual_name_format(self, mock_rag_service):
        """Test that returned format is correct with capitalized name."""
        result = mock_rag_service._check_individual_name("who is ziggy")

        # Name should be title-cased in response
        assert "Ziggy is a" in result
        assert "You can find Ziggy at" in result


class TestParkInventoryProperty:
    """Tests for park_inventory lazy-loading property."""

    def test_park_inventory_loads_successfully(self, sample_park_inventory):
        """Test that park inventory loads from file successfully."""
        json_content = json.dumps(sample_park_inventory)

        with patch("builtins.open", mock_open(read_data=json_content)), \
             patch("pathlib.Path.exists", return_value=True):

            rag = RAGService()
            inventory = rag.park_inventory

            assert inventory is not None
            assert "animals_by_species" in inventory
            assert "goat" in inventory["animals_by_species"]

    def test_park_inventory_file_not_found(self):
        """Test that missing file returns empty structure."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            rag = RAGService()
            inventory = rag.park_inventory

            # Should return empty but valid structure
            assert inventory == {"animals_by_species": {}, "animals_by_name": {}, "aliases": {}}

    def test_park_inventory_invalid_json(self):
        """Test that invalid JSON returns empty structure."""
        with patch("builtins.open", mock_open(read_data="invalid json {")):
            rag = RAGService()
            inventory = rag.park_inventory

            # Should return empty but valid structure
            assert inventory == {"animals_by_species": {}, "animals_by_name": {}, "aliases": {}}

    def test_park_inventory_cached(self, sample_park_inventory):
        """Test that park inventory is cached after first load."""
        json_content = json.dumps(sample_park_inventory)

        with patch("builtins.open", mock_open(read_data=json_content)) as mock_file:
            rag = RAGService()

            # First access
            inventory1 = rag.park_inventory
            # Second access
            inventory2 = rag.park_inventory

            # Should be same object (cached)
            assert inventory1 is inventory2

            # File should only be opened once
            assert mock_file.call_count == 1


class TestParkContextFormat:
    """Tests for park context format validation."""

    def test_park_context_format_complete(self, mock_rag_service):
        """Test that park context has correct format with all components."""
        result = mock_rag_service._get_park_context("goat")

        assert result is not None
        # Format: [PARK INFO: Leesburg Animal Park has X species! Their names include ... Find them at: ...]
        assert result.startswith("[PARK INFO:")
        assert result.endswith(".]")
        assert "Leesburg Animal Park has" in result
        assert "Their names include" in result
        assert "Find them at:" in result

    def test_individual_context_format_complete(self, mock_rag_service):
        """Test that individual context has correct format."""
        result = mock_rag_service._check_individual_name("Who is Ziggy?")

        assert result is not None
        # Format: [PARK INFO: Name is a Type at Leesburg Animal Park! You can find Name at Location.]
        assert result.startswith("[PARK INFO:")
        assert result.endswith(".]")
        assert "is a" in result
        assert "at Leesburg Animal Park!" in result
        assert "You can find" in result

    def test_park_context_escaping(self, mock_rag_service):
        """Test that special characters in data don't break format."""
        # Modify data to include special characters
        mock_rag_service._park_inventory["animals_by_species"]["goat"]["locations"] = [
            "Contact Area & Petting Zoo",
            "Main Barn (East)"
        ]

        result = mock_rag_service._get_park_context("goat")

        # Should still be properly formatted
        assert result.startswith("[PARK INFO:")
        assert "Contact Area & Petting Zoo" in result


class TestIntegration:
    """Integration tests combining multiple park inventory features."""

    def test_species_and_individual_queries_independent(self, mock_rag_service):
        """Test that species and individual queries work independently."""
        species_result = mock_rag_service._get_park_context("monkey")
        individual_result = mock_rag_service._check_individual_name("Who is Ziggy?")

        # Both should work and provide different context
        assert species_result is not None
        assert individual_result is not None
        assert species_result != individual_result

        # Species result talks about count and multiple animals
        assert "4 monkeys" in species_result

        # Individual result is specific to Ziggy
        assert "Ziggy is a" in individual_result

    def test_alias_resolves_to_correct_species(self, mock_rag_service):
        """Test that alias correctly resolves through entire chain."""
        # Query with alias should give same result as direct species
        alias_result = mock_rag_service._get_park_context("tamarin")
        direct_result = mock_rag_service._get_park_context("monkey")

        assert alias_result == direct_result

    def test_empty_inventory_graceful_handling(self):
        """Test that empty inventory doesn't crash."""
        rag = RAGService()
        rag._park_inventory = {"animals_by_species": {}, "animals_by_name": {}, "aliases": {}}

        species_result = rag._get_park_context("goat")
        individual_result = rag._check_individual_name("Who is Ziggy?")

        assert species_result is None
        assert individual_result is None

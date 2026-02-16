import pytest

from deckslots.models import Category, Decklist


class TestCategory:
    """Category represents a named grouping of slots in a decklist."""

    def test_category_has_name_and_total_slots(self):
        """A category has a name and a total number of slots."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.name == "Ramp"
        assert cat.total_slots == 10

    def test_new_category_has_empty_cards(self):
        """A new category starts with no cards assigned."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.cards == set()

    def test_filled_returns_zero_for_empty_category(self):
        """filled returns 0 when no cards are assigned."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.filled == 0

    def test_available_returns_total_slots_for_empty_category(self):
        """available returns total_slots when no cards are assigned."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.available == 10

    def test_is_full_returns_false_for_empty_category(self):
        """is_full returns False when no cards are assigned."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.is_full is False

    def test_category_rejects_zero_slots(self):
        """A category must have at least 1 slot."""
        with pytest.raises(ValueError):
            Category(name="Bad", total_slots=0)

    def test_category_rejects_100_slots(self):
        """A category must have at most 99 slots."""
        with pytest.raises(ValueError):
            Category(name="Bad", total_slots=100)

    def test_category_fixed_defaults_to_false(self):
        """Categories are not fixed by default."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.fixed is False

    def test_fixed_category_has_correct_attributes(self):
        """A fixed category preserves all fields correctly."""
        cat = Category(name="Commander", total_slots=1, fixed=True)
        assert cat.name == "Commander"
        assert cat.total_slots == 1
        assert cat.fixed is True
        assert cat.cards == set()
        assert cat.filled == 0
        assert cat.available == 1
        assert cat.is_full is False


class TestDecklistCreate:
    """Decklist.create builds a new decklist with required structure."""

    def test_create_returns_decklist_with_name(self):
        """Decklist.create returns a decklist with the given name."""
        deck = Decklist.create("Test Deck")
        assert deck.name == "Test Deck"

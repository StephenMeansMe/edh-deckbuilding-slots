from deckslots.models import Category


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

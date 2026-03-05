import pytest

from deckslots.models import BASIC_LAND_NAMES, Category, Decklist


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
        assert cat.cards == []

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
        assert cat.cards == []
        assert cat.filled == 0
        assert cat.available == 1
        assert cat.is_full is False


class TestCategoryCards:
    """Category.cards is a list to support duplicate card names."""

    def test_new_category_cards_is_list(self):
        """A new category's cards field is a list, not a set."""
        cat = Category(name="Ramp", total_slots=10)
        assert isinstance(cat.cards, list)


class TestCategoryCapped:
    """Category.capped controls slot validation behavior."""

    def test_uncapped_category_accepts_zero_slots(self):
        """An uncapped category allows total_slots=0."""
        cat = Category(name="Basic Lands", total_slots=0, capped=False)
        assert cat.total_slots == 0

    def test_uncapped_category_accepts_slots_above_99(self):
        """An uncapped category allows total_slots above 99."""
        cat = Category(name="Basic Lands", total_slots=200, capped=False)
        assert cat.total_slots == 200

    def test_uncapped_category_rejects_negative_slots(self):
        """An uncapped category still rejects negative total_slots."""
        with pytest.raises(ValueError):
            Category(name="Basic Lands", total_slots=-1, capped=False)

    def test_uncapped_category_is_never_full(self):
        """An uncapped category with 0 slots and no cards is not full."""
        cat = Category(name="Basic Lands", total_slots=0, capped=False)
        assert cat.is_full is False

    def test_uncapped_category_available_is_none(self):
        """An uncapped category reports available as None (unbounded)."""
        cat = Category(name="Basic Lands", total_slots=0, capped=False)
        assert cat.available is None

    def test_capped_defaults_to_true(self):
        """Categories are capped by default."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.capped is True


class TestCategoryAllowedCards:
    """Category.allowed_cards restricts which cards can be added."""

    def test_category_allowed_cards_defaults_to_none(self):
        """By default, a category has no card restrictions."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.allowed_cards is None

    def test_category_stores_allowed_cards(self):
        """A category can be constructed with an allowed_cards whitelist."""
        allowed = frozenset({"Plains", "Island"})
        cat = Category(
            name="Basics", total_slots=5, allowed_cards=allowed, capped=False
        )
        assert cat.allowed_cards == allowed


class TestBasicLandNames:
    """BASIC_LAND_NAMES is a frozenset of all 12 valid basic land names."""

    def test_basic_land_names_is_frozenset(self):
        """The constant is a frozenset (immutable)."""
        assert isinstance(BASIC_LAND_NAMES, frozenset)

    def test_basic_land_names_has_12_entries(self):
        """There are exactly 12 basic land names in MTG."""
        assert len(BASIC_LAND_NAMES) == 12

    def test_basic_land_names_contains_core_five(self):
        """The five classic basic lands are included."""
        for name in ("Plains", "Island", "Swamp", "Mountain", "Forest"):
            assert name in BASIC_LAND_NAMES

    def test_basic_land_names_contains_wastes(self):
        """Wastes (colorless basic land) is included."""
        assert "Wastes" in BASIC_LAND_NAMES

    def test_basic_land_names_contains_snow_covered(self):
        """All six snow-covered basic lands are included."""
        for name in (
            "Snow-Covered Plains",
            "Snow-Covered Island",
            "Snow-Covered Swamp",
            "Snow-Covered Mountain",
            "Snow-Covered Forest",
            "Snow-Covered Wastes",
        ):
            assert name in BASIC_LAND_NAMES


class TestDecklistCreate:
    """Decklist.create builds a new decklist with required structure."""

    def test_create_returns_decklist_with_name(self):
        """Decklist.create returns a decklist with the given name."""
        deck = Decklist.create("Test Deck")
        assert deck.name == "Test Deck"

    def test_create_includes_commander_category(self):
        """A new decklist has a Commander category."""
        deck = Decklist.create("Test Deck")
        assert "commander" in deck.categories

    def test_commander_category_has_one_fixed_slot(self):
        """The Commander category has exactly 1 fixed slot."""
        deck = Decklist.create("Test Deck")
        commander = deck.categories["commander"]
        assert commander.total_slots == 1
        assert commander.fixed is True

    def test_total_slots_for_new_decklist_is_one(self):
        """A new decklist has 1 total slot (commander=1, basic lands=0)."""
        deck = Decklist.create("Test Deck")
        assert deck.total_slots == 1


class TestDecklistCreateBasicLands:
    """Decklist.create includes a mandatory Basic Lands category."""

    def test_create_includes_basic_lands_category(self):
        """A new decklist has a Basic Lands category."""
        deck = Decklist.create("Test Deck")
        assert "basic lands" in deck.categories

    def test_basic_lands_is_fixed(self):
        """The Basic Lands category is fixed (cannot be removed by user)."""
        deck = Decklist.create("Test Deck")
        assert deck.categories["basic lands"].fixed is True

    def test_basic_lands_starts_with_zero_slots(self):
        """The Basic Lands category starts with 0 slots."""
        deck = Decklist.create("Test Deck")
        assert deck.categories["basic lands"].total_slots == 0

    def test_basic_lands_is_uncapped(self):
        """The Basic Lands category is uncapped (no upper limit)."""
        deck = Decklist.create("Test Deck")
        assert deck.categories["basic lands"].capped is False

    def test_basic_lands_has_allowed_cards(self):
        """The Basic Lands category restricts cards to BASIC_LAND_NAMES."""
        deck = Decklist.create("Test Deck")
        assert deck.categories["basic lands"].allowed_cards == BASIC_LAND_NAMES


class TestDecklistAddCategory:
    """Decklist.add_category adds user-defined categories."""

    def test_add_category_creates_category_with_slots(self):
        """add_category stores a new category accessible by lowercase key."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Ramp", 10)
        assert "ramp" in deck.categories
        assert deck.categories["ramp"].name == "Ramp"
        assert deck.categories["ramp"].total_slots == 10

    def test_add_category_increases_total_slots(self):
        """Adding a category increases the decklist's total slot count."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Ramp", 10)
        assert deck.total_slots == 11

    def test_add_category_rejects_duplicate_name(self):
        """Adding a category with the same name (case-insensitive) raises ValueError."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Ramp", 10)
        with pytest.raises(ValueError):
            deck.add_category("ramp", 5)

    def test_add_category_rejects_commander_name(self):
        """Cannot add a category named Commander (reserved)."""
        deck = Decklist.create("Test Deck")
        with pytest.raises(ValueError):
            deck.add_category("Commander", 1)

    def test_add_category_rejects_basic_lands_name(self):
        """Cannot add a category named Basic Lands (reserved)."""
        deck = Decklist.create("Test Deck")
        with pytest.raises(ValueError):
            deck.add_category("Basic Lands", 5)

    def test_add_category_rejects_zero_slots(self):
        """add_category rejects 0 slots (delegates to Category validation)."""
        deck = Decklist.create("Test Deck")
        with pytest.raises(ValueError):
            deck.add_category("Bad", 0)

    def test_add_category_rejects_100_slots(self):
        """add_category rejects 100 slots (delegates to Category validation)."""
        deck = Decklist.create("Test Deck")
        with pytest.raises(ValueError):
            deck.add_category("Bad", 100)

    def test_total_filled_for_new_decklist_is_zero(self):
        """A new decklist has 0 filled slots."""
        deck = Decklist.create("Test Deck")
        assert deck.total_filled == 0


class TestDecklistAddCard:
    """Decklist.add_card places a card into a category slot."""

    def test_add_card_appends_card_to_category(self):
        """add_card places the card into the named category's cards list."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        assert "Sol Ring" in deck.categories["ramp"].cards

    def test_add_card_raises_for_nonexistent_category(self):
        """add_card raises ValueError when the category does not exist."""
        deck = Decklist.create("Test Deck")
        with pytest.raises(ValueError, match="not found"):
            deck.add_card("Sol Ring", "Nonexistent")

    def test_add_card_raises_when_category_is_full(self):
        """add_card raises ValueError when the category has no available slots."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Tiny", 1)
        deck.add_card("Sol Ring", "Tiny")
        with pytest.raises(ValueError, match="full"):
            deck.add_card("Mana Crypt", "Tiny")

    def test_add_card_raises_when_card_not_in_allowed_cards(self):
        """add_card raises ValueError when the card is not in the whitelist."""
        deck = Decklist.create("Test Deck")
        with pytest.raises(ValueError, match="not allowed"):
            deck.add_card("Sol Ring", "Basic Lands")

    def test_add_card_accepts_valid_basic_land(self):
        """add_card succeeds when the card is in the allowed_cards whitelist."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Forest", "Basic Lands")
        assert "Forest" in deck.categories["basic lands"].cards

    def test_add_card_raises_for_duplicate_in_exclusive_decklist(self):
        """add_card raises ValueError when the card is already in a capped category."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Ramp", 10)
        deck.add_category("Draw", 10)
        deck.add_card("Sol Ring", "Ramp")
        with pytest.raises(ValueError, match="already in the decklist"):
            deck.add_card("Sol Ring", "Draw")

    def test_add_card_allows_duplicates_in_uncapped_category(self):
        """add_card allows the same card name multiple times in an uncapped category."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Forest", "Basic Lands")
        deck.add_card("Forest", "Basic Lands")
        assert deck.categories["basic lands"].cards.count("Forest") == 2

    def test_add_card_increments_total_filled(self):
        """add_card increases the decklist's total_filled count."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Ramp", 10)
        assert deck.total_filled == 0
        deck.add_card("Sol Ring", "Ramp")
        assert deck.total_filled == 1

    def test_add_card_to_commander_category(self):
        """add_card can place a card in the Commander fixed category."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        assert "Atraxa, Praetors' Voice" in deck.categories["commander"].cards


class TestDecklistFindCard:
    """Decklist.find_card locates the category key containing a given card."""

    def test_find_card_returns_category_key_when_found(self):
        """find_card returns the lowercase category key when the card is present."""
        deck = Decklist.create("Test Deck")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        assert deck.find_card("Sol Ring") == "ramp"

    def test_find_card_returns_none_when_absent(self):
        """find_card returns None when the card is not in any category."""
        deck = Decklist.create("Test Deck")
        assert deck.find_card("Sol Ring") is None

    def test_find_card_finds_card_in_uncapped_category(self):
        """find_card finds cards stored in uncapped categories."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Forest", "Basic Lands")
        assert deck.find_card("Forest") == "basic lands"

    def test_find_card_finds_card_in_commander_category(self):
        """find_card finds the commander in the Commander category."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        assert deck.find_card("Atraxa, Praetors' Voice") == "commander"


class TestCategoryUserAddable:
    """Category.user_addable controls whether card add is permitted."""

    def test_user_addable_defaults_to_true(self):
        """A freshly created Category is user-addable by default."""
        cat = Category(name="Ramp", total_slots=10)
        assert cat.user_addable is True

    def test_user_addable_can_be_set_false(self):
        """user_addable=False can be set on a fixed uncapped category."""
        cat = Category(
            name="Uncategorized",
            total_slots=0,
            fixed=True,
            capped=False,
            user_addable=False,
        )
        assert cat.user_addable is False


class TestDecklistRenameCategory:
    def test_rename_category_updates_display_name_and_key(self):
        deck = Decklist.create("My Deck")
        deck.add_category("Ramp", 10)
        deck.rename_category("Ramp", "Mana Rocks")
        assert "ramp" not in deck.categories
        assert "mana rocks" in deck.categories
        assert deck.categories["mana rocks"].name == "Mana Rocks"

    def test_rename_category_case_insensitive_lookup(self):
        deck = Decklist.create("My Deck")
        deck.add_category("Ramp", 10)
        deck.rename_category("ramp", "Mana Rocks")  # lowercase lookup
        assert "mana rocks" in deck.categories
        assert deck.categories["mana rocks"].name == "Mana Rocks"

    def test_rename_category_preserves_cards(self):
        deck = Decklist.create("My Deck")
        deck.add_category("Ramp", 10)
        deck.add_card("Cultivate", "Ramp")
        deck.rename_category("Ramp", "Mana Rocks")
        assert "Cultivate" in deck.categories["mana rocks"].cards

    def test_rename_category_allows_case_change_only(self):
        deck = Decklist.create("My Deck")
        deck.add_category("Ramp", 10)
        deck.rename_category("Ramp", "RAMP")  # same key, different display
        assert "ramp" in deck.categories
        assert deck.categories["ramp"].name == "RAMP"

    def test_rename_category_allows_same_name(self):
        deck = Decklist.create("My Deck")
        deck.add_category("Ramp", 10)
        deck.rename_category("Ramp", "Ramp")  # no-op: no error
        assert deck.categories["ramp"].name == "Ramp"

    def test_rename_category_raises_for_not_found(self):
        deck = Decklist.create("My Deck")
        with pytest.raises(ValueError, match="not found"):
            deck.rename_category("Nonexistent", "Something")

    def test_rename_category_raises_for_fixed_commander(self):
        deck = Decklist.create("My Deck")
        with pytest.raises(ValueError, match="Cannot rename fixed category"):
            deck.rename_category("commander", "Leader")

    def test_rename_category_raises_for_name_conflict(self):
        deck = Decklist.create("My Deck")
        deck.add_category("Ramp", 10)
        deck.add_category("Combo", 10)
        with pytest.raises(ValueError, match="already exists"):
            deck.rename_category("Ramp", "Combo")


class TestDecklistRename:
    def test_rename_updates_decklist_name(self):
        deck = Decklist.create("Old Name")
        deck.rename("New Name")
        assert deck.name == "New Name"

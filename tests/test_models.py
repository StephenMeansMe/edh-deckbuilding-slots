import pytest

from deckslots.exceptions import CardError, CategoryError, SlotError
from deckslots.models import (
    BASIC_LAND_NAMES,
    CappedCategory,
    Category,
    Decklist,
    UncappedCategory,
)


class TestCategoryIsAbstract:
    """Category is an abstract base class and cannot be instantiated directly."""

    def test_category_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            Category(name="Ramp", total_slots=10)  # type: ignore[abstract]


class TestCategory:
    """Category represents a named grouping of slots in a decklist."""

    def test_category_has_name_and_total_slots(self):
        """A category has a name and a total number of slots."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.name == "Ramp"
        assert cat.total_slots == 10

    def test_new_category_has_empty_cards(self):
        """A new category starts with no cards assigned."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.cards == []

    def test_filled_returns_zero_for_empty_category(self):
        """filled returns 0 when no cards are assigned."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.filled == 0

    def test_available_returns_total_slots_for_empty_category(self):
        """available returns total_slots when no cards are assigned."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.available == 10

    def test_is_full_returns_false_for_empty_category(self):
        """is_full returns False when no cards are assigned."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.is_full is False

    def test_category_rejects_zero_slots(self):
        """A category must have at least 1 slot."""
        with pytest.raises(ValueError):
            CappedCategory(name="Bad", total_slots=0)

    def test_category_rejects_100_slots(self):
        """A category must have at most 99 slots."""
        with pytest.raises(ValueError):
            CappedCategory(name="Bad", total_slots=100)

    def test_category_fixed_defaults_to_false(self):
        """Categories are not fixed by default."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.fixed is False

    def test_fixed_category_has_correct_attributes(self):
        """A fixed category preserves all fields correctly."""
        cat = CappedCategory(name="Commander", total_slots=1, fixed=True)
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
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert isinstance(cat.cards, list)


class TestCategoryCapped:
    """CappedCategory and UncappedCategory have distinct slot validation behavior."""

    def test_uncapped_category_is_never_full(self):
        """An UncappedCategory is never full."""
        cat = UncappedCategory(name="Basic Lands")
        assert cat.is_full is False

    def test_uncapped_category_available_is_none(self):
        """An UncappedCategory reports available as None (unbounded)."""
        cat = UncappedCategory(name="Basic Lands")
        assert cat.available is None

    def test_user_created_category_is_capped(self):
        """User-created categories are CappedCategory instances."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert isinstance(cat, CappedCategory)


class TestCategoryAllowedCards:
    """Category.allowed_cards restricts which cards can be added."""

    def test_category_allowed_cards_defaults_to_none(self):
        """By default, a category has no card restrictions."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.allowed_cards is None

    def test_category_stores_allowed_cards(self):
        """A category can be constructed with an allowed_cards whitelist."""
        allowed = frozenset({"Plains", "Island"})
        cat = UncappedCategory(name="Basics", allowed_cards=allowed)
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
        assert isinstance(commander, CappedCategory)
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

    def test_basic_lands_is_uncapped(self):
        """The Basic Lands category is an UncappedCategory."""
        deck = Decklist.create("Test Deck")
        assert isinstance(deck.categories["basic lands"], UncappedCategory)

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
        ramp = deck.categories["ramp"]
        assert ramp.name == "Ramp"
        assert isinstance(ramp, CappedCategory)
        assert ramp.total_slots == 10

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
        """A freshly created CappedCategory is user-addable by default."""
        cat = CappedCategory(name="Ramp", total_slots=10)
        assert cat.user_addable is True

    def test_user_addable_can_be_set_false(self):
        """user_addable=False can be set on a fixed uncapped category."""
        cat = UncappedCategory(name="Uncategorized", fixed=True, user_addable=False)
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


class TestDecklistMoveCard:
    """Decklist.move_card moves a card between categories."""

    def test_move_card_raises_when_card_not_found(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        with pytest.raises(ValueError, match="not found"):
            deck.move_card("Sol Ring", "Ramp")

    def test_move_card_raises_when_target_not_found(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        with pytest.raises(ValueError, match="not found"):
            deck.move_card("Sol Ring", "Nonexistent")

    def test_move_card_raises_when_target_is_full(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 1)
        deck.add_category("Draw", 1)
        deck.add_card("Sol Ring", "Ramp")
        deck.add_card("Rhystic Study", "Draw")
        with pytest.raises(ValueError, match="full"):
            deck.move_card("Sol Ring", "Draw")

    def test_move_card_raises_when_already_in_target(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        with pytest.raises(ValueError, match="already in"):
            deck.move_card("Sol Ring", "Ramp")

    def test_move_card_raises_when_card_not_allowed(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        with pytest.raises(ValueError, match="not allowed"):
            deck.move_card("Sol Ring", "Basic Lands")

    def test_move_card_raises_when_card_in_another_capped_category(self):
        """move_card rejects if the card already exists in another capped category."""
        deck = Decklist.create("Test")
        # Inject Uncategorized first so find_card finds Sol Ring here before Ramp.
        # This matches the real import scenario where Uncategorized is created
        # before user categories are added.
        deck.categories["uncategorized"] = UncappedCategory(
            name="Uncategorized", fixed=True, user_addable=False
        )
        deck.categories["uncategorized"].cards.append("Sol Ring")
        deck.add_category("Ramp", 10)
        deck.add_category("Draw", 10)
        # Sol Ring is also in Ramp (simulating it was already moved there).
        # add_card allows this because Uncategorized is UncappedCategory.
        deck.add_card("Sol Ring", "Ramp")
        with pytest.raises(ValueError, match="already in the decklist"):
            deck.move_card("Sol Ring", "Draw")  # Sol Ring in Ramp should block this

    def test_move_card_moves_card_to_target(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_category("Draw", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.move_card("Sol Ring", "Draw")
        assert "Sol Ring" not in deck.categories["ramp"].cards
        assert "Sol Ring" in deck.categories["draw"].cards


class TestDecklistRemoveCard:
    """Decklist.remove_card moves a card to Uncategorized."""

    def test_remove_card_raises_when_card_not_found(self):
        deck = Decklist.create("Test")
        with pytest.raises(ValueError, match="not found"):
            deck.remove_card("Sol Ring")

    def test_remove_card_moves_card_to_uncategorized(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.remove_card("Sol Ring")
        assert "Sol Ring" not in deck.categories["ramp"].cards
        assert "Sol Ring" in deck.categories["uncategorized"].cards

    def test_remove_card_creates_uncategorized_if_missing(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        assert "uncategorized" not in deck.categories
        deck.remove_card("Sol Ring")
        assert "uncategorized" in deck.categories
        assert isinstance(deck.categories["uncategorized"], UncappedCategory)


class TestDecklistDeleteCard:
    """Decklist.delete_card permanently removes a card."""

    def test_delete_card_raises_when_card_not_found(self):
        deck = Decklist.create("Test")
        with pytest.raises(ValueError, match="not found"):
            deck.delete_card("Sol Ring")

    def test_delete_card_removes_card_from_decklist(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.delete_card("Sol Ring")
        assert "Sol Ring" not in deck.categories["ramp"].cards
        assert deck.find_card("Sol Ring") is None


class TestDecklistPartners:
    """Decklist.enable_partners allows two commanders."""

    def test_commander_rejects_second_card_by_default(self):
        """Commander category is full after one card, rejecting a second."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        with pytest.raises(ValueError, match="full"):
            deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")

    def test_new_decklist_has_partners_disabled(self):
        """A freshly created decklist has partners_enabled set to False."""
        deck = Decklist.create("Test Deck")
        assert deck.partners_enabled is False

    def test_enable_partners_sets_flag(self):
        """enable_partners sets partners_enabled to True."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        assert deck.partners_enabled is True

    def test_enable_partners_expands_commander_to_two_slots(self):
        """enable_partners sets the Commander category's total_slots to 2."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        assert deck.categories["commander"].total_slots == 2

    def test_enable_partners_allows_two_commanders(self):
        """After enable_partners, two cards can be added to Commander."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        assert len(deck.categories["commander"].cards) == 2

    def test_enable_partners_is_idempotent(self):
        """Calling enable_partners twice keeps commander at 2 slots."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_partners()
        assert deck.categories["commander"].total_slots == 2
        assert deck.partners_enabled is True


class TestDecklistBackground:
    """Decklist.enable_background allows a Background alongside the commander."""

    def test_new_decklist_has_background_disabled(self):
        """A freshly created decklist has background_enabled set to False."""
        deck = Decklist.create("Test Deck")
        assert deck.background_enabled is False

    def test_enable_background_sets_flag(self):
        """enable_background sets background_enabled to True."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        assert deck.background_enabled is True

    def test_enable_background_expands_commander_to_two_slots(self):
        """enable_background sets the Commander category's total_slots to 2."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        assert deck.categories["commander"].total_slots == 2

    def test_enable_background_allows_two_commanders(self):
        """After enable_background, two cards can be added to Commander."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert len(deck.categories["commander"].cards) == 2

    def test_enable_background_is_idempotent(self):
        """Calling enable_background twice keeps Commander at 2 slots."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.enable_background()
        assert deck.categories["commander"].total_slots == 2
        assert deck.background_enabled is True

    def test_both_modes_enabled_gives_three_slots(self):
        """Enabling partners and background gives Commander 3 slots."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        assert deck.categories["commander"].total_slots == 3

    def test_both_modes_allows_three_commanders(self):
        """With both modes enabled, three cards can be added to Commander."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Livaan, Cultist of Tiamat", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert len(deck.categories["commander"].cards) == 3


class TestDecklistDisableModes:
    """disable_partners and disable_background reverse their respective enable calls."""

    def test_disable_partners_clears_flag(self):
        """disable_partners sets partners_enabled to False."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.disable_partners()
        assert deck.partners_enabled is False

    def test_disable_partners_decrements_commander_slots(self):
        """disable_partners shrinks Commander back to 1 slot (background off)."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.disable_partners()
        assert deck.categories["commander"].total_slots == 1

    def test_disable_partners_moves_all_commanders_to_uncategorized(self):
        """disable_partners moves every Commander card to Uncategorized."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        deck.disable_partners()
        assert deck.categories["commander"].cards == []
        assert "Malcolm, Keen-Eyed Navigator" in deck.categories["uncategorized"].cards
        assert "Tana, the Bloodsower" in deck.categories["uncategorized"].cards

    def test_disable_partners_creates_uncategorized_if_needed(self):
        """disable_partners creates the Uncategorized category if it does not exist."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        assert "uncategorized" not in deck.categories
        deck.disable_partners()
        assert "uncategorized" in deck.categories

    def test_disable_partners_is_noop_when_already_disabled(self):
        """disable_partners does nothing when partners_enabled is already False."""
        deck = Decklist.create("Test Deck")
        deck.disable_partners()  # should not raise
        assert deck.categories["commander"].total_slots == 1

    def test_disable_background_clears_flag(self):
        """disable_background sets background_enabled to False."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.disable_background()
        assert deck.background_enabled is False

    def test_disable_background_decrements_commander_slots(self):
        """disable_background shrinks Commander back to 1 slot (partners off)."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.disable_background()
        assert deck.categories["commander"].total_slots == 1

    def test_disable_background_moves_all_commanders_to_uncategorized(self):
        """disable_background moves every Commander card to Uncategorized."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Criminal Past", "Commander")
        deck.disable_background()
        assert deck.categories["commander"].cards == []
        assert "Cloakwood Hermit" in deck.categories["uncategorized"].cards
        assert "Criminal Past" in deck.categories["uncategorized"].cards

    def test_disable_one_mode_with_both_enabled_leaves_two_slots(self):
        """Disabling one mode when both are on leaves Commander with 2 slots."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        deck.disable_partners()
        assert deck.categories["commander"].total_slots == 2
        assert deck.partners_enabled is False
        assert deck.background_enabled is True


class TestCommanderOvercrowded:
    """Decklist.commander_overcrowded detects too many cards for enabled modes."""

    def test_empty_commander_not_overcrowded(self):
        """Commander with no cards is never overcrowded."""
        deck = Decklist.create("Test Deck")
        assert deck.commander_overcrowded is False

    def test_one_card_no_modes_not_overcrowded(self):
        """One Commander card with no modes enabled is normal."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        assert deck.commander_overcrowded is False

    def test_two_cards_no_modes_is_overcrowded(self):
        """Two Commander cards with no modes enabled is overcrowded."""
        deck = Decklist.create("Test Deck")
        # Bypass add_card to force the overcrowded state (e.g. after a load)
        deck.categories["commander"].total_slots = 2
        deck.categories["commander"].cards = [
            "Cloakwood Hermit",
            "Criminal Past",
        ]
        assert deck.commander_overcrowded is True

    def test_two_cards_partners_enabled_not_overcrowded(self):
        """Two Commander cards with partners enabled is fine."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        assert deck.commander_overcrowded is False

    def test_two_cards_background_enabled_not_overcrowded(self):
        """Two Commander cards with background enabled is fine."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert deck.commander_overcrowded is False

    def test_three_cards_one_mode_is_overcrowded(self):
        """Three Commander cards with only one mode enabled is overcrowded."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.categories["commander"].total_slots = 3
        deck.categories["commander"].cards = ["A", "B", "C"]
        assert deck.commander_overcrowded is True

    def test_three_cards_both_modes_not_overcrowded(self):
        """Three Commander cards with both modes enabled is fine."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Livaan, Cultist of Tiamat", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert deck.commander_overcrowded is False


class TestDecklistCompanion:
    """Decklist supports an optional, separate Companion zone."""

    def test_new_decklist_has_companion_disabled(self):
        """A freshly created decklist has companion_enabled set to False."""
        deck = Decklist.create("Test")
        assert deck.companion_enabled is False

    def test_enable_companion_sets_flag(self):
        """enable_companion sets companion_enabled to True."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        assert deck.companion_enabled is True

    def test_enable_companion_creates_companion_category(self):
        """enable_companion adds a CappedCategory named 'Companion' with 1 slot."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        assert "companion" in deck.categories
        cat = deck.categories["companion"]
        assert isinstance(cat, CappedCategory)
        assert cat.total_slots == 1
        assert cat.fixed is True

    def test_enable_companion_is_idempotent(self):
        """Calling enable_companion twice keeps exactly 1 slot."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        deck.enable_companion()
        assert deck.categories["companion"].total_slots == 1
        assert deck.companion_enabled is True

    def test_enable_companion_does_not_change_commander_slots(self):
        """enable_companion leaves Commander's slot count unchanged."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        assert deck.categories["commander"].total_slots == 1

    def test_disable_companion_clears_flag(self):
        """disable_companion sets companion_enabled to False."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        deck.disable_companion()
        assert deck.companion_enabled is False

    def test_disable_companion_removes_companion_category(self):
        """disable_companion removes the companion category from the decklist."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        deck.disable_companion()
        assert "companion" not in deck.categories

    def test_disable_companion_moves_card_to_uncategorized(self):
        """disable_companion evacuates the companion card to Uncategorized."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        deck.disable_companion()
        assert "companion" not in deck.categories
        assert "Lurrus of the Dream-Den" in deck.categories["uncategorized"].cards

    def test_disable_companion_creates_uncategorized_if_needed(self):
        """disable_companion creates Uncategorized if it doesn't exist yet."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        assert "uncategorized" not in deck.categories
        deck.disable_companion()
        assert "uncategorized" in deck.categories

    def test_disable_companion_is_noop_when_already_disabled(self):
        """disable_companion is a no-op when companion is not enabled."""
        deck = Decklist.create("Test")
        deck.disable_companion()
        assert deck.companion_enabled is False
        assert "companion" not in deck.categories

    def test_companion_slot_empty_false_when_disabled(self):
        """companion_slot_empty is False when companion mode is off."""
        deck = Decklist.create("Test")
        assert deck.companion_slot_empty is False

    def test_companion_slot_empty_true_when_enabled_and_no_card(self):
        """companion_slot_empty is True when enabled but no card added."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        assert deck.companion_slot_empty is True

    def test_companion_slot_empty_false_when_companion_filled(self):
        """companion_slot_empty is False when the companion card is present."""
        deck = Decklist.create("Test")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        assert deck.companion_slot_empty is False


class TestDomainExceptions:
    """models.py raises domain-specific exception types, not raw ValueError."""

    def test_add_duplicate_card_raises_card_error(self):
        deck = Decklist.create("Test")
        deck.add_card("Sol Ring", "Commander")
        with pytest.raises(CardError):
            deck.add_card("Sol Ring", "Commander")

    def test_add_card_to_nonexistent_category_raises_category_error(self):
        deck = Decklist.create("Test")
        with pytest.raises(CategoryError):
            deck.add_card("Sol Ring", "Nonexistent")

    def test_add_card_to_full_slot_raises_slot_error(self):
        deck = Decklist.create("Test")
        deck.add_card("Sol Ring", "Commander")
        with pytest.raises(SlotError):
            deck.add_card("Swiftfoot Boots", "Commander")

    def test_add_disallowed_card_raises_category_error(self):
        deck = Decklist.create("Test")
        with pytest.raises(CategoryError):
            deck.add_card("Sol Ring", "Basic Lands")

    def test_invalid_slot_count_raises_slot_error(self):
        with pytest.raises(SlotError):
            CappedCategory(name="Ramp", total_slots=0)

    def test_add_category_duplicate_raises_category_error(self):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        with pytest.raises(CategoryError):
            deck.add_category("Ramp", 5)

    def test_move_card_not_found_raises_card_error(self):
        deck = Decklist.create("Test")
        with pytest.raises(CardError):
            deck.move_card("Nonexistent", "Basic Lands")

    def test_remove_card_not_found_raises_card_error(self):
        deck = Decklist.create("Test")
        with pytest.raises(CardError):
            deck.remove_card("Nonexistent")

    def test_delete_card_not_found_raises_card_error(self):
        deck = Decklist.create("Test")
        with pytest.raises(CardError):
            deck.delete_card("Nonexistent")

    def test_rename_nonexistent_category_raises_category_error(self):
        deck = Decklist.create("Test")
        with pytest.raises(CategoryError):
            deck.rename_category("Nonexistent", "New Name")

    def test_rename_fixed_category_raises_category_error(self):
        deck = Decklist.create("Test")
        with pytest.raises(CategoryError):
            deck.rename_category("Commander", "Leader")

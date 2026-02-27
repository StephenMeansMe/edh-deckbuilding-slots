# Domain Concepts

Reference for reasoning about business logic and new features.

---

## EDH / Commander

A multiplayer Magic: The Gathering format. Each deck contains exactly **100 cards** and is led by a **legendary creature** (the commander) that lives in its own designated zone. The deck follows a **singleton rule**: no card may appear more than once, with the exception of basic lands, which may be included in any quantity.

## Slot

A **slot** is a single position in a decklist that expects a card to be assigned to it. Slots exist independently of cards — an empty slot is valid. Slots are owned by a category.

## Category

A **category** is a named grouping of slots (e.g., "Ramp," "Removal," "Draw"). Categories come in two forms:

- **Capped** — user-created categories with a fixed slot count (1–99). When full (`len(cards) == total_slots`), no more cards can be added. `available` returns the number of empty slots; `is_full` returns `True` when none remain.
- **Uncapped** — no upper slot limit (`total_slots >= 0`, no maximum). `available` returns `None`; `is_full` always returns `False`. Used for Basic Lands and Uncategorized.

## Fixed Category

A **fixed category** is created automatically by `Decklist.create()` and cannot be renamed or deleted by the user. Two fixed categories exist in the MVP:

| Category | Slots | Capped | Notes |
|---|---|---|---|
| Commander | 1 | Yes | Exactly 1 slot; holds the deck's commander |
| Basic Lands | 0 (initial) | No | Uncapped; restricted to 12 basic land names |

*(Roadmap: partner, background, and companion are optional pre-configured fixed slots.)*

## Basic Lands

The **Basic Lands** category is fixed and uncapped. It is the only category that allows **duplicate card names**. It is restricted to the 12 valid basic land names via an `allowed_cards` whitelist (enforced by `Decklist.add_card()`):

- Classic: Plains, Island, Swamp, Mountain, Forest
- Wastes
- Snow-covered: Snow-Covered Plains, Snow-Covered Island, Snow-Covered Swamp, Snow-Covered Mountain, Snow-Covered Forest, Snow-Covered Wastes

The whitelist is stored as `BASIC_LAND_NAMES`, a module-level `frozenset[str]` in `models.py`.

## Uncategorized

**Uncategorized** is a fixed, uncapped category that is auto-created when a decklist is imported from a file. It acts as the landing zone for cards that have not yet been placed in a user-defined category. The app **persistently warns** the user until Uncategorized is empty. Users cannot manually add cards to Uncategorized directly; they reach it via `card remove` (which moves a card from its current category back to Uncategorized) or via `decklist import`.

## Exclusivity

In the MVP, categories are **exclusive**: each card occupies exactly one slot in exactly one category. The total slot count across all categories equals 100.

The exclusivity rule is enforced by `Decklist.add_card()`: before adding a card to a capped category, the method checks that the card does not already exist in any other capped category. **Uncapped categories are exempt from this check** — a card can coexist in an uncapped category (e.g., Basic Lands) and a capped one without triggering the exclusivity error, though in practice basic lands are not placed in capped categories.

*(Roadmap: non-exclusive mode will allow a card to appear in multiple category slots simultaneously, with one designated as the primary placement. Non-exclusive mode allows total slots to exceed 100.)*

## Business Rules for Adding Cards

`Decklist.add_card(card, category_name)` enforces the following in order:

1. **Category existence** — the named category must exist in the decklist.
2. **Allowed-cards whitelist** — if the category has an `allowed_cards` set, the card name must be in it.
3. **Fullness** — capped categories reject cards when `is_full` is `True`.
4. **Singleton exclusivity** — for capped categories, the card must not already exist in any other capped category.

Card **move** and **remove** operations (`card move`, `card remove`) manipulate `category.cards` directly in the command handlers, bypassing `Decklist.add_card()`, so the exclusivity check is **not** re-run during a move.

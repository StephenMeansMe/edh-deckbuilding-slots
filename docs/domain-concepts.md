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

A **fixed category** cannot be renamed or deleted by the user. Fixed categories either come pre-created (`Decklist.create()` always adds Commander and Basic Lands) or are added by enabling an optional mode.

| Category | Capped | Auto-created | Notes |
|---|---|---|---|
| Commander | Yes (1–3 slots) | Always | 1 slot by default; expands when partner or background mode is enabled |
| Basic Lands | No | Always | Uncapped; restricted to 12 basic land names |
| Companion | Yes (1 slot) | `enable-companion` | Separate zone outside the main 100; disabled by default |
| Uncategorized | No | On first use | Landing zone for displaced or removed cards |

## Commander Modes

The Commander category starts with **1 slot** and can expand by enabling optional modes:

- **Partner mode** (`decklist enable-partner`) — adds 1 slot, allowing two partner commanders. `decklist disable-partner` removes the slot and moves all Commander cards to Uncategorized.
- **Background mode** (`decklist enable-background`) — adds 1 slot for a Background enchantment alongside a "choose a Background" commander. `decklist disable-background` similarly shrinks the slot and evacuates.

Both modes can be active simultaneously (Commander slot grows to 3). The `commander_overcrowded` property returns `True` when the Commander category holds more cards than the currently enabled modes allow; the REPL warns the user until resolved.

## Companion

**Companion** is an optional fixed zone for a companion creature that lives **outside the main 100-card deck**. It is a separate `CappedCategory` (1 slot) and does **not** expand the Commander category.

Enabling companion mode (`decklist enable-companion`) creates the Companion category. Disabling it (`decklist disable-companion`) removes the category and moves any companion card to Uncategorized.

When companion mode is enabled but the slot is empty, the REPL warns the user (`companion_slot_empty` property). The companion card appears in its own `Companion` section in both exported files and saved files, between the `Commander` section and `Maindeck`.

## Basic Lands

The **Basic Lands** category is fixed and uncapped. It is the only category that allows **duplicate card names**. It is restricted to the 12 valid basic land names via an `allowed_cards` whitelist (enforced by `Decklist.add_card()`):

- Classic: Plains, Island, Swamp, Mountain, Forest
- Wastes
- Snow-covered: Snow-Covered Plains, Snow-Covered Island, Snow-Covered Swamp, Snow-Covered Mountain, Snow-Covered Forest, Snow-Covered Wastes

The whitelist is stored as `BASIC_LAND_NAMES`, a module-level `frozenset[str]` in `models.py`.

## Uncategorized

**Uncategorized** is a fixed, uncapped category that acts as a landing zone for cards not yet placed in a user-defined category. It is created on first use — not at decklist creation — and appears in the following situations:

- `decklist import` — cards that aren't the commander or a basic land land here
- `card remove` — moves a card from its current category to Uncategorized
- `decklist disable-partner` / `disable-background` / `disable-companion` — evacuates cards from the disabled fixed slot here

The app **persistently warns** the user until Uncategorized is empty. Users cannot target Uncategorized with `card add` or `card move`; `user_addable` is `False` on the Uncategorized category.

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

`Decklist.move_card()` is a model method that performs its own exclusivity check (it cannot call `add_card` internally, because the card is still in the source category at validation time, which would cause a spurious "already in decklist" failure). `Decklist.remove_card()` moves a card to the Uncategorized `UncappedCategory`, so exclusivity does not apply. `Decklist.delete_card()` removes permanently without any exclusivity concern.

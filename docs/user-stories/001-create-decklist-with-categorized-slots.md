# User Story 001: Create a Decklist with Categorized Slots

## Story

**As a** Commander/EDH deckbuilder,
**I want to** create a new decklist by defining a commander slot and adding named categories with a set number of slots each,
**so that** I have a structured skeleton for my 100-card deck before I start assigning specific cards.

## Acceptance Criteria

1. A new decklist is created with a mandatory "Commander" category containing exactly one fixed slot.
2. I can add user-defined categories (e.g., "Ramp," "Removal," "Draw") each with a specified number of slots (1–99).
3. Slots exist independently of cards — a freshly created decklist has empty slots that are ready to be filled.
4. The total slot count across all categories is tracked (target: 100 in exclusive mode).
5. I cannot create a category with zero or more than 99 slots.

## Notes

- This story targets the foundational data model — `Slot`, `Category`, and `Decklist` — which the rest of the application (card assignment, export, Scryfall integration) will build on.
- Fixed slots (commander, partner, background, companion) are a special structural concept; only the commander slot is mandatory for this story.
- No card assignment or validation logic is in scope here.

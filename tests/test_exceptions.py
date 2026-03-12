from deckslots.exceptions import (
    CardError,
    CategoryError,
    DecklistError,
    FileError,
    ParseError,
    SlotError,
)


def test_exception_hierarchy():
    assert issubclass(CardError, DecklistError)
    assert issubclass(SlotError, DecklistError)
    assert issubclass(CategoryError, DecklistError)
    assert issubclass(FileError, DecklistError)
    assert issubclass(ParseError, DecklistError)
    assert issubclass(DecklistError, ValueError)
    assert issubclass(DecklistError, Exception)

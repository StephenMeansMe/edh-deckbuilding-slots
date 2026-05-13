"""Scryfall bulk data management: fetch, cache, and card lookup."""

from __future__ import annotations

import json
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    card: str
    found: bool
    commander_legal: bool


def build_name_index(cards: list[dict]) -> dict[str, dict]:
    """Build a lowercase-name → card-dict index from a list of Scryfall card objects.

    Multi-face cards (DFCs, split cards) are indexed by their full combined name
    AND by each individual face name. All entries point to the same card object.
    """
    index: dict[str, dict] = {}
    for card in cards:
        index[card["name"].lower()] = card
        for face in card.get("card_faces", []):
            index[face["name"].lower()] = card
    return index


def validate_card(card_name: str, index: dict[str, dict]) -> ValidationResult:
    """Look up *card_name* in *index* and return a ValidationResult."""
    entry = index.get(card_name.lower())
    if entry is None:
        return ValidationResult(card=card_name, found=False, commander_legal=False)
    legal = entry.get("legalities", {}).get("commander") == "legal"
    return ValidationResult(card=card_name, found=True, commander_legal=legal)


def get_cache_path() -> Path:
    """Return the path to the local Scryfall oracle_cards cache file."""
    import os

    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        base = Path(xdg)
    else:
        base = Path.home() / ".cache"
    return base / "deckslots" / "oracle_cards.json"


def is_cache_stale(path: Path, max_age_days: int = 7) -> bool:
    """Return True if *path* does not exist or is older than *max_age_days*."""
    if not path.exists():
        return True
    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds >= max_age_days * 24 * 3600


def load_index_from_cache(path: Path) -> dict[str, dict] | None:
    """Load and index oracle_cards JSON from *path*.

    Returns None if the file is missing or contains invalid JSON.
    """
    if not path.exists():
        return None
    try:
        cards = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return build_name_index(cards)


def fetch_bulk_data_url() -> str:
    """Fetch the current download URI for the oracle_cards bulk file from Scryfall."""
    api_url = "https://api.scryfall.com/bulk-data/oracle-cards"
    with urllib.request.urlopen(api_url) as resp:  # noqa: S310
        data = json.loads(resp.read().decode())
    return data["download_uri"]


def download_oracle_cards(dest: Path) -> None:
    """Download the Scryfall oracle_cards bulk file and save it to *dest*."""
    url = fetch_bulk_data_url()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        dest.write_bytes(resp.read())


# ---------------------------------------------------------------------------
# Image pipeline (Phase 2)
# ---------------------------------------------------------------------------


def get_image_cache_dir() -> Path:
    """Return the directory where Scryfall card images are cached."""
    import os

    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "deckslots" / "card_images"


_FILENAME_SCRUB = re.compile(r"[^a-z0-9]+")


def _image_filename(card_name: str) -> str:
    """Return the on-disk filename for *card_name*'s cached image."""
    slug = _FILENAME_SCRUB.sub("_", card_name.lower()).strip("_")
    return f"{slug}.jpg"


def _image_url_from_index(card_name: str, index: dict) -> str | None:
    """Look up an `image_uris.normal` URL for *card_name* in *index*.

    Returns the front-face URL for double-faced/split cards.
    """
    entry = index.get(card_name.lower())
    if entry is None:
        return None
    image_uris = entry.get("image_uris")
    if isinstance(image_uris, dict) and "normal" in image_uris:
        return image_uris["normal"]
    for face in entry.get("card_faces", []):
        face_uris = face.get("image_uris")
        if isinstance(face_uris, dict) and "normal" in face_uris:
            return face_uris["normal"]
    return None


def fetch_card_image(
    card_name: str,
    index: dict | None = None,
    cache_dir: Path | None = None,
) -> Path | None:
    """Return a local path to the cached image of *card_name*, fetching if needed.

    Returns None if no image URL can be resolved or the download fails.
    Network errors are swallowed — callers fall back to a placeholder.
    """
    cache_dir = cache_dir or get_image_cache_dir()
    dest = cache_dir / _image_filename(card_name)
    if dest.exists():
        return dest

    url: str | None = None
    if index is not None:
        url = _image_url_from_index(card_name, index)
    if url is None:
        return None

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as resp:  # noqa: S310
            dest.write_bytes(resp.read())
    except OSError:
        return None
    return dest

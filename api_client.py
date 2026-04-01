"""
Hypixel SkyBlock API client
===========================
Thin wrapper around the public SkyBlock endpoints. All network calls go
through this module so the rest of the codebase stays testable with mocked
responses.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger(__name__)

BAZAAR_URL = "https://api.hypixel.net/v2/skyblock/bazaar"
ITEMS_URL = "https://api.hypixel.net/v2/resources/skyblock/items"

_DEFAULT_TIMEOUT = 10  # seconds


class HypixelAPIError(RuntimeError):
    """Raised when an API request fails."""


def _get(url: str) -> dict[str, Any]:
    """Perform a GET request and return parsed JSON, or raise HypixelAPIError."""
    try:
        response = requests.get(url, timeout=_DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HypixelAPIError(f"Request to {url!r} failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def fetch_bazaar() -> dict[str, Any]:
    """Return the full bazaar payload from the Hypixel API."""
    log.info("Fetching bazaar data...")
    return _get(BAZAAR_URL)


def fetch_items() -> dict[str, Any]:
    """Return the full items resource payload from the Hypixel API."""
    log.info("Fetching item data...")
    return _get(ITEMS_URL)


def get_npc_sell_prices(item_ids: list[str]) -> dict[str, float]:
    """
    Look up NPC sell prices for the given item IDs.

    Falls back to cached ``testItemData.json`` if the live API is unavailable.
    """
    try:
        data = fetch_items()
    except HypixelAPIError as exc:
        log.warning("Live API unavailable (%s); falling back to cache.", exc)
        cache_path = Path(__file__).parent / "testItemData.json"
        if not cache_path.exists():
            raise FileNotFoundError(
                "No cached item data found and the live API is unreachable."
            ) from exc
        with cache_path.open() as f:
            data = json.load(f)

    id_set = set(item_ids)
    prices: dict[str, float] = {}
    for item in data.get("items", []):
        if item.get("id") in id_set:
            prices[item["id"]] = item["npc_sell_price"]

    missing = id_set - prices.keys()
    if missing:
        log.warning("Could not find NPC sell prices for: %s", missing)

    return prices


def get_bazaar_buy_price(product_id: str) -> float | None:
    """Return the instant-buy price for a bazaar product, or None on failure."""
    try:
        data = fetch_bazaar()
        return data["products"][product_id]["quick_status"]["buyPrice"]
    except (HypixelAPIError, KeyError) as exc:
        log.warning("Could not fetch bazaar price for %r: %s", product_id, exc)
        return None

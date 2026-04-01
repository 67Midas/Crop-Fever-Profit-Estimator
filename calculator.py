"""
Crop Fever ROI Calculator
=========================
Estimates the return-on-investment timeline and extra coins-per-hour gained
from upgrading Crop Fever in Hypixel SkyBlock farming.

Game mechanics modelled:
  - Crop Fever activation probability per block broken (levels 1-5)
  - Weighted rare-drop table for each crop during a Crop Fever window
  - Rare crop (Cropie / Squash / Fermento / Helianthus) spawn chance bonus
  - Optional Hypercharge multiplier on base-crop NPC sell prices
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final
import logging

import api_client

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ONCE_COMPRESSED_UNIT: Final[int] = 160
TWICE_COMPRESSED_UNIT: Final[int] = 25_600

# Crop Fever runs for exactly one minute (60 seconds) of block breaks.
CROP_FEVER_DURATION_SECONDS: Final[int] = 60

# During an active Crop Fever window, rare-crop spawn chance receives a flat
# +15% additive bonus (per wiki; may change with patches).
RARE_CROP_CF_BONUS: Final[float] = 0.15

# ---------------------------------------------------------------------------
# Game data
# ---------------------------------------------------------------------------

CROP_NICKNAMES: Final[dict[str, str]] = {
    "MELON": "Melon",
    "PUMPKIN": "Pumpkin",
    "CACTUS": "Cactus",
    "INK_SACK:3": "Cocoa Beans",   # Cocoa Beans
    "CARROT_ITEM": "Carrot",
    "WHEAT": "Wheat",
    "SUGAR_CANE": "Sugar Cane",
    "NETHER_STALK": "Netherwart",
    "POTATO_ITEM": "Potato",
    "RED_MUSHROOM": "Mushroom",
    "MOONFLOWER": "Moonflower",
    "WILD_ROSE": "Wild Rose",
    "DOUBLE_PLANT": "Sunflower",  # Sunflower
}

NPC_SELL_PRICES: Final[dict[str, float]] = {
    "MELON": 2,
    "PUMPKIN": 10,
    "CACTUS": 4,
    "INK_SACK:3": 3,   # Cocoa Beans
    "CARROT_ITEM": 3,
    "WHEAT": 6,
    "SUGAR_CANE": 4,
    "NETHER_STALK": 4,
    "POTATO_ITEM": 3,
    "RED_MUSHROOM": 10,
    "MOONFLOWER": 4,
    "WILD_ROSE": 4,
    "DOUBLE_PLANT": 4,  # Sunflower
}

RARE_CROP_NPC_SELL_PRICES: Final[dict[str, float]] = {
    "SQUASH": 75_000,
    "HELIANTHUS": 275_000,
    "CROPIE": 25_000,
    "FERMENTO": 250_000,
}

RARE_CROP_BASE_CHANCES: Final[dict[str, float]] = {
    "SQUASH": 0.0003,
    "HELIANTHUS": 0.00004,
    "CROPIE": 0.0005,
    "FERMENTO": 0.00007,
}

# Which rare-crop category each base crop belongs to
CROP_RARE_CATEGORY: Final[dict[str, str]] = {
    "MELON": "SQUASH",
    "PUMPKIN": "SQUASH",
    "CACTUS": "FERMENTO",
    "INK_SACK:3": "SQUASH",
    "CARROT_ITEM": "CROPIE",
    "WHEAT": "CROPIE",
    "SUGAR_CANE": "FERMENTO",
    "NETHER_STALK": "FERMENTO",
    "POTATO_ITEM": "CROPIE",
    "RED_MUSHROOM": "FERMENTO",
    "MOONFLOWER": "HELIANTHUS",
    "WILD_ROSE": "HELIANTHUS",
    "DOUBLE_PLANT": "HELIANTHUS",
}

# Drop amounts (in raw item count) for each rarity tier during Crop Fever
CF_DROP_AMOUNTS: Final[dict[str, dict[str, int]]] = {
    "MELON":        {"NONE": 1, "UNCOMMON": 24*ONCE_COMPRESSED_UNIT, "RARE": 48*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 4*TWICE_COMPRESSED_UNIT, "PRAY TO RNGESUS": 12*TWICE_COMPRESSED_UNIT},
    "PUMPKIN":      {"NONE": 1, "UNCOMMON": 6*ONCE_COMPRESSED_UNIT,  "RARE": 12*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 110*ONCE_COMPRESSED_UNIT,  "PRAY TO RNGESUS": 4*TWICE_COMPRESSED_UNIT},
    "CACTUS":       {"NONE": 1, "UNCOMMON": 6*ONCE_COMPRESSED_UNIT,  "RARE": 18*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 1*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 6*TWICE_COMPRESSED_UNIT},
    "INK_SACK:3":   {"NONE": 1, "UNCOMMON": 6*ONCE_COMPRESSED_UNIT,  "RARE": 12*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 120*ONCE_COMPRESSED_UNIT,  "PRAY TO RNGESUS": 4*TWICE_COMPRESSED_UNIT},
    "CARROT_ITEM":  {"NONE": 1, "UNCOMMON": 18*ONCE_COMPRESSED_UNIT, "RARE": 42*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 4*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 12*TWICE_COMPRESSED_UNIT},
    "WHEAT":        {"NONE": 1, "UNCOMMON": 6*ONCE_COMPRESSED_UNIT,  "RARE": 10*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 120*ONCE_COMPRESSED_UNIT,  "PRAY TO RNGESUS": 12*TWICE_COMPRESSED_UNIT},
    "SUGAR_CANE":   {"NONE": 1, "UNCOMMON": 12*ONCE_COMPRESSED_UNIT, "RARE": 24*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 1*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 6*TWICE_COMPRESSED_UNIT},
    "NETHER_STALK": {"NONE": 1, "UNCOMMON": 18*ONCE_COMPRESSED_UNIT, "RARE": 36*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 2*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 6*TWICE_COMPRESSED_UNIT},
    "POTATO_ITEM":  {"NONE": 1, "UNCOMMON": 18*ONCE_COMPRESSED_UNIT, "RARE": 32*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 2*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 6*TWICE_COMPRESSED_UNIT},
    "RED_MUSHROOM": {"NONE": 1, "UNCOMMON": 6*ONCE_COMPRESSED_UNIT,  "RARE": 12*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 120*ONCE_COMPRESSED_UNIT,  "PRAY TO RNGESUS": 16*TWICE_COMPRESSED_UNIT},
    "MOONFLOWER":   {"NONE": 1, "UNCOMMON": 12*ONCE_COMPRESSED_UNIT, "RARE": 24*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 2*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 6*TWICE_COMPRESSED_UNIT},
    "WILD_ROSE":    {"NONE": 1, "UNCOMMON": 12*ONCE_COMPRESSED_UNIT, "RARE": 24*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 2*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 6*TWICE_COMPRESSED_UNIT},
    "DOUBLE_PLANT": {"NONE": 1, "UNCOMMON": 12*ONCE_COMPRESSED_UNIT, "RARE": 24*ONCE_COMPRESSED_UNIT, "CRAZY RARE": 2*TWICE_COMPRESSED_UNIT,   "PRAY TO RNGESUS": 6*TWICE_COMPRESSED_UNIT},
}

_TOTAL_CF_WEIGHT: Final[float] = 20_138.0
CF_TIER_CHANCES: Final[dict[str, float]] = {
    "NONE":             20_000 / _TOTAL_CF_WEIGHT,
    "UNCOMMON":             90 / _TOTAL_CF_WEIGHT,
    "RARE":                 40 / _TOTAL_CF_WEIGHT,
    "CRAZY RARE":            7 / _TOTAL_CF_WEIGHT,
    "PRAY TO RNGESUS":       1 / _TOTAL_CF_WEIGHT,
}

# Probability that one block broken triggers a Crop Fever activation
CF_ACTIVATION_CHANCE: Final[dict[int, float]] = {
    1: 0.00001,
    2: 0.00002,
    3: 0.00003,
    4: 0.00004,
    5: 0.00005,
}

_COMPACTED_MOONFLOWER_COST: Final[int] = 102_400
CF_UPGRADE_COSTS: Final[dict[int, int]] = {
    level: _COMPACTED_MOONFLOWER_COST * (16 * 2 ** (level - 1))
    for level in range(1, 6)
}

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class CropFeverResult:
    crop_id: str
    level: int
    upgrade_cost: int
    extra_profit_per_hour: float
    roi_hours: float

    @property
    def roi_days(self) -> float:
        return self.roi_hours / 24

    def __str__(self) -> str:
        return (
            f"[{self.crop_id}  Lv{self.level}] "
            f"Extra profit/hr: {self.extra_profit_per_hour:>12,.0f} coins | "
            f"ROI: {self.roi_hours:>8.1f} h ({self.roi_days:.2f} days)"
        )


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def get_effective_sell_prices() -> dict[str, float]:
    """
    Return the best available sell price for each crop.

    Fetches bazaar instant-sell prices once and compares each against the
    hardcoded NPC price. The higher of the two is used so ROI estimates
    reflect real market value. Falls back silently to NPC prices when the
    bazaar API is unavailable or a crop has no bazaar listing.
    """
    effective: dict[str, float] = dict(NPC_SELL_PRICES)  # start from NPC baseline

    try:
        data = api_client.fetch_bazaar()
        for crop_id, npc_price in NPC_SELL_PRICES.items():
            try:
                bazaar_sell = data["products"][crop_id]["quick_status"]["sellPrice"]
                # Note: the bazaar prices are usually always worse than NPC sell prices - I'd wager it's because of the low demand
                # Crops have very few uses outside of Helianthus Armor & visitors (with the exception of carrots for pet candy)
                # I'm also using the average sell prices over the week to avoid getting inflated results due to market manipulation
                if bazaar_sell > npc_price:
                    log.info(
                        "%s: using bazaar sell price %.4f (NPC: %.2f)",
                        crop_id, bazaar_sell, npc_price,
                    )
                    effective[crop_id] = bazaar_sell
            except KeyError:
                pass  # crop not listed on bazaar; NPC price stays
    except api_client.HypixelAPIError as exc:
        log.warning("Bazaar API unavailable (%s); using NPC prices for all crops.", exc)

    return effective


def _expected_profit_per_activation(
    crop_id: str,
    blocks_per_second: float,
    hypercharge_bonus: float,
    sell_price: float,
) -> float:
    """
    Return the expected extra coins gained during a single Crop Fever window.

    The window lasts `CROP_FEVER_DURATION_SECONDS` seconds, so the number of
    blocks broken during it is `blocks_per_second * CROP_FEVER_DURATION_SECONDS`.

    Parameters
    ----------
    sell_price:
        Effective sell price for this crop (max of NPC vs bazaar sell price).
    """
    rare_crop_type = CROP_RARE_CATEGORY[crop_id]
    rare_crop_chance = RARE_CROP_BASE_CHANCES[rare_crop_type]

    # --- Rare-crop contribution (lower bound; assumes flat additive bonus) ---
    rare_profit_per_block = (
        RARE_CROP_NPC_SELL_PRICES[rare_crop_type] * (RARE_CROP_CF_BONUS) * rare_crop_chance
    )

    # --- Weighted average base-crop drop value per block ---
    cf_profit_per_block = 0.0
    for tier, chance in CF_TIER_CHANCES.items():
        drop_amount = CF_DROP_AMOUNTS[crop_id][tier]
        multiplier = hypercharge_bonus if tier == "NONE" else 1.0
        cf_profit_per_block += drop_amount * chance * sell_price * multiplier

    blocks_per_window = blocks_per_second * CROP_FEVER_DURATION_SECONDS
    return (rare_profit_per_block + cf_profit_per_block) * blocks_per_window


def calculate(
    crop_id: str,
    level: int,
    blocks_per_second: float,
    hypercharge_bonus: float = 1.0,
    effective_sell_prices: dict[str, float] | None = None,
) -> CropFeverResult:
    """
    Calculate extra profit per hour and ROI for a specific crop + CF level.

    Parameters
    ----------
    crop_id:
        Item ID string (e.g. ``"WHEAT"``).
    level:
        Crop Fever level (1–5).
    blocks_per_second:
        How fast the player breaks blocks.
    hypercharge_bonus:
        Multiplicative bonus applied to base (tier NONE) crop drops.
    effective_sell_prices:
        Pre-fetched mapping of crop ID → best sell price (NPC or bazaar).
        If omitted, ``get_effective_sell_prices()`` is called automatically.

    Returns
    -------
    CropFeverResult
    """
    if crop_id not in NPC_SELL_PRICES:
        raise ValueError(f"Unknown crop ID: {crop_id!r}")
    if level not in CF_ACTIVATION_CHANCE:
        raise ValueError(f"Level must be 1–5, got {level}")

    if effective_sell_prices is None:
        effective_sell_prices = get_effective_sell_prices()

    sell_price = effective_sell_prices[crop_id]
    activation_chance = CF_ACTIVATION_CHANCE[level]
    profit_per_activation = _expected_profit_per_activation(
        crop_id, blocks_per_second, hypercharge_bonus, sell_price
    )

    blocks_per_hour = blocks_per_second * 3_600
    activations_per_hour = blocks_per_hour * activation_chance
    #log.warning(f"activations_per_hour: {activations_per_hour}, profit_per_activation: {profit_per_activation}")
    extra_profit_per_hour = activations_per_hour * profit_per_activation

    upgrade_cost = CF_UPGRADE_COSTS[level]
    roi_hours = upgrade_cost / extra_profit_per_hour if extra_profit_per_hour else float("inf")

    return CropFeverResult(
        crop_id=CROP_NICKNAMES[crop_id],
        level=level,
        upgrade_cost=upgrade_cost,
        extra_profit_per_hour=extra_profit_per_hour,
        roi_hours=roi_hours,
    )


def calculate_all(
    blocks_per_second: float = 19.5,
    hypercharge_bonus: float = 1.0,
) -> list[CropFeverResult]:
    """Run calculations for every (crop, level) combination."""
    effective_sell_prices = get_effective_sell_prices()
    results = []
    for crop_id in NPC_SELL_PRICES:
        for level in CF_ACTIVATION_CHANCE:
            results.append(
                calculate(crop_id, level, blocks_per_second, hypercharge_bonus, effective_sell_prices)
            )
    return results
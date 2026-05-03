NOTE: As of the Harvest Feast update and the new Overbloom stat, this project is outdated
I will add support for the new harvest feast crops/seasonings soon (meaning, before galatea part 2 is released)

# 🌾 Crop Fever ROI Calculator

A data-driven Python tool that models the return-on-investment timeline for
upgrading **Crop Fever** in Hypixel SkyBlock's farming system.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## Features

- **Full probability model** of the Crop Fever drop table (NONE → PRAY TO
  RNGESUS tiers) using weighted expectations
- **Rare-crop spawn** contribution (Cropie / Squash / Fermento / Helianthus)
  during active Crop Fever windows
- **Live API integration** with the Hypixel SkyBlock items & bazaar endpoints;
  graceful fallback to cached data when offline
- **Interactive HTML dashboard** — self-contained, no extra dependencies,
  sorts/filters by crop, level, and farming speed
- Clean, modular architecture: `calculator.py` is fully decoupled from I/O

---

## Project structure

```
crop_fever_calculator/
├── calculator.py    # Core probability model & data constants
├── api_client.py    # Hypixel API wrapper (live + cached fallback)
├── visualiser.py    # Generates self-contained HTML dashboard
├── main.py          # CLI entry point
└── README.md
```

---

## Quick start

```bash
# Install dependencies
pip install requests

# Run with defaults (19.5 bps, all crops, all levels)
python main.py

# Show only level-5 results
python main.py --level 5

# Analyse a specific crop at 20 bps and export a dashboard
python main.py --crop WHEAT --bps 20 --html

# Apply a 1.5× Hypercharge multiplier to base-crop NPC sell prices
python main.py --hypercharge 1.5 --level 5
```

### CLI flags

| Flag | Default | Description |
|---|---|---|
| `--bps N` | `19.5` | Blocks broken per second |
| `--level {1-5}` | *(all)* | Show only this Crop Fever level |
| `--crop ID` | *(all)* | Filter to one crop (e.g. `WHEAT`) |
| `--hypercharge X` | `1.0` | Multiplier for base-crop sell price |
| `--html` | off | Generate & open interactive dashboard |
| `--out FILE` | `dashboard.html` | Dashboard output path |

---

## How it works

### Expected extra profit per activation

During an active Crop Fever window, the game breaks blocks for
`CROP_FEVER_DURATION_SECONDS` (60) seconds.  For every block in that window,
the expected extra coins earned is:

```
E[coins/block] = Σ_tier  P(tier) × drops(tier) × npc_price
               + (base_rare_crop_chance + 0.15) × rare_npc_price
```

Profit per activation then scales with `blocks/s × 60`.

### Activations per hour

```
activations/hr = blocks/s × 3600 × P(activation per block | level)
```

### ROI

```
ROI (hours) = upgrade_cost / expected_extra_profit_per_hour
```

---

## Assumptions & caveats

- **Rare-crop bonus** — the +15% spawn chance during Crop Fever is treated as
  flat additive.  It is unknown whether bonuses from Rarefinder chip or Rose
  Dragon are additive or multiplicative.  This gives a **lower bound** on
  rare-crop profit.
- **Concurrent activations** — the model does not account for the restriction
  that Crop Fever cannot activate while already active.  At typical farming
  speeds this has negligible impact.
- **Sugar Cane / Cactus** — the wiki notes that Crop Fever may proc twice on
  two-block-tall crops.  This is unconfirmed and is **not** modelled.

---

## License

MIT

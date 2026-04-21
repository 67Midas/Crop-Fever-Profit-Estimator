"""
Command-line interface for the Crop Fever ROI Calculator.

Usage
-----
    python main.py                          # defaults
    python main.py --bps 20 --level 5      # 20 blocks/s, level 5 only
    python main.py --crop WHEAT --html      # export HTML dashboard
    python main.py --help
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path
import matplotlib.pyplot as plt

import calculator
from visualiser import build_dashboard


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _fmt_coins(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def print_table(results: list[calculator.CropFeverResult], level: int | None = None) -> None:
    filtered = [r for r in results if (level is None or r.level == level)]
    if not filtered:
        print("No results match the given filters.")
        return

    header = f"{'Crop':<16} {'Level':>5} {'Upgrade Cost':>14} {'Extra Profit/hr':>16} {'ROI (hours)':>12} {'ROI (days)':>10}"
    print("\n" + header)
    print("-" * len(header))
    for r in sorted(filtered, key=lambda x: x.roi_hours):
        print(
            f"{r.crop_id:<16} {r.level:>5} "
            f"{_fmt_coins(r.upgrade_cost):>14} "
            f"{_fmt_coins(r.extra_profit_per_hour):>16} "
            f"{r.roi_hours:>12.1f} "
            f"{r.roi_days:>10.2f}"
        )
    print()


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description="Hypixel SkyBlock – Crop Fever ROI Calculator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    def _bps(value: str) -> float:
        v = float(value)
        if not (0 <= v <= 20):
            raise argparse.ArgumentTypeError(f"--bps must be between 0 and 20, got {v}")
        return v

    parser.add_argument(
        "--bps",
        type=_bps,
        default=19.5,
        metavar="N",
        help="Blocks broken per second (0–20)",
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=range(1, 6),
        default=None,
        metavar="{1-5}",
        help="Show only this Crop Fever level (omit for all levels)",
    )
    parser.add_argument(
        "--crop",
        default=None,
        metavar="ID",
        help="Filter to a single crop ID (e.g. WHEAT)",
    )
    parser.add_argument(
        "--hypercharge",
        type=float,
        default=1.0,
        metavar="X",
        help="Hypercharge multiplier for base-crop NPC sell price",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate an interactive HTML dashboard and open it in the browser",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("dashboard.html"),
        metavar="FILE",
        help="Output path for the HTML dashboard (only used with --html)",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Show a matplotlib plot of ROI (hours) vs crop for all levels",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    results = calculator.calculate_all(
        blocks_per_second=args.bps,
        hypercharge_bonus=args.hypercharge,
    )

    if args.crop:
        crop_id = args.crop.upper()
        results = [r for r in results if r.crop_id == crop_id]
        if not results:
            print(f"Error: unknown crop ID {crop_id!r}. "
                  f"Valid IDs: {sorted(calculator.NPC_SELL_PRICES)}")
            sys.exit(1)

    print_table(results, level=args.level)


    if args.plot:
        # Prepare data for plotting
        crops = sorted(set(r.crop_id for r in results))
        levels = sorted(set(r.level for r in results))
        crop_to_idx = {crop: i for i, crop in enumerate(crops)}
        fig, ax = plt.subplots(figsize=(12, 6))
        for level in levels:
            xs = []
            ys = []
            for crop in crops:
                for r in results:
                    if r.crop_id == crop and r.level == level:
                        xs.append(crop)
                        ys.append(r.roi_hours)
                        break
            ax.plot(xs, ys, marker="o", label=f"Level {level}")
        ax.set_xlabel("Crop")
        ax.set_ylabel("ROI (hours)")
        ax.set_title("Crop Fever ROI (hours) by Crop and Level")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    if args.html:
        html = build_dashboard(results)
        args.out.write_text(html, encoding="utf-8")
        print(f"Dashboard written to {args.out.resolve()}")
        webbrowser.open(args.out.resolve().as_uri())


if __name__ == "__main__":
    main()

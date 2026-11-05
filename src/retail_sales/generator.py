"""Deterministic synthetic retail transaction generator."""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PRODUCTS = [
    ("P001", "Wireless Mouse", "Electronics", 24.99),
    ("P002", "USB-C Cable", "Electronics", 12.50),
    ("P003", "Laptop Stand", "Electronics", 39.95),
    ("P004", "Desk Lamp", "Home", 31.25),
    ("P005", "Coffee Mug", "Home", 10.00),
    ("P006", "Water Bottle", "Home", 18.75),
    ("P007", "Notebook", "Stationery", 6.50),
    ("P008", "Gel Pens", "Stationery", 8.25),
    ("P009", "Desk Planner", "Stationery", 15.00),
    ("P010", "Running Socks", "Apparel", 13.50),
    ("P011", "Cotton T-Shirt", "Apparel", 22.00),
    ("P012", "Baseball Cap", "Apparel", 19.99),
    ("P013", "Yoga Mat", "Fitness", 28.00),
    ("P014", "Resistance Bands", "Fitness", 17.50),
    ("P015", "Foam Roller", "Fitness", 26.75),
    ("P016", "Trail Mix", "Grocery", 7.25),
    ("P017", "Ground Coffee", "Grocery", 14.50),
    ("P018", "Green Tea", "Grocery", 9.75),
    ("P019", "Phone Case", "Electronics", 16.99),
    ("P020", "Canvas Tote", "Apparel", 11.50),
]


def generate_transactions(output: Path, rows: int = 10_000, seed: int = 2025, duplicate_count: int = 400) -> pd.DataFrame:
    """Create a reproducible mixture of clean, invalid, missing, and duplicate rows."""
    if rows <= 0 or duplicate_count < 0 or duplicate_count >= rows:
        raise ValueError("rows must be positive and duplicate_count must be between 0 and rows - 1")

    rng = random.Random(seed)
    unique_count = rows - duplicate_count
    start = date(2024, 1, 1)
    records: list[dict[str, object]] = []

    for index in range(unique_count):
        product_id, product_name, category, price = rng.choice(PRODUCTS)
        transaction_date = start + timedelta(days=rng.randrange(731))
        record: dict[str, object] = {
            "transaction_id": f"TX-{index + 1:07d}",
            "order_id": f"ORD-{index // 2 + 1:06d}",
            "transaction_date": transaction_date.isoformat(),
            "customer_id": f"C-{rng.randint(1, 1_000):04d}",
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "quantity": rng.randint(1, 5),
            "unit_price": f"{price:.2f}",
        }

        # Stable intervals make every type of dirty record reproducible and reviewable.
        if index % 211 == 0:
            record["customer_id"] = ""
        if index % 223 == 0:
            record["quantity"] = 0
        if index % 227 == 0:
            record["transaction_date"] = "not-a-date"
        if index % 229 == 0:
            record["unit_price"] = "-4.00"
        records.append(record)

    frame = pd.DataFrame(records)
    duplicates = frame.iloc[:duplicate_count].copy()
    combined = pd.concat([frame, duplicates], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output, index=False)
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic retail transactions")
    parser.add_argument("--output", type=Path, default=Path("data/transactions.csv"))
    parser.add_argument("--rows", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument("--duplicates", type=int, default=400)
    args = parser.parse_args()
    generated = generate_transactions(args.output, args.rows, args.seed, args.duplicates)
    print(f"generated {len(generated)} rows at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


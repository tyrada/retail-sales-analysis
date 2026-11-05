"""Run the retail cleaning and analysis workflow and export portfolio artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from retail_sales.cleaning import clean_transactions


def build_summaries(cleaned: pd.DataFrame) -> dict[str, pd.DataFrame]:
    data = cleaned.copy()
    data["month"] = pd.to_datetime(data["transaction_date"]).dt.to_period("M").astype(str)
    monthly = data.groupby("month", as_index=False).agg(revenue=("revenue", "sum"), transactions=("transaction_id", "count"))
    products = (
        data.groupby(["product_id", "product_name"], as_index=False)
        .agg(units_sold=("quantity", "sum"), revenue=("revenue", "sum"))
        .sort_values(["revenue", "product_id"], ascending=[False, True])
    )
    customers = (
        data.groupby("customer_id", as_index=False)
        .agg(order_count=("order_id", "nunique"), revenue=("revenue", "sum"))
    )
    repeat_customers = customers.loc[customers["order_count"] >= 2].sort_values(["order_count", "customer_id"], ascending=[False, True])

    pair_counts: Counter[tuple[str, str]] = Counter()
    for products_in_order in data.groupby("order_id")["product_name"]:
        unique_products = sorted(set(products_in_order[1]))
        pair_counts.update(combinations(unique_products, 2))
    copurchases = pd.DataFrame(
        [(left, right, count) for (left, right), count in pair_counts.most_common()],
        columns=("product_a", "product_b", "order_count"),
    )
    return {"monthly_revenue": monthly, "top_products": products, "repeat_customers": repeat_customers, "copurchases": copurchases}


def _save_charts(summaries: dict[str, pd.DataFrame], output_dir: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")

    monthly = summaries["monthly_revenue"]
    fig, axis = plt.subplots(figsize=(11, 5))
    axis.plot(monthly["month"], monthly["revenue"], marker="o", linewidth=2)
    axis.set(title="Monthly Retail Revenue", xlabel="Month", ylabel="Revenue ($)")
    axis.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / "monthly_revenue.png", dpi=140)
    plt.close(fig)

    products = summaries["top_products"].head(10).sort_values("revenue")
    fig, axis = plt.subplots(figsize=(9, 6))
    axis.barh(products["product_name"], products["revenue"], color="#2878B5")
    axis.set(title="Top 10 Products by Revenue", xlabel="Revenue ($)", ylabel="")
    fig.tight_layout()
    fig.savefig(output_dir / "top_products.png", dpi=140)
    plt.close(fig)

    repeats = summaries["repeat_customers"]
    fig, axis = plt.subplots(figsize=(9, 5))
    axis.hist(repeats["order_count"], bins=15, color="#F28E2B", edgecolor="white")
    axis.set(title="Repeat-Customer Order Distribution", xlabel="Distinct orders", ylabel="Customers")
    fig.tight_layout()
    fig.savefig(output_dir / "repeat_customers.png", dpi=140)
    plt.close(fig)


def run_analysis(input_path: Path, output_dir: Path) -> dict[str, object]:
    raw = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    result = clean_transactions(raw)
    summaries = build_summaries(result.accepted)
    output_dir.mkdir(parents=True, exist_ok=True)

    result.accepted.to_csv(output_dir / "cleaned_transactions.csv", index=False)
    result.accepted.to_parquet(output_dir / "cleaned_transactions.parquet", index=False)
    result.rejected.to_csv(output_dir / "quarantined_transactions.csv", index=False)
    for name, summary in summaries.items():
        summary.to_csv(output_dir / f"{name}.csv", index=False)
    _save_charts(summaries, output_dir)

    metrics: dict[str, object] = {
        "input_count": result.input_count,
        "accepted_count": len(result.accepted),
        "rejected_count": len(result.rejected) - result.duplicate_count,
        "duplicate_count": result.duplicate_count,
        "total_revenue": round(float(result.accepted["revenue"].sum()), 2),
    }
    (output_dir / "run_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    top_month = summaries["monthly_revenue"].sort_values("revenue", ascending=False).iloc[0]
    top_product = summaries["top_products"].iloc[0]
    top_pair = summaries["copurchases"].iloc[0]
    findings = f"""# Findings

- Processed **{result.input_count:,}** input rows: **{len(result.accepted):,}** accepted, **{len(result.rejected) - result.duplicate_count:,}** invalid, and **{result.duplicate_count:,}** duplicates.
- Accepted revenue was **${metrics['total_revenue']:,.2f}** across {len(summaries['monthly_revenue'])} months.
- The highest-revenue month was **{top_month['month']}** at **${top_month['revenue']:,.2f}**.
- The highest-revenue product was **{top_product['product_name']}** at **${top_product['revenue']:,.2f}**.
- **{len(summaries['repeat_customers']):,}** customers placed at least two distinct orders.
- The most frequent product pair was **{top_pair['product_a']} + {top_pair['product_b']}**, appearing in **{int(top_pair['order_count'])}** orders.

Co-purchase associations describe items observed in the same order. They do not establish that purchasing one item causes purchasing another; promotions, seasonality, customer preferences, and the synthetic generation process can all confound the relationship.
"""
    (output_dir / "findings.md").write_text(findings, encoding="utf-8")
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and analyze retail transactions")
    parser.add_argument("--input", type=Path, default=Path("data/transactions.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    metrics = run_analysis(args.input, args.output_dir)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

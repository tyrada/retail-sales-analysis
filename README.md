# Retail Sales Analysis

A small pandas project that turns a deliberately messy 10,000-row retail extract into validated analytical data, summary tables, and readable charts. It is designed to demonstrate reproducible data generation, transformation, data-quality accounting, and responsible interpretation.

## Architecture

```text
seeded generator -> raw CSV -> schema/type validation -> cleaned CSV + Parquet
                                      |               -> summary CSVs + charts
                                      +-> quarantine  -> findings report
```

The cleaner first identifies repeated `transaction_id` values, keeping one copy. It then validates identifiers, ISO dates, positive integer quantities, and positive prices. Accepted rows receive a calculated `revenue = quantity * unit_price`; every rejected row retains its source values and one or more failure reasons.

## Data schema

| Column | Meaning |
| --- | --- |
| `transaction_id` | Stable line-item identifier and deduplication key |
| `order_id` | Basket identifier used for co-purchase analysis |
| `transaction_date` | Sale date, normalized to `YYYY-MM-DD` |
| `customer_id` | Customer identifier |
| `product_id`, `product_name`, `category` | Product attributes |
| `quantity` | Positive integer units |
| `unit_price` | Positive per-unit price |
| `revenue` | Derived accepted-row revenue |

## Setup and run

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'

generate-retail-data --rows 10000 --seed 2025 --duplicates 400
analyze-retail-sales --input data/transactions.csv --output-dir outputs
pytest -q --cov=retail_sales --cov-report=term-missing
```

The generator produces the same ordered file for the same arguments. The analysis exports:

- cleaned transactions as CSV and Parquet;
- a quarantine CSV and `run_metrics.json`;
- monthly revenue, top products, repeat customers, and product-pair CSVs;
- `monthly_revenue.png`, `top_products.png`, and `repeat_customers.png`;
- a generated `findings.md`.

Generated data and outputs are ignored by Git because they can be reproduced. The checked-in [findings report](reports/findings.md) records the verified default run.

## Actual results

Executed on November 5, 2026 with Python 3.12.16 and seed `2025`:

| Metric | Result |
| --- | ---: |
| Input rows | 10,000 |
| Accepted rows | 9,428 |
| Invalid rows | 172 |
| Duplicate rows | 400 |
| Accepted revenue | $509,977.30 |
| Months represented | 24 |

The highest-revenue month was June 2024 at $23,978.97; Laptop Stand led product revenue at $57,847.60; 999 customers placed at least two orders. Canvas Tote and Desk Lamp were the most frequent pair, appearing together in 37 orders.

These co-purchase associations are descriptive, not causal. Shared purchases may reflect promotions, customer preferences, seasonality, or the synthetic generator rather than one product causing another purchase.

Test result: **5 passed** with **64% total statement coverage**. CSV, Parquet, seven summary/quality files, the findings report, and three PNG charts were produced successfully.

## Local and cloud scope

This is a local pandas analysis project. It has no AWS implementation, mocked AWS tests, cloud deployment, IAM policy, or cloud cost. No external services or secrets are required.

## Limitations

- The dataset is synthetic and cannot support claims about real customers.
- Prices are treated as fixed line-item values; taxes, refunds, discounts, and currency conversion are absent.
- The in-memory pandas workflow is appropriate for this sample, not datasets larger than available memory.
- Duplicate detection assumes `transaction_id` is a trustworthy stable key.
- Pair counts do not use association-rule support, confidence, or lift.

## Interview questions and answers

1. **Why quarantine instead of dropping invalid rows?** Quarantine preserves evidence, failure reasons, and counts so upstream issues can be corrected and reprocessed.
2. **Why remove duplicates before calculating revenue?** Duplicate line items would overstate revenue and product demand. The stable transaction key defines which rows repeat.
3. **Why export both CSV and Parquet?** CSV is easy to inspect and exchange; Parquet preserves types and offers compressed columnar reads for analytics.
4. **How are repeat customers defined?** A customer must have at least two distinct `order_id` values, rather than merely multiple line items in one basket.
5. **Why do product pairs not prove causation?** Co-occurrence does not isolate confounding factors or a counterfactual; it only reports that two products appeared in the same orders.

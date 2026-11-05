from __future__ import annotations

import pandas as pd

from retail_sales.analysis import build_summaries


def test_summaries_calculate_monthly_product_repeat_and_pairs():
    cleaned = pd.DataFrame(
        [
            ["T1", "O1", "2025-01-01", "C1", "P1", "Mouse", "Electronics", 2, 10.0, 20.0],
            ["T2", "O1", "2025-01-01", "C1", "P2", "Mug", "Home", 1, 5.0, 5.0],
            ["T3", "O2", "2025-02-01", "C1", "P1", "Mouse", "Electronics", 1, 10.0, 10.0],
            ["T4", "O3", "2025-02-02", "C2", "P2", "Mug", "Home", 2, 5.0, 10.0],
        ],
        columns=(
            "transaction_id", "order_id", "transaction_date", "customer_id", "product_id",
            "product_name", "category", "quantity", "unit_price", "revenue",
        ),
    )

    summaries = build_summaries(cleaned)

    assert summaries["monthly_revenue"].set_index("month").loc["2025-01", "revenue"] == 25.0
    assert summaries["top_products"].iloc[0]["product_name"] == "Mouse"
    assert summaries["repeat_customers"]["customer_id"].tolist() == ["C1"]
    assert summaries["copurchases"].iloc[0].to_dict() == {
        "product_a": "Mouse", "product_b": "Mug", "order_count": 1,
    }


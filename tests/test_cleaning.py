from __future__ import annotations

import pandas as pd
import pytest

from retail_sales.cleaning import SchemaError, clean_transactions


def sample_frame() -> pd.DataFrame:
    columns = (
        "transaction_id", "order_id", "transaction_date", "customer_id", "product_id",
        "product_name", "category", "quantity", "unit_price",
    )
    return pd.DataFrame(
        [
            ["TX-1", "O-1", "2025-01-01", "C-1", "P-1", "Mouse", "Electronics", "2", "10.25"],
            ["TX-1", "O-1", "2025-01-01", "C-1", "P-1", "Mouse", "Electronics", "2", "10.25"],
            ["TX-2", "O-2", "bad-date", "C-2", "P-2", "Mug", "Home", "1", "5.00"],
            ["TX-3", "O-3", "2025-01-03", "", "P-2", "Mug", "Home", "1.5", "-1"],
        ],
        columns=columns,
    )


def test_cleaning_quarantines_duplicates_and_invalid_rows():
    result = clean_transactions(sample_frame())

    assert result.input_count == 4
    assert result.duplicate_count == 1
    assert len(result.accepted) == 1
    assert len(result.rejected) == 3
    reasons = " ".join(result.rejected["rejection_reason"])
    assert "duplicate transaction_id" in reasons
    assert "invalid transaction_date" in reasons
    assert "missing required identifier" in reasons
    assert "quantity must be a positive integer" in reasons
    assert "unit_price must be positive" in reasons


def test_revenue_is_quantity_times_price():
    result = clean_transactions(sample_frame())
    assert result.accepted.iloc[0]["revenue"] == pytest.approx(20.50)


def test_missing_columns_raise_schema_error():
    with pytest.raises(SchemaError, match="missing required columns"):
        clean_transactions(pd.DataFrame({"transaction_id": ["TX-1"]}))


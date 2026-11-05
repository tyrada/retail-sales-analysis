"""Validation and cleaning rules for retail transaction data."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REQUIRED_COLUMNS = (
    "transaction_id", "order_id", "transaction_date", "customer_id", "product_id",
    "product_name", "category", "quantity", "unit_price",
)


class SchemaError(ValueError):
    """Raised when a dataset does not contain the expected columns."""


@dataclass(frozen=True)
class CleanResult:
    accepted: pd.DataFrame
    rejected: pd.DataFrame
    input_count: int
    duplicate_count: int


def clean_transactions(raw: pd.DataFrame) -> CleanResult:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in raw.columns]
    if missing_columns:
        raise SchemaError(f"missing required columns: {', '.join(missing_columns)}")

    work = raw.loc[:, REQUIRED_COLUMNS].copy()
    for column in REQUIRED_COLUMNS:
        work[column] = work[column].astype("string").str.strip()

    duplicate_mask = work["transaction_id"].duplicated(keep="first")
    duplicate_rows = work.loc[duplicate_mask].copy()
    duplicate_rows["rejection_reason"] = "duplicate transaction_id"
    candidates = work.loc[~duplicate_mask].copy()

    parsed_dates = pd.to_datetime(candidates["transaction_date"], format="%Y-%m-%d", errors="coerce")
    quantities = pd.to_numeric(candidates["quantity"], errors="coerce")
    prices = pd.to_numeric(candidates["unit_price"], errors="coerce")

    missing_id = candidates[["transaction_id", "order_id", "customer_id", "product_id"]].isna().any(axis=1)
    missing_id |= candidates[["transaction_id", "order_id", "customer_id", "product_id"]].eq("").any(axis=1)
    bad_date = parsed_dates.isna()
    bad_quantity = quantities.isna() | quantities.le(0) | quantities.mod(1).ne(0)
    bad_price = prices.isna() | prices.le(0)
    invalid_mask = missing_id | bad_date | bad_quantity | bad_price

    reasons = pd.Series("", index=candidates.index, dtype="string")
    rules = (
        (missing_id, "missing required identifier"),
        (bad_date, "invalid transaction_date"),
        (bad_quantity, "quantity must be a positive integer"),
        (bad_price, "unit_price must be positive"),
    )
    for mask, reason in rules:
        reasons.loc[mask] = reasons.loc[mask].apply(lambda current: f"{current}; {reason}".strip("; "))

    invalid_rows = candidates.loc[invalid_mask].copy()
    invalid_rows["rejection_reason"] = reasons.loc[invalid_mask]
    rejected = pd.concat([invalid_rows, duplicate_rows], ignore_index=True)

    accepted = candidates.loc[~invalid_mask].copy()
    accepted["transaction_date"] = parsed_dates.loc[~invalid_mask].dt.date
    accepted["quantity"] = quantities.loc[~invalid_mask].astype("int64")
    accepted["unit_price"] = prices.loc[~invalid_mask].round(2)
    accepted["revenue"] = (accepted["quantity"] * accepted["unit_price"]).round(2)
    accepted = accepted.sort_values(["transaction_date", "transaction_id"]).reset_index(drop=True)

    return CleanResult(accepted, rejected, len(raw), int(duplicate_mask.sum()))


"""
Feature engineering pipeline for Kestrel Home Returns Risk.

This module converts raw order-level data into model-ready features
using only information that can reasonably be available before dispatch.

Important leakage exclusions:
- pickup_scheduled_at
- last_service_event_type
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

LEAKAGE_COLUMNS = [
    "pickup_scheduled_at",
    "last_service_event_type",
]

NOTE_PATTERNS = {
    "has_call_before": r"\bcall before\b",
    "has_landmark": r"\blandmark\b",
    "has_gate": r"\bgate\b",
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def _safe_divide(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """
    Safely calculate numerator / denominator.

    Returns 0 when denominator is zero.
    """
    return np.where(
        denominator > 0,
        numerator / denominator,
        0.0,
    )


def _add_customer_features(
    df: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge customer reference data and create customer-level features.
    """

    customer_cols = [
        "customer_id",
        "city",
        "state",
        "signup_date",
        "shield_member",
    ]

    customer_data = customers[customer_cols].copy()

    df = df.merge(
        customer_data,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    # Historical return behaviour.
    # These are available before the current order and therefore
    # are valid dispatch-time features.
    df["prior_return_rate"] = _safe_divide(
        df["customer_prior_returns"],
        df["customer_prior_orders"],
    )

    # Customer has any previous order.
    df["has_prior_orders"] = (
        df["customer_prior_orders"] > 0
    ).astype(int)

    # Customer has returned something previously.
    df["has_prior_returns"] = (
        df["customer_prior_returns"] > 0
    ).astype(int)

    return df


def _add_product_features(
    df: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge product reference data and create product-level features.
    """

    product_cols = [
        "sku",
        "family",
        "model_name",
        "list_price_inr",
        "warranty_months",
        "launch_date",
    ]

    product_data = products[product_cols].copy()

    df = df.merge(
        product_data,
        on="sku",
        how="left",
        validate="many_to_one",
    )

    # Convert dates before calculating product age.
    df["launch_date"] = pd.to_datetime(
        df["launch_date"],
        errors="coerce",
    )

    # Product age in days when the order was placed.
    df["product_age_days"] = (
        df["order_placed_at"] - df["launch_date"]
    ).dt.days

    # Protect against unexpected negative values.
    df["product_age_days"] = (
        df["product_age_days"]
        .clip(lower=0)
    )

    # Difference between stored order value and product list price.
    # This can capture the effective pricing relationship.
    df["price_to_list_ratio"] = (
        df["order_value_inr"]
        / df["list_price_inr"].replace(0, np.nan)
    )

    df["price_to_list_ratio"] = (
        df["price_to_list_ratio"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    return df


def _add_time_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create dispatch-time calendar features from order timestamp.
    """

    df["order_placed_at"] = pd.to_datetime(
        df["order_placed_at"],
        errors="coerce",
    )

    df["order_hour"] = df["order_placed_at"].dt.hour

    df["order_day_of_week"] = (
        df["order_placed_at"].dt.dayofweek
    )

    df["order_day"] = (
        df["order_placed_at"].dt.day
    )

    df["order_month"] = (
        df["order_placed_at"].dt.month
    )

    df["order_quarter"] = (
        df["order_placed_at"].dt.quarter
    )

    return df


def _add_delivery_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create delivery-related features that are available before dispatch.
    """

    # 000000 means the system default pincode was used.
    df["has_default_pincode"] = (
        df["delivery_pincode"] == 0
    ).astype(int)

    # Pincode as categorical rather than a continuous number.
    df["delivery_pincode"] = (
        df["delivery_pincode"]
        .fillna(0)
        .astype(str)
    )

    return df


def _add_note_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extract a small number of interpretable indicators from delivery notes.

    Raw delivery_note is intentionally not passed to the model.
    """

    note_text = (
        df["delivery_note"]
        .fillna("")
        .astype(str)
    )

    for feature_name, pattern in NOTE_PATTERNS.items():
        df[feature_name] = (
            note_text
            .str.contains(
                pattern,
                case=False,
                regex=True,
                na=False,
            )
            .astype(int)
        )

    return df


# ---------------------------------------------------------------------
# Main feature pipeline
# ---------------------------------------------------------------------

def build_features(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    is_train: bool = False,
) -> pd.DataFrame:
    """
    Build model-ready features from raw Kestrel order data.

    Parameters
    ----------
    orders:
        Raw train or test order dataframe.

    customers:
        Customer reference dataframe.

    products:
        Product reference dataframe.

    is_train:
        If True, preserves the `returned` target column.

    Returns
    -------
    pd.DataFrame
        Model-ready feature dataframe.
    """

    df = orders.copy()

    # -------------------------------------------------------------
    # 1. Remove columns that represent post-return operational state
    # -------------------------------------------------------------

    df = df.drop(
        columns=LEAKAGE_COLUMNS,
        errors="ignore",
    )

    # -------------------------------------------------------------
    # 2. Date parsing
    # -------------------------------------------------------------

    df["order_placed_at"] = pd.to_datetime(
        df["order_placed_at"],
        errors="coerce",
    )

    # -------------------------------------------------------------
    # 3. Customer features
    # -------------------------------------------------------------

    df = _add_customer_features(
        df,
        customers,
    )

    # -------------------------------------------------------------
    # 4. Product features
    # -------------------------------------------------------------

    df = _add_product_features(
        df,
        products,
    )

    # -------------------------------------------------------------
    # 5. Time features
    # -------------------------------------------------------------

    df = _add_time_features(df)

    # -------------------------------------------------------------
    # 6. Delivery features
    # -------------------------------------------------------------

    df = _add_delivery_features(df)

    # -------------------------------------------------------------
    # 7. Delivery-note indicators
    # -------------------------------------------------------------

    df = _add_note_features(df)

    # -------------------------------------------------------------
    # 8. Additional numerical transformations
    # -------------------------------------------------------------

    # Order values are highly skewed, so log transformation gives
    # models another smoother representation.
    df["log_order_value"] = np.log1p(
        df["order_value_inr"].clip(lower=0)
    )

    # Log transform customer order history as well.
    df["log_customer_prior_orders"] = np.log1p(
        df["customer_prior_orders"].clip(lower=0)
    )

    # -------------------------------------------------------------
    # 9. Remove raw text / identifiers that should not be directly
    #    learned by the baseline model.
    # -------------------------------------------------------------

    columns_to_drop = [
        "order_id",
        "order_placed_at",
        "customer_id",
        "sku",
        "model_name",
        "delivery_note",
        "signup_date",
        "launch_date",
    ]

    # Keep target only when processing training data.
    if not is_train:
        columns_to_drop.append("returned")

    df = df.drop(
        columns=columns_to_drop,
        errors="ignore",
    )

    # -------------------------------------------------------------
    # 10. Convert binary Y/N fields
    # -------------------------------------------------------------

    binary_mapping = {
        "Y": 1,
        "N": 0,
    }

    for column in ["is_gift", "shield_member"]:
        if column in df.columns:
            df[column] = (
                df[column]
                .map(binary_mapping)
                .fillna(0)
                .astype(int)
            )

    # -------------------------------------------------------------
    # 11. Handle obvious numeric missing values
    # -------------------------------------------------------------

    numeric_columns = df.select_dtypes(
        include=["number"]
    ).columns

    for column in numeric_columns:
        df[column] = (
            df[column]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
        )

    # -------------------------------------------------------------
    # 12. Ensure categorical columns are strings
    # -------------------------------------------------------------

    categorical_columns = [
        "sales_channel",
        "payment_mode",
        "source",
        "family",
        "city",
        "state",
        "delivery_pincode",
    ]

    for column in categorical_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .fillna("UNKNOWN")
                .astype(str)
            )

    return df


# ---------------------------------------------------------------------
# Convenience function for train + test
# ---------------------------------------------------------------------

def prepare_train_test(
    train: pd.DataFrame,
    test: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
):
    """
    Prepare training and test feature matrices.

    Returns
    -------
    X_train, y_train, X_test
    """

    train_features = build_features(
        train,
        customers,
        products,
        is_train=True,
    )

    test_features = build_features(
        test,
        customers,
        products,
        is_train=False,
    )

    y_train = train_features.pop("returned")

    # Make sure train/test have exactly the same columns.
    X_train, X_test = train_features.align(
        test_features,
        join="left",
        axis=1,
        fill_value=0,
    )

    return X_train, y_train, X_test
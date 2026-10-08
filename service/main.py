from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.features.feature_pipeline import build_features


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "models" / "return_risk_catboost.cbm"
CUSTOMERS_PATH = PROJECT_ROOT / "data" / "customers.csv"
PRODUCTS_PATH = PROJECT_ROOT / "data" / "products.csv"
TRAIN_PATH = PROJECT_ROOT / "data" / "train.csv"


# ---------------------------------------------------------------------
# Load model and reference data
# ---------------------------------------------------------------------

model = CatBoostClassifier()

try:
    model.load_model(str(MODEL_PATH))
except Exception as exc:
    raise RuntimeError(
        f"Could not load model from {MODEL_PATH}: {exc}"
    )

try:
    customers = pd.read_csv(CUSTOMERS_PATH)
    products = pd.read_csv(PRODUCTS_PATH)
    train = pd.read_csv(TRAIN_PATH)
except Exception as exc:
    raise RuntimeError(
        f"Could not load reference data: {exc}"
    )


# ---------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------

app = FastAPI(
    title="Kestrel Home Returns Risk API",
    description="Pre-dispatch return risk scoring service.",
    version="1.0.0",
)


# ---------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------

class OrderRequest(BaseModel):
    order_id: str
    customer_id: str
    sku: str

    order_placed_at: str
    sales_channel: str
    payment_mode: str
    delivery_pincode: int | str
    source: str

    discount_pct: float
    qty: int
    order_value_inr: float
    promised_delivery_days: float

    is_gift: str
    delivery_note: str = ""

    customer_prior_orders: int
    customer_prior_returns: int


# ---------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "Kestrel Home Returns Risk API",
        "status": "running",
        "model": "CatBoost",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": MODEL_PATH.exists(),
        "customers_loaded": len(customers),
        "products_loaded": len(products),
        "training_rows_available": len(train),
    }


# ---------------------------------------------------------------------
# Prediction endpoint
# ---------------------------------------------------------------------

@app.post("/predict")
def predict(order: OrderRequest):

    try:
        # Convert incoming JSON to DataFrame
        order_df = pd.DataFrame(
            [order.model_dump()]
        )

        # Build exactly the same feature structure
        # used during model training.
        features = build_features(
            orders=order_df,
            customers=customers,
            products=products,
            is_train=False,
            bucket_reference=train,
        )

        # Ensure feature order matches the trained model.
        expected_features = model.feature_names_

        missing_features = [
            feature
            for feature in expected_features
            if feature not in features.columns
        ]

        if missing_features:
            raise ValueError(
                f"Missing model features: {missing_features}"
            )

        # Ignore accidental extra columns and enforce
        # the exact training feature order.
        features = features[expected_features]

        # Continuous return-risk probability.
        score = float(
            model.predict_proba(features)[0][1]
        )

        # Operational risk level.
        if score >= 0.70:
            risk_level = "HIGH"
            action = "Review / confirmation call"
        elif score >= 0.40:
            risk_level = "MEDIUM"
            action = "Consider confirmation call"
        else:
            risk_level = "LOW"
            action = "Proceed normally"

        # -------------------------------------------------------------
        # Employee-readable reasons
        # -------------------------------------------------------------

        reasons = []

        prior_orders = order.customer_prior_orders
        prior_returns = order.customer_prior_returns

        if prior_orders > 0:
            customer_return_rate = (
                prior_returns / prior_orders
            )
        else:
            customer_return_rate = 0.0

        if customer_return_rate >= 0.30:
            reasons.append(
                f"Customer historical return rate is "
                f"{customer_return_rate:.0%}."
            )

        if prior_returns > 0:
            reasons.append(
                "Customer has previous return history."
            )

        if order.discount_pct >= 30:
            reasons.append(
                "Order has a relatively high discount."
            )

        if order.order_value_inr >= 30000:
            reasons.append(
                "Order value is relatively high."
            )

        if str(order.is_gift).upper() == "Y":
            reasons.append(
                "Order is marked as a gift."
            )

        if not reasons:
            reasons.append(
                "Risk is driven by the combined order, "
                "customer, product and delivery features."
            )

        return {
            "order_id": order.order_id,
            "return_risk_score": round(score, 4),
            "risk_level": risk_level,
            "recommended_action": action,
            "reasons": reasons[:3],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed: {str(exc)}",
        )
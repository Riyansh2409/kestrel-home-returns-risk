import requests
import streamlit as st


# ============================================================
# Configuration
# ============================================================

API_URL = "http://127.0.0.1:8000/predict"


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Kestrel Returns Risk",
    page_icon="📦",
    layout="centered",
)


# ============================================================
# Custom styling
# ============================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #666;
            margin-bottom: 1.5rem;
        }

        .risk-score {
            font-size: 3rem;
            font-weight: 700;
            text-align: center;
            margin-top: 0.5rem;
        }

        .risk-label {
            font-size: 1.3rem;
            font-weight: 600;
            text-align: center;
        }

        .result-box {
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #ddd;
            margin-top: 1rem;
        }

        .reason-item {
            padding: 0.35rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Header
# ============================================================

st.markdown(
    '<div class="main-title">Kestrel Returns Risk</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Pre-dispatch return risk scoring for incoming orders'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# Order Information
# ============================================================

st.subheader("Order Information")

col1, col2 = st.columns(2)

with col1:
    order_id = st.text_input(
        "Order ID",
        value="TEST001",
    )

    customer_id = st.text_input(
        "Customer ID",
        value="CUST00001",
    )

    sku = st.text_input(
        "SKU",
        value="SKU001",
    )

    sales_channel = st.selectbox(
        "Sales Channel",
        [
            "Online",
            "Store",
            "Partner",
        ],
    )

    payment_mode = st.selectbox(
        "Payment Mode",
        [
            "COD",
            "UPI",
            "Credit Card",
            "Debit Card",
            "Net Banking",
        ],
    )

with col2:
    order_value = st.number_input(
        "Order Value (₹)",
        min_value=0.0,
        value=25000.0,
        step=500.0,
    )

    discount_pct = st.number_input(
        "Discount (%)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=1.0,
    )

    qty = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1,
    )

    promised_delivery_days = st.number_input(
        "Promised Delivery Days",
        min_value=1.0,
        value=5.0,
        step=1.0,
    )

    delivery_pincode = st.number_input(
        "Delivery Pincode",
        min_value=0,
        value=560001,
        step=1,
    )


# ============================================================
# Additional Information
# ============================================================

st.subheader("Customer & Delivery Information")

col3, col4 = st.columns(2)

with col3:
    source = st.selectbox(
        "Order Source",
        [
            "Website",
            "Mobile App",
            "Partner",
            "Store",
        ],
    )

    customer_prior_orders = st.number_input(
        "Customer Prior Orders",
        min_value=0,
        value=5,
        step=1,
    )

    customer_prior_returns = st.number_input(
        "Customer Prior Returns",
        min_value=0,
        value=2,
        step=1,
    )

with col4:
    is_gift = st.selectbox(
        "Gift Order",
        ["N", "Y"],
    )

    delivery_note = st.text_input(
        "Delivery Note",
        value="Call before delivery",
    )

    order_placed_at = st.text_input(
        "Order Date & Time",
        value="2026-06-15 14:30:00",
    )


# ============================================================
# Prediction Button
# ============================================================

st.divider()

predict_button = st.button(
    "🔍 Score Return Risk",
    type="primary",
    use_container_width=True,
)


# ============================================================
# Prediction
# ============================================================

if predict_button:

    # Basic validation
    if not order_id.strip():
        st.error("Order ID is required.")

    elif not customer_id.strip():
        st.error("Customer ID is required.")

    elif not sku.strip():
        st.error("SKU is required.")

    elif customer_prior_returns > customer_prior_orders:
        st.error(
            "Customer prior returns cannot exceed prior orders."
        )

    else:

        payload = {
            "order_id": order_id,
            "customer_id": customer_id,
            "sku": sku,
            "order_placed_at": order_placed_at,
            "sales_channel": sales_channel,
            "payment_mode": payment_mode,
            "delivery_pincode": delivery_pincode,
            "source": source,
            "discount_pct": discount_pct,
            "qty": qty,
            "order_value_inr": order_value,
            "promised_delivery_days": promised_delivery_days,
            "is_gift": is_gift,
            "delivery_note": delivery_note,
            "customer_prior_orders": customer_prior_orders,
            "customer_prior_returns": customer_prior_returns,
        }

        try:

            with st.spinner("Scoring order..."):

                response = requests.post(
                    API_URL,
                    json=payload,
                    timeout=30,
                )

            # ----------------------------------------------------
            # Successful prediction
            # ----------------------------------------------------

            if response.status_code == 200:

                result = response.json()

                score = result["return_risk_score"]
                risk_level = result["risk_level"]
                action = result["recommended_action"]
                reasons = result.get("reasons", [])

                st.divider()

                st.subheader("Prediction Result")

                # Score
                st.markdown(
                    f"""
                    <div class="result-box">
                        <div class="risk-score">
                            {score:.2%}
                        </div>
                        <div class="risk-label">
                            {risk_level} RETURN RISK
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.progress(
                    min(max(score, 0.0), 1.0)
                )

                # Action
                st.markdown("### Recommended Action")

                if risk_level == "HIGH":
                    st.error(action)

                elif risk_level == "MEDIUM":
                    st.warning(action)

                else:
                    st.success(action)

                # Reasons
                st.markdown("### Why this score?")

                if reasons:

                    for reason in reasons:

                        st.markdown(
                            f'<div class="reason-item">• {reason}</div>',
                            unsafe_allow_html=True,
                        )

                else:

                    st.info(
                        "No specific reason was returned."
                    )

            # ----------------------------------------------------
            # API error
            # ----------------------------------------------------

            else:

                try:
                    error_detail = response.json().get(
                        "detail",
                        "Unknown API error.",
                    )
                except Exception:
                    error_detail = response.text

                st.error(
                    f"Prediction failed: {error_detail}"
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to the prediction API. "
                "Make sure FastAPI is running on "
                "http://127.0.0.1:8000"
            )

        except requests.exceptions.Timeout:

            st.error(
                "The prediction API took too long to respond."
            )

        except Exception as exc:

            st.error(
                f"Unexpected error: {exc}"
            )


# ============================================================
# Footer
# ============================================================

st.divider()

st.caption(
    "Model: CatBoost | API: FastAPI | "
    "Scoring is based on pre-dispatch order information."
)
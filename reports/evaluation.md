# Model Evaluation

## 1. Evaluation Objective

The objective of the evaluation is to determine whether the model can reliably rank orders according to their likelihood of being returned before dispatch.

The evaluation focuses on:

- Ranking quality using ROC-AUC and PR-AUC.
- Precision and recall for identifying potential returns.
- F1 score for balancing precision and recall.
- Threshold selection for operational use.
- False-positive and false-negative behavior.
- Feature importance and potential data leakage.

Accuracy is not treated as the primary metric because returned orders are a minority class.

---

## 2. Dataset Split

A time-based validation strategy was used instead of a random train-test split.

| Dataset | Period | Rows |
|---|---|---:|
| Training | Apr 2025 - Apr 2026 | 9,654 |
| Validation | May 2026 - Jun 2026 | 1,501 |
| Full Training Data | Historical training period | 11,155 |
| Final Test | Unlabelled recent orders | 2,096 |

The time-based split better represents the intended production scenario: historical orders are used to predict outcomes for later orders.

---

## 3. Class Distribution

The training data contains a relatively small proportion of returned orders.

### Training

- Total orders: 11,155
- Return rate: 11.39%

### Validation

- Total orders: 1,501
- Returned: 167
- Not returned: 1,334
- Return rate: 11.13%

Because approximately 88.87% of validation orders were not returned, a model that predicted "not returned" for every order would already achieve approximately 88.87% accuracy.

Therefore, accuracy alone would provide a misleading view of model performance.

---

## 4. Model Comparison

Three classification approaches were evaluated on the time-based validation set.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.776 | 0.259 | 0.545 | 0.351 | 0.759 | 0.362 |
| Random Forest | 0.727 | 0.229 | 0.617 | 0.334 | 0.745 | 0.311 |
| CatBoost | **0.805** | **0.290** | 0.521 | **0.373** | **0.758** | **0.361** |

CatBoost was selected as the final model because it provided the strongest overall F1 score and competitive ranking performance while handling the mixture of categorical and numerical features effectively.

---

## 5. Final CatBoost Model

The final model uses:

```text
CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.05,
    loss_function="Logloss",
    eval_metric="AUC",
    random_seed=42,
    auto_class_weights="Balanced"
)
```

---

## 6. Final Validation Performance

At the default classification threshold of 0.50, the CatBoost model achieved:

| Metric | Result |
|---|---:|
| Accuracy | 0.805 |
| Precision | 0.290 |
| Recall | 0.521 |
| F1 | 0.373 |
| ROC-AUC | 0.758 |
| PR-AUC | 0.361 |

Confusion matrix at threshold 0.50:

```text
                Predicted
              No Return  Return
Actual
No Return        1121      213
Return             80       87
```

This means:

- True Negatives: 1,121
- False Positives: 213
- False Negatives: 80
- True Positives: 87

---

## 7. Threshold Selection

The model produces continuous probability scores rather than only binary predictions.

Different thresholds produce different operational trade-offs between:

- Catching more actual returns.
- Reducing unnecessary operational interventions.
- Maintaining useful precision.

A threshold sweep was performed on the validation set.

The strongest F1 score occurred at a threshold of approximately **0.55**.

### Threshold = 0.55

| Metric | Result |
|---|---:|
| Accuracy | 0.835 |
| Precision | 0.331 |
| Recall | 0.473 |
| F1 | 0.389 |
| Orders flagged | 239 |
| True returns caught | 79 |
| False holds | 160 |
| Missed returns | 88 |

At this threshold:

- 239 of 1,501 validation orders were flagged.
- Flag rate was approximately 15.9%.
- 79 of 167 actual returns were identified.
- 160 non-returning orders were incorrectly flagged.
- 88 actual returns were missed.

The threshold is therefore treated as a **candidate operational threshold**, not a guaranteed optimal business policy.

---

## 8. Why 0.55?

The threshold was not selected simply because a probability of 0.50 is conventional.

The threshold was evaluated against the validation data to understand the trade-off between:

- Catching more actual returns.
- Reducing unnecessary operational interventions.
- Maintaining useful precision.

At 0.55, the F1 score improved from approximately 0.373 at the default 0.50 threshold to approximately 0.389.

The threshold should be revisited after deployment using actual intervention outcomes and business costs.

---

## 9. Operational Error Analysis

At the 0.55 threshold:

### False Positives

160 non-returning orders were flagged.

This represents approximately:

```text
160 / 1334 = 11.99%
```

of non-returning validation orders.

These orders represent the main operational cost of using the model, because an employee may spend time reviewing or calling customers who would not have returned the order anyway.

### False Negatives

88 actual returns were not flagged.

This represents approximately:

```text
88 / 167 = 52.69%
```

of actual returns in the validation period.

This shows that the model should not be interpreted as a system that catches every return.

Its purpose is to prioritize higher-risk orders for intervention.

---

## 10. Business Cost Context

The provided business information states:

- Incremental cost of a return: **₹1,150**
- Confirmation call cost: **₹45**
- Confirmation-call pilot reduction in otherwise-expected returns: approximately **35%**

The estimated avoided return cost per prevented return under the pilot assumption is:

```text
35% × ₹1,150 = ₹402.50
```

The corresponding simple break-even probability for a confirmation call is:

```text
₹45 / ₹402.50 ≈ 11.2%
```

This indicates that confirmation calls can potentially be economically useful for sufficiently high-risk orders.

This calculation is an economic planning estimate based on the reported pilot effect. It does not establish guaranteed savings.

No cancellation cost is assumed because no cancellation rupee cost was provided.

---

## 11. Feature Importance

The model's highest feature-importance values included:

| Feature | Importance |
|---|---:|
| sales_channel | 9.46 |
| payment_mode | 8.38 |
| promised_delivery_days | 6.53 |
| product_age_days | 5.75 |
| city | 5.42 |
| delivery_pincode | 5.40 |
| family | 5.24 |
| order_hour | 4.91 |
| discount_pct | 4.26 |
| order_day | 4.05 |
| state | 3.63 |
| shield_member | 3.55 |
| price_to_list_ratio | 3.51 |
| order_month | 3.28 |
| log_order_value | 3.25 |

Feature importance indicates which features contributed more to the model's predictions.

It does **not** establish that a feature causes a customer to return an order.

The project also includes the generated feature-importance artifacts:

```text
outputs/feature_importance.csv
outputs/feature_importance.png
```

---

## 12. Leakage Prevention

The prediction task is defined as a pre-dispatch decision.

Therefore, information that becomes available only after the return or during later operational processing must not be used.

The following fields were excluded from model features:

```text
last_service_event_type
pickup_scheduled_at
```

These fields can contain information that occurs after or around the return process and could allow the model to indirectly observe the outcome it is supposed to predict.

The feature pipeline also avoids using raw identifiers and post-outcome information as predictive features.

---

## 13. Feature Engineering

The final feature pipeline combines:

### Customer Information

- Historical order count
- Historical return count
- Historical return rate
- Prior-return indicator
- Shield membership

### Product Information

- Product family
- List price
- Warranty period
- Product age

### Order Information

- Order value
- Quantity
- Discount percentage
- Payment mode
- Sales channel

### Delivery Information

- Promised delivery days
- Delivery pincode
- City
- State
- Delivery note indicators

### Time Information

- Order month
- Order day
- Order quarter
- Order hour
- Day of week

### Derived Features

- Price-to-list-price ratio
- Log order value
- Log customer order count
- Discount bucket
- Prior return-rate bucket
- Order-value bucket

The categorical bucket boundaries used during inference are based on the training data to avoid inconsistent feature construction between training and prediction.

---

## 14. Test Predictions

The final model generated predictions for:

**2,096 unlabelled test orders.**

The submission file contains:

```text
order_id,score
```

Validation checks performed on the output:

- 2,096 prediction rows
- 2,096 unique order IDs
- No duplicate order IDs
- No missing scores
- Continuous probability scores between 0 and 1

The final submission file is:

```text
outputs/predictions.csv
```

The model therefore provides a continuous risk score for ranking and operational prioritization rather than only producing a binary return/no-return label.

---

## 15. Limitations

Several limitations should be considered before production deployment.

### Historical Data

The model is trained on historical order behavior. Future customer behavior and operational conditions may differ.

### Model Recall

At the 0.55 threshold, the model misses a substantial proportion of actual returns. It should therefore not be treated as a complete return-prevention system.

### False Positives

Some non-returning orders are flagged. Operational teams should account for the cost and capacity of reviewing or calling these customers.

### Pilot Assumption

The economic calculation assumes that the reported 35% reduction from the confirmation-call pilot applies to the current population. This needs to be validated experimentally.

### Threshold Stability

The 0.55 threshold was selected using the available validation period. The optimal threshold may change as customer behavior, products, channels, or intervention costs change.

### Explainability

The employee-readable reasons provided by the application are supporting indicators derived from order/customer information. They are not formal causal explanations of individual predictions.

---

## 16. Recommended Production Evaluation

Before using the model as a permanent operational rule, run a controlled pilot.

For each upcoming order:

1. Generate the model risk score.
2. Flag orders above the candidate threshold.
3. Apply the confirmation-call intervention according to the operational policy.
4. Record whether the customer was contacted.
5. Record the eventual return outcome.
6. Compare intervention and control groups.
7. Measure actual return reduction and financial impact.
8. Reassess the operating threshold.

The most important production metrics should include:

- Return rate
- Return reduction among contacted customers
- Precision of flagged orders
- Recall of actual returns
- Confirmation-call conversion
- Cost per prevented return
- Net financial impact
- Operational workload

This would provide stronger evidence of business value than offline model metrics alone.

---

## 17. Conclusion

The final CatBoost model provides a useful ranking signal for pre-dispatch return risk.

The time-based validation results show:

- ROC-AUC: **0.758**
- PR-AUC: **0.361**
- F1 at 0.50: **0.373**
- F1 at 0.55: **0.389**
- Candidate operational threshold: **0.55**

The model should be deployed as a **decision-support and prioritization system**, not as an automatic cancellation mechanism.

The recommended next step is a controlled operational pilot that measures whether targeted confirmation calls actually reduce returns and generate positive net financial impact.
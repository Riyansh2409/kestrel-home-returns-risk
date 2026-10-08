# Memo to Ritu

**Subject:** Pre-dispatch Returns Risk Model

## Executive Summary

Kestrel Home Appliances can use a pre-dispatch machine learning model to identify orders that are more likely to be returned.

The model produces a continuous return-risk score for every order. A validation-based candidate threshold of **0.55** can be used to identify orders for operational review or a confirmation call.

The objective is not to automatically reject or cancel orders. Instead, the score provides an early-warning signal so that the operations team can focus attention on orders with higher estimated return risk.

## Model Performance

The model was evaluated using a time-based validation split, with older orders used for training and later orders used for validation.

The final CatBoost model achieved:

| Metric | Validation Result |
|---|---:|
| ROC-AUC | 0.758 |
| PR-AUC | 0.361 |
| Precision | 0.291 |
| Recall | 0.521 |
| F1 Score | 0.373 |

Accuracy was **80.5%**, but accuracy is not treated as the primary metric because returns are relatively uncommon. A model that simply predicted "not returned" for every order would already achieve approximately **88.9% accuracy** on the validation period.

The model therefore focuses more on ranking and identifying return-risk orders than on maximizing raw accuracy.

## Operational Threshold

A threshold of **0.55** was selected as a candidate operating point based on the validation-set F1 score.

At this threshold:

- **239 of 1,501** validation orders were flagged.
- Flag rate: **15.9%**
- **79 actual returns** were correctly identified.
- **88 actual returns** were missed.
- **160 non-returning orders** were incorrectly flagged.

This means the threshold should be treated as an operational starting point rather than a guaranteed decision rule.

The recommended workflow is to use the model as a **review / confirmation-call signal**, rather than automatically holding or cancelling every flagged order.

## Business Economics

The business information provided states:

- Incremental cost of a return: **₹1,150**
- Confirmation call cost: **₹45**
- Spring confirmation-call pilot reduced otherwise-expected returns by approximately **35%**

Using these figures, the expected avoided return cost from a successful confirmation call is approximately:

**35% × ₹1,150 = ₹402.50**

The simple break-even probability for a confirmation call is therefore approximately:

**₹45 / ₹402.50 = 11.2%**

This suggests that a confirmation call can be economically attractive when the estimated probability of return is sufficiently high.

However, this calculation is a planning estimate based on the reported pilot effect. It should not be interpreted as guaranteed savings.

## Recommendation

Use the model as a pre-dispatch decision-support tool:

1. Generate a return-risk score for every order.
2. Use **0.55** as the initial candidate threshold for operational review.
3. Prioritize flagged orders for a confirmation call or manual review.
4. Do not automatically cancel or reject orders solely because they receive a high score.
5. Monitor actual return outcomes and confirmation-call results after deployment.
6. Recalibrate the threshold using real operational results and the actual cost of interventions.

This approach allows Kestrel to focus limited operational effort on a smaller group of orders instead of contacting every customer.

## Important Limitations

The validation results come from historical data and should not be treated as a guarantee of future performance.

The model also does not use fields that are only known after the return or during later operational processing, such as post-return service or pickup information.

The current model provides risk scores and supporting employee-readable reasons. The reasons are intended as operational indicators and should not be interpreted as formal causal explanations of why an order will be returned.

The economic estimate also depends on the confirmation-call pilot effect continuing to apply to the current customer and order population.

## Next Step

The recommended next step is a controlled operational pilot.

Run the model on upcoming orders, apply the candidate threshold, record which flagged customers receive confirmation calls, and compare subsequent return outcomes against an appropriate control group.

This will allow Kestrel to estimate the model's real-world lift, intervention effectiveness, and actual financial impact before making the workflow a permanent part of the dispatch process.
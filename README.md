# Kestrel Home Returns Risk

Pre-dispatch machine learning system for identifying orders that are more likely to be returned.

The system produces a continuous return-risk score for each order and provides an operational risk level and employee-readable reasons through a FastAPI service and Streamlit interface.

---

## 1. Problem

Kestrel Home Appliances wants to identify potentially high-risk orders before dispatch.

The goal is to:

- Score the probability that an order will be returned.
- Avoid using information that becomes available only after a return.
- Provide an operational signal that can support confirmation calls or review.
- Produce continuous risk scores for the final test orders.

---

## 2. Project Architecture

```text
Raw Order
   |
   v
Feature Engineering
   |
   +--> Customer history
   +--> Product information
   +--> Order information
   +--> Delivery information
   +--> Time features
   +--> Bucket features
   |
   v
CatBoost Classifier
   |
   v
Return Risk Score
   |
   +--> Risk Level
   +--> Recommended Action
   +--> Employee-readable Reasons



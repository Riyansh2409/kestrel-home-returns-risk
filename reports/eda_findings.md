# Kestrel Home Returns Risk — EDA Findings

## 1. Dataset Overview

- Training rows: 11,155
- Unique order IDs: 10,504
- Duplicate order IDs: 651
- Conflicting duplicate labels: 0
- Training period: April 2025 to June 2026
- Test period: July 2026 to September 2026
- Overall return rate: 11.36%

## 2. Data Quality

- Customer IDs missing from reference data: 0
- SKUs missing from reference data: 0
- Duplicate customer IDs: 0
- Duplicate SKUs: 0
- `delivery_note` missing: 2,752 rows
- `pickup_scheduled_at` missing: 9,855 rows

## 3. Leakage Audit

`pickup_scheduled_at` and `last_service_event_type` were excluded.

`pickup_scheduled_at` showed a 91.62% return rate when present versus 0.77% when absent.

`REVERSE_PICKUP` had a 100% return rate.

These fields represent information from the return/service workflow and are not appropriate for a pre-dispatch prediction model.

## 4. Key EDA Findings

### Payment
COD had an 18.84% return rate, compared with 7.59% for prepaid UPI.

### Sales Channel
Marketplace had the highest return rate at 13.52%.

### Shield
Shield members had an 18.73% return rate versus 9.27% for non-members.

### Discount
Return rate generally increased with discount level, reaching 21.62% for the 31–40% discount bucket.

### Product Family
Robot Vacuum had the highest return rate at 19.27%.
Ceiling Fan had the lowest at 6.54%.

### Customer History
Customers with a 51–75% historical return rate had a 52.32% return rate on current orders.

### Delivery
Return rate generally increased with promised delivery days.

### Order Value
The highest order-value quintile had a 15.35% return rate versus around 9% in the lower/middle quintiles.

### Quantity
Quantity showed only a weak difference between quantity 1 and 2.

### Delivery Notes
Simple keyword analysis showed relatively weak effects. `call_before`, `gate`, and `landmark` were retained as candidate engineered features for validation, but are not treated as major drivers.

## 5. Feature Strategy

Use only information reasonably available before dispatch.

### Candidate features

- Customer history
- Shield membership
- Payment mode
- Sales channel
- Discount
- Quantity
- Order value
- Product attributes
- Promised delivery days
- Delivery pincode indicators
- Time features
- Selected delivery-note indicators

### Excluded

- `last_service_event_type`
- `pickup_scheduled_at`
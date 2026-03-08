# Starbucks Customer Ordering Patterns ☕

A customer segmentation project built from transactional Starbucks-style order data. This analysis moves from raw order-level records to customer-level behavioral features, then uses clustering to identify distinct customer groups.

## Project Overview 📌

The goal of this project is to understand how customers differ in terms of:

- spending behavior
- ordering frequency
- convenience preference
- customization habits
- satisfaction patterns

Instead of jumping straight into clustering, the notebook follows a structured workflow:

1. understand the dataset
2. check data quality
3. explore behavior with question-driven analysis
4. engineer customer-level features
5. run clustering and interpret the resulting segments

## Dataset Snapshot 📊

- `100,000` orders
- `14,988` unique customers
- `500` stores
- Date range: `2024-01-01` to `2025-12-30`
- Granularity: one row per order
- Duplicate `order_id` rows: `0`

Since the raw data is at the order level, segmentation was performed only after aggregating behavior at the `customer_id` level.

## Repository Contents 🗂️

- `starbucks_customer_segmentation.ipynb` : main analysis notebook
- `starbucks_customer_ordering_patterns.csv` : raw dataset
- `customer_segments_output.csv` : customer-level output with assigned segments
- `project_plan.md` : project roadmap and analysis flow

## Analysis Workflow 🔎

The notebook is organized into the following stages:

1. data loading and structure checks
2. numeric and categorical review
3. question-based exploratory analysis
4. customer-level aggregation
5. feature engineering for segmentation
6. feature validation and redundancy checks
7. K-Means clustering
8. segment profiling and business interpretation

## Key Findings ✨

### 1. Customer activity

- Customers placed about `6.7` orders each on average.
- The typical order contains around `3.7` items.
- Average customizations per order are about `1.8`.
- Average order value is `$14.87`.

This suggests the dataset contains repeat behavior strong enough for meaningful customer segmentation.

### 2. Channel behavior

- `Mobile App` is the largest channel with `42.5%` of all orders.
- `Drive-Thru` contributes `28.0%`.
- `In-Store Cashier` contributes `22.1%`.
- `Kiosk` contributes `7.4%`.
- Mobile App orders have the highest average spend at `$18.08`.

The biggest behavioral split in the data appears to come from convenience-oriented digital ordering versus more traditional channels.

### 3. Rewards members behave differently

Compared with non-members, rewards members:

- spend more per order (`$15.72` vs `$14.09`)
- have larger carts (`3.87` vs `3.63`)
- customize more (`2.00` vs `1.64`)
- use order-ahead much more often (`40.2%` vs `20.3%`)
- report slightly higher satisfaction (`3.73` vs `3.65`)

Rewards membership appears to be associated with stronger engagement and more digital convenience usage.

### 4. Satisfaction is linked to operational experience

- Satisfaction is highest when fulfillment is in the `3 to 5 minute` range.
- Satisfaction declines for slower orders, especially `7+ minutes`.
- `Mobile App` shows the highest average satisfaction (`3.86`).
- `Drive-Thru` shows the lowest average satisfaction (`3.44`) and the highest fulfillment time (`5.80` minutes).

This suggests fulfillment speed and channel experience both affect how customers perceive the service.

## Feature Engineering for Segmentation 🧠

Customer-level features were built from behavior, value, convenience, and timing patterns, including:

- `total_orders`
- `recency_days`
- `order_frequency`
- `avg_total_spend`
- `avg_cart_size`
- `avg_num_customizations`
- `food_order_rate`
- `order_ahead_rate`
- `avg_fulfillment_time`
- `avg_customer_satisfaction`
- `weekend_order_rate`
- channel mix rates
- time-of-day ordering rates

`total_revenue` was intentionally dropped from the final clustering input because it was highly correlated with `total_orders` (`r = 0.928`).

## Clustering Result 🤖

K-Means clustering was tested across multiple values of `k`.

- Best result in the notebook: `k = 2`
- Silhouette score: `0.1184`

### Segment 0: Digital Convenience Customers

- `48.8%` of customers
- higher average spend
- more customizations
- higher food order rate
- much higher order-ahead usage
- strong Mobile App preference

### Segment 1: Store-First Value Customers

- `51.2%` of customers
- lower average spend
- fewer customizations
- lower order-ahead usage
- lower Mobile App usage
- stronger Drive-Thru and In-Store presence

## Business Takeaway 💡

The strongest separation in this dataset is not simply frequent vs infrequent customers. The major difference is how customers order:

- digital vs traditional channel behavior
- convenience preference
- customization intensity
- average spend pattern
- order-ahead usage

This makes the segmentation useful for:

- personalized offers
- loyalty targeting
- channel-specific campaigns
- operational improvements for lower-satisfaction groups

## Tools and Libraries 🛠️

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn

## How to Run ▶️

Run the notebook locally:

```bash
jupyter notebook starbucks_customer_segmentation.ipynb
```

Then execute the cells in order.

## Future Scope 🚀

Possible next steps for this project:

- improve manual interpretation of the segments
- compare K-Means with other clustering approaches
- build a recommendation system using customer preferences and segment patterns
- connect segment outputs to marketing or retention strategies

## Final Note

This project was built with a simple principle: understand the data properly before modeling. The notebook focuses on step-by-step analysis so the segmentation results remain interpretable and business-relevant.

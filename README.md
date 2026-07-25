# Starbucks-Style Customer Segmentation and Analytics

This project explores customer behavior in a Kaggle order dataset and presents
the results through a notebook and a FastAPI dashboard. It is an independent
portfolio analysis and is not affiliated with Starbucks.

## Project Goal 🎯

The goal of this project is simple: understand how customers behave and group similar customers together in a way that is useful for business decisions.

I wanted to answer questions like:

- Who spends more?
- Who prefers mobile ordering?
- Who orders ahead more often?
- Who seems more value-focused?
- What kind of customer groups can help with offers, loyalty, and customer experience?

## Dataset

The raw CSV comes from Likitha Gedipudi's
[Starbucks Customer Ordering Patterns](https://www.kaggle.com/datasets/likithagedipudi/starbucks-customer-ordering-patterns)
dataset on Kaggle. It is a simulated 100,000-transaction dataset covering
2024–2025 and is published under the CC0 Public Domain license. See
[DATASET.md](DATASET.md) for the version, integrity hashes, validation contract,
and limitations.

Do not describe these rows as official Starbucks customer records.

- `100,000` order records
- `14,988` unique customers
- `500` stores
- Date range: `2024-01-01` to `2025-12-30`
- Each row represents one order
- Duplicate `order_id` rows: `0`

Since the data is at the order level, I first converted it into customer-level behavior before building segments.

## Project files

- `starbucks_customer_segmentation.ipynb`  
  Main notebook for analysis, feature creation, clustering, and segment interpretation.

- `app.py`  
  FastAPI backend for the dashboard.

- `templates/index.html`  
  Main dashboard layout.

- `static/app.js`  
  Frontend logic for charts and dashboard interactions.

- `static/style.css`  
  Dashboard styling.

- `starbucks_customer_ordering_patterns.csv`  
  Raw transactional dataset.

- `customer_segments_output.csv`  
  Customer-level dataset with final segment assignments.

- `analysis/`
  Reusable dataset validation and clustering evaluation code.

- `scripts/`
  Command-line checks that generate machine-readable validation evidence.

- `tests/` and `.github/workflows/ci.yml`
  API, data-contract, and model-evaluation tests run on every push and pull
  request.

## Method

The workflow followed these steps:

1. checked the structure of the dataset
2. reviewed missing values, summary statistics, and category distributions
3. explored the data with business questions first
4. built customer-level features from order history
5. tested clustering to separate customers into groups
6. reviewed the groups and gave them practical names
7. built a dashboard to explore the results

## Findings

Here are the main things I found, without the technical language.

### 1. Customers do come back

- The same customers appear many times in the data.
- On average, each customer placed about `6.7` orders.

This means the dataset is good for customer segmentation because it captures repeat behavior, not just one-time visits.

### 2. Mobile ordering is a big deal

- `Mobile App` is the biggest ordering channel.
- It accounts for `42.5%` of all orders.
- Mobile App orders also have the highest average spend at `$18.08`.

This tells us that digital behavior matters a lot. Some customers clearly prefer convenience and app-based ordering.

### 3. Rewards members behave differently

Compared with non-members, rewards members:

- spend more
- place slightly larger orders
- customize more
- use order-ahead much more often
- report slightly better satisfaction

In simple terms, rewards members look more engaged and more comfortable with digital convenience.

### 4. Speed affects satisfaction

- Satisfaction is strongest when orders are fulfilled in about `3 to 5 minutes`.
- Satisfaction drops when orders take longer.
- `Drive-Thru` has the lowest satisfaction and the slowest average fulfillment time.

This suggests that service speed and ordering experience both matter to customers.

### 5. The biggest customer difference is not order frequency

The two groups were not separated mainly by how often customers ordered.

The real difference was:

- how they order
- how much they spend
- whether they use the app
- whether they order ahead
- how much they customize

So the strongest split in this dataset is more about customer style than customer frequency.

## Customer segments

K-Means selected `k=2` because it had the highest tested silhouette score:
`0.1190`. That score is weak and indicates substantial overlap. The two groups
are useful as exploratory behavioral summaries, but they are not cleanly
separated personas and should not be treated as ground truth.

The final result produced two main customer groups.

### 1. Digital Convenience Customers

- `7,309` customers (`48.8%`)
- Higher average spend (`$16.49`)
- Larger carts
- More customizations
- Much higher order-ahead usage
- Strong Mobile App preference

In simple terms, these are the customers who like convenience, use digital channels more, and tend to spend more per order.

### 2. Store-First Value Customers

- `7,679` customers (`51.2%`)
- Lower average spend (`$13.33`)
- Smaller carts
- Fewer customizations
- Lower order-ahead usage
- More Drive-Thru and In-Store behavior

In simple terms, these customers look more traditional in how they order and seem more value-conscious.

## Business use

These segments can help answer real business questions:

- Which customers should get app-focused offers?
- Which customers may respond better to value bundles?
- Which customers are better targets for rewards sign-up campaigns?
- Which customer group may need better service experience?

That is why this segmentation is useful beyond just the model itself.

## Dashboard

Along with the notebook, I built a FastAPI dashboard to explore the results.

The dashboard includes:

- segment summaries
- customer search and profile view
- churn scoring
- drink recommendation logic
- campaign simulation by segment
- order trend analysis

## Tools

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- FastAPI
- Jinja2
- Chart.js

## Reproduce the checks

```bash
python -m pip install -r requirements-dev.txt
python -m scripts.validate_dataset
python -m scripts.evaluate_segmentation
coverage run --source=analysis -m unittest discover -s tests -v
coverage report --show-missing --fail-under=90
```

The clustering evaluation writes its metrics to
`artifacts/clustering_metrics.json`.

The coverage threshold applies to the reusable validation and clustering
modules. Dashboard routes have separate API smoke tests; the repository does
not claim 90% coverage for the full web application.

## Run locally

### Run the notebook

```bash
jupyter notebook starbucks_customer_segmentation.ipynb
```

### Run the dashboard

```bash
uvicorn app:app --reload --port 8000
```

Then open:

```bash
http://127.0.0.1:8000
```

## Container and deployment

```bash
docker build -t starbucks-segmentation .
docker run --rm -p 8000:8000 starbucks-segmentation
curl http://127.0.0.1:8000/api/health
```

The Docker configuration is compatible with services that provide a `PORT`
environment variable, including Railway. This repository does not claim a live
Railway deployment until a public service URL and successful health check are
recorded here.

## Limitations and next work

- regenerate `customer_segments_output.csv` through a standalone feature
  pipeline instead of relying on notebook state
- compare K-Means with density-based and hierarchical approaches
- validate whether the segments remain stable across time windows
- evaluate campaign recommendations against observed outcomes before treating
  them as business impact

## Final Note

The dashboard demonstrates how exploratory segments can support analysis. It
does not establish causal business impact or production readiness on its own.

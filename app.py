
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
from collections import Counter
import os

app = FastAPI(title="Starbucks Customer Segmentation Dashboard")

# Static files & templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Data loading
RAW_DATA_PATH = os.path.join(BASE_DIR, "starbucks_customer_ordering_patterns.csv")
CUSTOMER_DATA_PATH = os.path.join(BASE_DIR, "customer_segments_output.csv")

raw_data = None
raw_data_available = os.path.exists(RAW_DATA_PATH)
if raw_data_available:
    raw_data = pd.read_csv(RAW_DATA_PATH)
    raw_data["order_date"] = pd.to_datetime(raw_data["order_date"])
    raw_data["order_hour"] = raw_data["order_time"].str.split(":").str[0].astype(int)

customers = pd.read_csv(CUSTOMER_DATA_PATH)
total_orders_all = int(customers["total_orders"].sum())

# Pre-compute: Segment profiles
segment_profiles = {}
for seg_name in customers["segment_name"].unique():
    seg = customers[customers["segment_name"] == seg_name]
    profile = {
        "name": seg_name,
        "size": int(len(seg)),
        "pct": round(len(seg) / len(customers) * 100, 1),
        "avg_spend": round(seg["avg_total_spend"].mean(), 2),
        "avg_orders": round(seg["total_orders"].mean(), 1),
        "avg_revenue": round(seg["total_revenue"].mean(), 2),
        "avg_cart_size": round(seg["avg_cart_size"].mean(), 2),
        "avg_customizations": round(seg["avg_num_customizations"].mean(), 2),
        "food_order_rate": round(seg["food_order_rate"].mean() * 100, 1),
        "order_ahead_rate": round(seg["order_ahead_rate"].mean() * 100, 1),
        "avg_satisfaction": round(seg["avg_customer_satisfaction"].mean(), 2),
        "avg_fulfillment": round(seg["avg_fulfillment_time"].mean(), 2),
        "avg_recency": round(seg["recency_days"].mean(), 1),
        "rewards_rate": round(seg["is_rewards_member"].mean() * 100, 1),
        "weekend_rate": round(seg["weekend_order_rate"].mean() * 100, 1),
        "morning_rate": round(seg["morning_rate"].mean() * 100, 1),
        "afternoon_rate": round(seg["afternoon_rate"].mean() * 100, 1),
        "evening_rate": round(seg["evening_rate"].mean() * 100, 1),
        "top_drinks": seg["favorite_drink_category"].value_counts().head(5).to_dict(),
    }
    for col in customers.columns:
        if col.endswith("_rate") and any(ch in col for ch in ["mobile", "drive", "in_store", "kiosk"]):
            profile[col] = round(seg[col].mean() * 100, 1)
    segment_profiles[seg_name] = profile

drink_associations = {}
all_drinks = sorted(customers["favorite_drink_category"].dropna().unique().tolist())

if raw_data_available:
    # For each drink, find what other drinks are commonly ordered by the same customer
    customer_drinks = raw_data.groupby("customer_id")["drink_category"].apply(set).to_dict()
    all_drinks = raw_data["drink_category"].unique().tolist()
    for drink in all_drinks:
        buyers = [cid for cid, drinks in customer_drinks.items() if drink in drinks]
        co_drinks = Counter()
        for cid in buyers:
            for d in customer_drinks[cid]:
                if d != drink:
                    co_drinks[d] += 1
        total = len(buyers) if buyers else 1
        drink_associations[drink] = {
            d: round(count / total, 3)
            for d, count in co_drinks.most_common(10)
        }

# Segment drink popularity
segment_drink_popularity = {}
for seg_name in customers["segment_name"].unique():
    seg_ids = set(customers[customers["segment_name"] == seg_name]["customer_id"])
    if raw_data_available:
        seg_orders = raw_data[raw_data["customer_id"].isin(seg_ids)]
        total_seg_orders = len(seg_orders)
        drink_counts = seg_orders["drink_category"].value_counts()
        segment_drink_popularity[seg_name] = {
            drink: round(count / total_seg_orders * 100, 1)
            for drink, count in drink_counts.items()
        }
    else:
        seg = customers[customers["segment_name"] == seg_name]
        drink_counts = seg["favorite_drink_category"].value_counts()
        total_seg_customers = max(len(seg), 1)
        segment_drink_popularity[seg_name] = {
            drink: round(count / total_seg_customers * 100, 1)
            for drink, count in drink_counts.items()
        }

def compute_churn_score(row):
    """Heuristic churn score 0-100. Higher = more likely to churn."""
    score = 0.0

    # Recency component (0-40): more days since last order = higher risk
    max_recency = customers["recency_days"].quantile(0.95)
    recency_score = min(row["recency_days"] / max(max_recency, 1), 1.0) * 40
    score += recency_score

    # Frequency component (0-30): fewer orders = higher risk
    max_orders = customers["total_orders"].quantile(0.95)
    freq_score = (1 - min(row["total_orders"] / max(max_orders, 1), 1.0)) * 30
    score += freq_score

    # Satisfaction component (0-30): lower satisfaction = higher risk
    sat_score = (1 - (row["avg_customer_satisfaction"] - 1) / 4) * 30
    score += sat_score

    return round(min(max(score, 0), 100), 1)

customers["churn_score"] = customers.apply(compute_churn_score, axis=1)
customers["churn_risk"] = pd.cut(
    customers["churn_score"],
    bins=[-1, 33, 66, 101],
    labels=["Low", "Medium", "High"]
)

# Helper

def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return round(float(obj), 4)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return str(obj.date())
    return obj


def get_customer_top_channels(customer_row):
    channel_map = {
        "mobile_app_rate": "Mobile App",
        "drive_thru_rate": "Drive-Thru",
        "in_store_cashier_rate": "In-Store Cashier",
        "kiosk_rate": "Kiosk",
    }
    ranked = []
    for col, label in channel_map.items():
        if col in customer_row.index:
            ranked.append((label, round(float(customer_row[col]) * 100, 1)))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return {label: value for label, value in ranked[:3] if value > 0}


def build_fallback_trends():
    channel_specs = [
        ("Mobile App", "mobile_app_rate"),
        ("Drive-Thru", "drive_thru_rate"),
        ("In-Store Cashier", "in_store_cashier_rate"),
        ("Kiosk", "kiosk_rate"),
    ]
    channel_labels = []
    channel_values = []
    channel_spend = []
    for label, col in channel_specs:
        if col in customers.columns:
            approx_orders = float((customers[col] * customers["total_orders"]).sum())
            channel_labels.append(label)
            channel_values.append(round(approx_orders))
            active = customers[customers[col] > 0]
            channel_spend.append(round(float(active["avg_total_spend"].mean()), 2) if not active.empty else 0.0)

    drink_counts = customers["favorite_drink_category"].value_counts()
    return {
        "by_day": {"labels": [], "values": []},
        "by_hour": {"labels": [], "values": []},
        "by_channel": {
            "labels": channel_labels,
            "values": channel_values,
            "avg_spend": channel_spend,
        },
        "by_drink": {"labels": drink_counts.index.tolist(), "values": drink_counts.tolist()},
        "monthly": {"labels": [], "orders": [], "avg_spend": []},
        "raw_data_available": False,
    }

# Action recommendation engine

def get_action_recommendations(customer_row):
    recs = []

    if customer_row["avg_total_spend"] > customers["avg_total_spend"].quantile(0.75):
        recs.append({"type": "retain", "title": "Loyalty Offer",
            "desc": "This customer spends well above average. A loyalty bonus, early seasonal access, or bonus reward stars would fit well.",
            "priority": "high"})
    elif customer_row["avg_total_spend"] < customers["avg_total_spend"].quantile(0.25):
        recs.append({"type": "value", "title": "Value Offer",
            "desc": "Spend per visit is on the lower side. Value bundles or a limited-time price offer may help lift basket size.",
            "priority": "medium"})

    if customer_row["total_orders"] > customers["total_orders"].quantile(0.75):
        recs.append({"type": "upsell", "title": "Basket Growth",
            "desc": "This customer orders often. Food pairings, premium upgrades, or seasonal add-ons are reasonable next offers.",
            "priority": "medium"})
    elif customer_row["total_orders"] < customers["total_orders"].quantile(0.25):
        recs.append({"type": "reactivate", "title": "Reactivation Offer",
            "desc": "Order count is low. A simple win-back message with a short-term offer could help bring this customer back.",
            "priority": "high"})

    if customer_row["avg_customer_satisfaction"] < 3.0:
        recs.append({"type": "fix", "title": "Service Follow-Up",
            "desc": "Satisfaction is below average. It would be worth checking service quality, order accuracy, or fulfillment speed.",
            "priority": "high"})
    elif customer_row["avg_customer_satisfaction"] >= 4.5:
        recs.append({"type": "advocate", "title": "Positive Feedback Ask",
            "desc": "Satisfaction is very high. This is a good customer to target for reviews, referrals, or early product feedback.",
            "priority": "low"})

    if customer_row["order_ahead_rate"] > 0.6:
        recs.append({"type": "digital", "title": "Mobile Experience",
            "desc": "This customer relies heavily on order-ahead. App-focused offers and a smooth pickup experience matter here.",
            "priority": "medium"})

    if customer_row["avg_num_customizations"] > customers["avg_num_customizations"].quantile(0.75):
        recs.append({"type": "personalize", "title": "Customization Offer",
            "desc": "This customer customizes drinks often. Personalized add-ons or seasonal flavor options should work well.",
            "priority": "medium"})

    if not customer_row["is_rewards_member"]:
        recs.append({"type": "enroll", "title": "Rewards Sign-Up",
            "desc": "This customer is not in the rewards program yet. A sign-up incentive could move them into the loyalty funnel.",
            "priority": "medium"})

    if customer_row["food_order_rate"] < 0.2:
        recs.append({"type": "cross_sell", "title": "Food Pairing",
            "desc": "Food attachment is low. Simple breakfast or snack pairings may be worth testing.",
            "priority": "low"})

    if not recs:
        recs.append({"type": "maintain", "title": "Regular Promotion",
            "desc": "This customer looks fairly stable. Standard seasonal or loyalty campaigns should be enough for now.", "priority": "low"})

    return recs

# Routes: Pages

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Routes: Segment APIs

@app.get("/api/segments")
async def api_segments():
    return clean_for_json({
        "segments": list(segment_profiles.values()),
        "total_customers": int(len(customers)),
        "total_orders": total_orders_all,
        "overall_avg_spend": round(float(customers["avg_total_spend"].mean()), 2),
        "overall_avg_satisfaction": round(float(customers["avg_customer_satisfaction"].mean()), 2),
        "raw_data_available": raw_data_available,
    })

@app.get("/api/compare")
async def api_compare():
    metrics = [
        "avg_total_spend", "total_orders", "avg_cart_size",
        "avg_num_customizations", "avg_customer_satisfaction",
        "food_order_rate", "order_ahead_rate", "avg_fulfillment_time",
        "total_revenue", "weekend_order_rate",
    ]
    metric_labels = [
        "Avg Spend", "Avg Orders", "Avg Cart Size",
        "Avg Customizations", "Satisfaction",
        "Food Order Rate", "Order Ahead Rate", "Avg Fulfillment (min)",
        "Avg Revenue", "Weekend Rate",
    ]
    comparison = {}
    for seg_name in customers["segment_name"].unique():
        seg = customers[customers["segment_name"] == seg_name]
        comparison[seg_name] = {
            "values": [round(float(seg[m].mean()), 2) for m in metrics],
        }
    return clean_for_json({"labels": metric_labels, "metric_keys": metrics, "segments": comparison})

@app.get("/api/trends")
async def api_trends():
    if not raw_data_available:
        return clean_for_json(build_fallback_trends())

    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_counts = raw_data["day_of_week"].value_counts().reindex(day_order).fillna(0)
    hour_counts = raw_data["order_hour"].value_counts().sort_index()
    channel_counts = raw_data["order_channel"].value_counts()
    channel_spend = raw_data.groupby("order_channel")["total_spend"].mean().round(2)
    drink_counts = raw_data["drink_category"].value_counts()

    monthly_data = raw_data.copy()
    monthly_data["order_month"] = monthly_data["order_date"].dt.to_period("M").astype(str)
    monthly = monthly_data.groupby("order_month").agg(
        orders=("order_id", "count"), avg_spend=("total_spend", "mean")
    ).round(2)

    return clean_for_json({
        "by_day": {"labels": day_order, "values": day_counts.tolist()},
        "by_hour": {"labels": hour_counts.index.tolist(), "values": hour_counts.tolist()},
        "by_channel": {
            "labels": channel_counts.index.tolist(),
            "values": channel_counts.tolist(),
            "avg_spend": channel_spend.reindex(channel_counts.index).tolist(),
        },
        "by_drink": {"labels": drink_counts.index.tolist(), "values": drink_counts.tolist()},
        "monthly": {
            "labels": monthly.index.tolist(),
            "orders": monthly["orders"].tolist(),
            "avg_spend": monthly["avg_spend"].tolist(),
        },
        "raw_data_available": True,
    })

# Routes: Customer APIs

@app.get("/api/customer/{customer_id}")
async def api_customer(customer_id: str):
    customer_id = customer_id.upper()
    row = customers[customers["customer_id"] == customer_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    row_dict = clean_for_json(row.iloc[0].to_dict())

    customer_row = row.iloc[0]
    if raw_data_available:
        cust_orders = raw_data[raw_data["customer_id"] == customer_id]
        order_history = {
            "total_orders": int(len(cust_orders)),
            "first_order": str(cust_orders["order_date"].min().date()) if not cust_orders.empty else None,
            "last_order": str(cust_orders["order_date"].max().date()) if not cust_orders.empty else None,
            "top_channels": cust_orders["order_channel"].value_counts().head(3).to_dict(),
            "top_drinks": cust_orders["drink_category"].value_counts().head(3).to_dict(),
        }
    else:
        order_history = {
            "total_orders": int(customer_row["total_orders"]),
            "first_order": None,
            "last_order": None,
            "top_channels": get_customer_top_channels(customer_row),
            "top_drinks": (
                {customer_row["favorite_drink_category"]: 1}
                if pd.notna(customer_row.get("favorite_drink_category"))
                else {}
            ),
            "note": "Detailed order history is unavailable in this deployed version because the raw transaction file is not included.",
        }

    recs = get_action_recommendations(customer_row)

    return clean_for_json({
        "customer": row_dict,
        "order_history": order_history,
        "recommendations": recs,
    })

@app.get("/api/customer_search")
async def api_customer_search(q: str = Query("", min_length=0)):
    query = q.upper()
    if len(query) < 3:
        return {"results": []}
    matches = customers[customers["customer_id"].str.contains(query, na=False)].head(10)
    results = []
    for _, row in matches.iterrows():
        results.append({
            "customer_id": row["customer_id"],
            "segment": row["segment_name"],
            "total_orders": int(row["total_orders"]),
            "avg_spend": round(float(row["avg_total_spend"]), 2),
            "churn_risk": str(row["churn_risk"]),
        })
    return {"results": results}

# Routes: Customer 360 Timeline

@app.get("/api/customer/{customer_id}/timeline")
async def api_customer_timeline(customer_id: str):
    customer_id = customer_id.upper()
    row = customers[customers["customer_id"] == customer_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    if not raw_data_available:
        customer_row = row.iloc[0]
        seg = customers[customers["segment_name"] == customer_row["segment_name"]]
        compare_keys = ["avg_total_spend", "total_orders", "avg_cart_size",
                        "avg_num_customizations", "avg_customer_satisfaction", "order_ahead_rate"]
        compare_labels = ["Spend", "Orders", "Cart Size", "Customizations", "Satisfaction", "Order Ahead"]
        return clean_for_json({
            "monthly": {"labels": [], "orders": [], "avg_spend": [], "avg_satisfaction": []},
            "channel_evolution": [],
            "spend_trend": "not available",
            "peer_comparison": {
                "labels": compare_labels,
                "customer": [round(float(customer_row[k]), 2) for k in compare_keys],
                "segment_avg": [round(float(seg[k].mean()), 2) for k in compare_keys],
            },
            "order_count": int(customer_row["total_orders"]),
            "note": "Timeline charts require raw order-level data and are not available in this deployed version.",
        })

    cust_orders = raw_data[raw_data["customer_id"] == customer_id].sort_values("order_date")

    if cust_orders.empty:
        raise HTTPException(status_code=404, detail="No orders found")

    # Monthly aggregation for trends
    cust_monthly = cust_orders.copy()
    cust_monthly["month"] = cust_monthly["order_date"].dt.to_period("M").astype(str)
    monthly = cust_monthly.groupby("month").agg(
        orders=("order_id", "count"),
        avg_spend=("total_spend", "mean"),
        avg_satisfaction=("customer_satisfaction", "mean"),
    ).round(2)

    # Channel evolution
    channel_by_half = []
    mid = len(cust_orders) // 2
    if mid > 0:
        first_half = cust_orders.iloc[:mid]["order_channel"].value_counts(normalize=True).round(3).to_dict()
        second_half = cust_orders.iloc[mid:]["order_channel"].value_counts(normalize=True).round(3).to_dict()
        channel_by_half = [
            {"period": "Earlier Orders", "channels": first_half},
            {"period": "Recent Orders", "channels": second_half},
        ]

    # Spend trend direction
    if len(monthly) >= 2:
        early_spend = monthly["avg_spend"].iloc[:len(monthly)//2].mean()
        late_spend = monthly["avg_spend"].iloc[len(monthly)//2:].mean()
        spend_trend = "increasing" if late_spend > early_spend * 1.05 else (
            "decreasing" if late_spend < early_spend * 0.95 else "stable")
    else:
        spend_trend = "not enough data"

    # Peer comparison: customer vs segment average
    customer_row = row.iloc[0]
    seg = customers[customers["segment_name"] == customer_row["segment_name"]]
    compare_keys = ["avg_total_spend", "total_orders", "avg_cart_size",
                    "avg_num_customizations", "avg_customer_satisfaction", "order_ahead_rate"]
    compare_labels = ["Spend", "Orders", "Cart Size", "Customizations", "Satisfaction", "Order Ahead"]
    peer_comparison = {
        "labels": compare_labels,
        "customer": [round(float(customer_row[k]), 2) for k in compare_keys],
        "segment_avg": [round(float(seg[k].mean()), 2) for k in compare_keys],
    }

    return clean_for_json({
        "monthly": {
            "labels": monthly.index.tolist(),
            "orders": monthly["orders"].tolist(),
            "avg_spend": monthly["avg_spend"].tolist(),
            "avg_satisfaction": monthly["avg_satisfaction"].tolist(),
        },
        "channel_evolution": channel_by_half,
        "spend_trend": spend_trend,
        "peer_comparison": peer_comparison,
        "order_count": int(len(cust_orders)),
    })

# Routes: Drink Recommendation Engine

@app.get("/api/recommendations/drinks/{customer_id}")
async def api_drink_recommendations(customer_id: str):
    customer_id = customer_id.upper()
    row = customers[customers["customer_id"] == customer_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    seg_name = row.iloc[0]["segment_name"]
    if raw_data_available:
        cust_orders = raw_data[raw_data["customer_id"] == customer_id]
        ordered_drinks = set(cust_orders["drink_category"].unique())
        all_available = set(raw_data["drink_category"].unique())
    else:
        favorite_drink = row.iloc[0].get("favorite_drink_category")
        ordered_drinks = {favorite_drink} if pd.notna(favorite_drink) else set()
        all_available = set(all_drinks)

    not_tried = all_available - ordered_drinks

    recs = []

    # Method 1: Segment popularity for drinks not yet tried
    seg_pop = segment_drink_popularity.get(seg_name, {})
    for drink in not_tried:
        pop_score = seg_pop.get(drink, 0)
        recs.append({
            "drink": drink,
            "score": pop_score,
            "reason": f"Popular with {seg_name} customers ({pop_score}% of segment orders)",
            "method": "segment_popularity"
        })

    # Method 2: Association rules from drinks they DO order
    if raw_data_available:
        for ordered in ordered_drinks:
            assoc = drink_associations.get(ordered, {})
            for drink, strength in assoc.items():
                if drink in not_tried:
                    existing = next((r for r in recs if r["drink"] == drink), None)
                    assoc_score = strength * 100
                    if existing:
                        existing["score"] = max(existing["score"], assoc_score)
                        existing["assoc_reason"] = f"Customers who order {ordered} also enjoy {drink} ({strength*100:.0f}%)"
                    else:
                        recs.append({
                            "drink": drink,
                            "score": assoc_score,
                            "reason": f"Customers who order {ordered} also enjoy {drink} ({strength*100:.0f}%)",
                            "method": "association"
                        })

    # Method 3: If already tried all drinks, suggest re-trying less-ordered ones
    if not recs:
        if raw_data_available:
            drink_freq = cust_orders["drink_category"].value_counts()
            least_ordered = drink_freq.tail(3)
            for drink, count in least_ordered.items():
                recs.append({
                    "drink": drink,
                    "score": 50,
                    "reason": f"You have only ordered {drink} {count} time(s) - give it another try!",
                    "method": "rediscovery"
                })
        else:
            for drink, score in list(seg_pop.items())[:3]:
                recs.append({
                    "drink": drink,
                    "score": score,
                    "reason": f"Often preferred by customers in the {seg_name} segment.",
                    "method": "segment_preference"
                })

    # Sort by score and return top 5
    recs.sort(key=lambda x: x["score"], reverse=True)
    return clean_for_json({
        "customer_id": customer_id,
        "segment": seg_name,
        "drinks_tried": list(ordered_drinks),
        "recommendations": recs[:5],
        "raw_data_available": raw_data_available,
    })

# Routes: Churn Risk

@app.get("/api/churn_scores")
async def api_churn_scores():
    risk_dist = customers["churn_risk"].value_counts().to_dict()
    avg_by_risk = customers.groupby("churn_risk").agg(
        count=("customer_id", "count"),
        avg_spend=("avg_total_spend", "mean"),
        avg_orders=("total_orders", "mean"),
        avg_satisfaction=("avg_customer_satisfaction", "mean"),
        avg_recency=("recency_days", "mean"),
    ).round(2)

    # Top at-risk customers
    high_risk = customers.nlargest(10, "churn_score")[
        ["customer_id", "churn_score", "churn_risk", "total_orders",
         "avg_total_spend", "total_revenue", "recency_days",
         "avg_customer_satisfaction", "segment_name"]
    ]

    return clean_for_json({
        "distribution": {str(k): int(v) for k, v in risk_dist.items()},
        "by_risk_level": {
            str(idx): row.to_dict()
            for idx, row in avg_by_risk.iterrows()
        },
        "top_at_risk": high_risk.to_dict(orient="records"),
        "avg_churn_score": round(float(customers["churn_score"].mean()), 1),
    })

# Routes: Campaign Simulator

class CampaignRequest(BaseModel):
    segment: str
    campaign_type: str  # "discount", "loyalty", "reactivation", "upsell"
    intensity: Optional[float] = 1.0  # 0.5 = light, 1.0 = standard, 1.5 = aggressive

@app.post("/api/simulate")
async def api_simulate(req: CampaignRequest):
    seg = customers[customers["segment_name"] == req.segment]
    if seg.empty:
        raise HTTPException(status_code=404, detail=f"Segment '{req.segment}' not found")

    seg_size = len(seg)
    avg_spend = float(seg["avg_total_spend"].mean())
    avg_orders = float(seg["total_orders"].mean())
    avg_revenue = float(seg["total_revenue"].mean())
    avg_sat = float(seg["avg_customer_satisfaction"].mean())
    intensity = max(0.5, min(req.intensity or 1.0, 2.0))

    result = {"segment": req.segment, "campaign_type": req.campaign_type,
              "segment_size": seg_size, "intensity": intensity}

    if req.campaign_type == "discount":
        # 10-15% discount -> estimate 8-15% order increase, but lower margin
        discount_pct = 12 * intensity
        order_lift = 10 * intensity
        new_orders = avg_orders * (1 + order_lift / 100)
        new_spend = avg_spend * (1 - discount_pct / 100)
        new_revenue = new_orders * new_spend
        revenue_change = (new_revenue - avg_revenue) / max(avg_revenue, 1) * 100
        result.update({
            "discount_pct": round(discount_pct, 1),
            "projected_order_lift": round(order_lift, 1),
            "current_avg_revenue": round(avg_revenue, 2),
            "projected_avg_revenue": round(new_revenue, 2),
            "revenue_change_pct": round(revenue_change, 1),
            "estimated_response_rate": round(min(25 * intensity, 45), 1),
            "total_projected_revenue": round(new_revenue * seg_size, 0),
            "roi_estimate": f"{'Positive' if revenue_change > 0 else 'Negative'} - {abs(revenue_change):.1f}% per customer",
            "recommendation": "Worth testing for value-oriented segments." if revenue_change > 0
                else "This may hurt margin more than it helps volume. A loyalty campaign may be safer."
        })

    elif req.campaign_type == "loyalty":
        # Loyalty program: 5-12% retention improvement, 3-8% spend increase
        retention_lift = 8 * intensity
        spend_lift = 5 * intensity
        new_revenue = avg_revenue * (1 + spend_lift / 100) * (1 + retention_lift / 200)
        revenue_change = (new_revenue - avg_revenue) / max(avg_revenue, 1) * 100
        result.update({
            "retention_lift_pct": round(retention_lift, 1),
            "spend_lift_pct": round(spend_lift, 1),
            "current_avg_revenue": round(avg_revenue, 2),
            "projected_avg_revenue": round(new_revenue, 2),
            "revenue_change_pct": round(revenue_change, 1),
            "estimated_enrollment_rate": round(min(35 * intensity, 60), 1),
            "total_projected_revenue": round(new_revenue * seg_size, 0),
            "roi_estimate": f"Positive - {revenue_change:.1f}% revenue improvement with retention gains",
            "recommendation": "A good fit for stronger segments where repeat behavior can be deepened over time."
        })

    elif req.campaign_type == "reactivation":
        # Win-back: target dormant customers, 5-20% come back
        dormant = seg[seg["recency_days"] > seg["recency_days"].quantile(0.7)]
        dormant_count = len(dormant)
        winback_rate = 12 * intensity
        recovered_customers = int(dormant_count * winback_rate / 100)
        recovered_revenue = recovered_customers * avg_spend * 3  # assume 3 orders if reactivated
        result.update({
            "dormant_customers": dormant_count,
            "projected_winback_rate": round(winback_rate, 1),
            "recovered_customers": recovered_customers,
            "revenue_per_recovered": round(avg_spend * 3, 2),
            "total_recovered_revenue": round(recovered_revenue, 0),
            "cost_per_winback": round(avg_spend * 0.3, 2),  # assume ~30% of order as incentive cost
            "estimated_roi": round((recovered_revenue - dormant_count * avg_spend * 0.3) / max(dormant_count * avg_spend * 0.3, 1) * 100, 1),
            "recommendation": f"Target the {dormant_count:,} more dormant customers first and keep the offer simple."
        })

    elif req.campaign_type == "upsell":
        # Upsell: increase cart size or premiumization
        cart_lift = 6 * intensity
        premium_lift = 8 * intensity
        new_spend = avg_spend * (1 + premium_lift / 100)
        new_revenue = avg_revenue * (1 + (cart_lift + premium_lift) / 200)
        revenue_change = (new_revenue - avg_revenue) / max(avg_revenue, 1) * 100
        result.update({
            "cart_size_lift_pct": round(cart_lift, 1),
            "premium_spend_lift_pct": round(premium_lift, 1),
            "current_avg_spend": round(avg_spend, 2),
            "projected_avg_spend": round(new_spend, 2),
            "current_avg_revenue": round(avg_revenue, 2),
            "projected_avg_revenue": round(new_revenue, 2),
            "revenue_change_pct": round(revenue_change, 1),
            "estimated_conversion": round(min(20 * intensity, 40), 1),
            "total_projected_revenue": round(new_revenue * seg_size, 0),
            "recommendation": "This fits segments that already show decent engagement and can support basket-building offers."
        })
    else:
        raise HTTPException(status_code=400, detail="Invalid campaign_type. Use: discount, loyalty, reactivation, upsell")

    return clean_for_json(result)

# Routes: Segment Explorer

@app.get("/api/explorer")
async def api_explorer(
    feature_x: str = Query("avg_total_spend"),
    feature_y: str = Query("total_orders"),
    limit: int = Query(2000, le=5000),
):
    valid_features = customers.select_dtypes(include=[np.number]).columns.tolist()
    if feature_x not in valid_features or feature_y not in valid_features:
        raise HTTPException(status_code=400,
            detail=f"Invalid feature. Available: {valid_features}")

    sample = customers.sample(n=min(limit, len(customers)), random_state=42)
    points = []
    for _, row in sample.iterrows():
        points.append({
            "x": round(float(row[feature_x]), 3),
            "y": round(float(row[feature_y]), 3),
            "segment": row["segment_name"],
            "customer_id": row["customer_id"],
            "churn_risk": str(row["churn_risk"]),
        })

    return clean_for_json({
        "feature_x": feature_x,
        "feature_y": feature_y,
        "available_features": valid_features,
        "points": points,
        "total_sampled": len(points),
    })

# Routes: Executive Summary

@app.get("/api/executive_summary")
async def api_executive_summary():
    total_cust = len(customers)
    total_orders = total_orders_all
    avg_spend = round(float(customers["avg_total_spend"].mean()), 2)
    avg_sat = round(float(customers["avg_customer_satisfaction"].mean()), 2)
    total_rev = round(float(customers["total_revenue"].sum()), 0)

    # Key findings
    findings = []

    # Segment size insight
    for name, prof in segment_profiles.items():
        findings.append({
            "title": f"{name} Segment",
            "detail": f"Contains {prof['size']:,} customers ({prof['pct']}%). "
                      f"Average spend ${prof['avg_spend']}, satisfaction {prof['avg_satisfaction']}/5.",
            "type": "segment"
        })

    # Channel insight
    if raw_data_available:
        channel_dom = raw_data["order_channel"].value_counts()
        top_channel = channel_dom.index[0]
        top_channel_pct = round(channel_dom.iloc[0] / total_orders * 100, 1)
    else:
        approx_channel_totals = {
            "Mobile App": float((customers.get("mobile_app_rate", 0) * customers["total_orders"]).sum()),
            "Drive-Thru": float((customers.get("drive_thru_rate", 0) * customers["total_orders"]).sum()),
            "In-Store Cashier": float((customers.get("in_store_cashier_rate", 0) * customers["total_orders"]).sum()),
            "Kiosk": float((customers.get("kiosk_rate", 0) * customers["total_orders"]).sum()),
        }
        top_channel = max(approx_channel_totals, key=approx_channel_totals.get)
        top_channel_pct = round(approx_channel_totals[top_channel] / max(total_orders, 1) * 100, 1)
    findings.append({
        "title": f"{top_channel} is the leading channel",
        "detail": f"{top_channel} accounts for {top_channel_pct}% of all orders. "
                  "Channel preference is one of the clearest ways the customer groups differ.",
        "type": "insight"
    })

    # Churn risk insight
    high_risk_pct = round(len(customers[customers["churn_risk"] == "High"]) / total_cust * 100, 1)
    high_risk_rev = round(float(customers[customers["churn_risk"] == "High"]["total_revenue"].sum()), 0)
    findings.append({
        "title": f"{high_risk_pct}% of customers fall into high churn risk",
        "detail": f"These {len(customers[customers['churn_risk'] == 'High']):,} customers represent "
                  f"${high_risk_rev:,.0f} in revenue. A focused reactivation campaign is worth considering.",
        "type": "risk"
    })

    # Rewards insight
    rewards_pct = round(customers["is_rewards_member"].mean() * 100, 1)
    findings.append({
        "title": f"Rewards enrollment is {rewards_pct}%",
        "detail": "Rewards members show different behavioral patterns. "
                  "That leaves room to test enrollment offers among non-members.",
        "type": "opportunity"
    })

    # Top opportunities
    opportunities = []
    for name, prof in segment_profiles.items():
        if prof["order_ahead_rate"] > 40:
            opportunities.append({
                "segment": name,
                "action": "Lean into app usage with mobile offers and a reliable pickup experience",
                "impact": "high"
            })
        if prof["avg_satisfaction"] < 3.6:
            opportunities.append({
                "segment": name,
                "action": "Review satisfaction drivers such as fulfillment speed and order accuracy",
                "impact": "high"
            })
        if prof["food_order_rate"] < 30:
            opportunities.append({
                "segment": name,
                "action": "Test food pairing prompts at checkout",
                "impact": "medium"
            })
        if prof["rewards_rate"] < 50:
            opportunities.append({
                "segment": name,
                "action": "Test rewards sign-up offers for this segment",
                "impact": "medium"
            })

    return clean_for_json({
        "headline_metrics": {
            "total_customers": total_cust,
            "total_orders": total_orders,
            "total_revenue": total_rev,
            "avg_spend": avg_spend,
            "avg_satisfaction": avg_sat,
            "segments": len(segment_profiles),
            "high_risk_customers": int(len(customers[customers["churn_risk"] == "High"])),
            "raw_data_available": raw_data_available,
        },
        "findings": findings,
        "opportunities": opportunities,
        "methodology": [
            "100K+ order-level transactions aggregated to 15K customer profiles",
            "20+ behavioral features engineered across spend, recency, channel, and preferences",
            "K-Means clustering reviewed with elbow and silhouette checks",
            "Churn risk scored with a recency-frequency-satisfaction heuristic",
            "Drink recommendations based on segment popularity and co-order patterns",
        ],
    })

# Run

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)

from collections.abc import Iterable
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

CLUSTERING_FEATURES = [
    "total_orders",
    "recency_days",
    "order_frequency",
    "avg_total_spend",
    "avg_cart_size",
    "avg_num_customizations",
    "food_order_rate",
    "order_ahead_rate",
    "avg_fulfillment_time",
    "avg_customer_satisfaction",
    "weekend_order_rate",
    "drive_thru_rate",
    "in_store_cashier_rate",
    "kiosk_rate",
    "mobile_app_rate",
    "morning_rate",
    "afternoon_rate",
    "evening_rate",
]

LOG_FEATURES = {"total_orders", "recency_days", "order_frequency"}


@dataclass(frozen=True)
class CandidateResult:
    k: int
    inertia: float
    silhouette: float
    calinski_harabasz: float
    davies_bouldin: float
    min_cluster_share: float

    def to_dict(self) -> dict:
        return asdict(self)


def _log_selected_features(values: np.ndarray) -> np.ndarray:
    transformed = values.copy()
    for index, feature in enumerate(CLUSTERING_FEATURES):
        if feature in LOG_FEATURES:
            transformed[:, index] = np.log1p(np.clip(transformed[:, index], 0, None))
    return transformed


def prepare_feature_matrix(customers: pd.DataFrame) -> np.ndarray:
    missing = sorted(set(CLUSTERING_FEATURES).difference(customers.columns))
    if missing:
        raise ValueError(f"missing clustering features: {', '.join(missing)}")

    pipeline = make_pipeline(
        SimpleImputer(strategy="median"),
        FunctionTransformer(_log_selected_features, validate=False),
        StandardScaler(),
    )
    return pipeline.fit_transform(customers[CLUSTERING_FEATURES])


def evaluate_kmeans_candidates(
    customers: pd.DataFrame,
    k_values: Iterable[int] = range(2, 7),
    sample_size: int = 5_000,
    random_state: int = 42,
) -> list[CandidateResult]:
    matrix = prepare_feature_matrix(customers)
    results: list[CandidateResult] = []

    for k in k_values:
        if k < 2 or k >= len(matrix):
            raise ValueError("each k must be at least 2 and smaller than the dataset")

        model = KMeans(
            n_clusters=k,
            n_init=20,
            max_iter=500,
            random_state=random_state,
        )
        labels = model.fit_predict(matrix)
        counts = np.bincount(labels, minlength=k)
        results.append(
            CandidateResult(
                k=k,
                inertia=round(float(model.inertia_), 4),
                silhouette=round(
                    float(
                        silhouette_score(
                            matrix,
                            labels,
                            sample_size=min(sample_size, len(matrix)),
                            random_state=random_state,
                        )
                    ),
                    4,
                ),
                calinski_harabasz=round(
                    float(calinski_harabasz_score(matrix, labels)), 4
                ),
                davies_bouldin=round(float(davies_bouldin_score(matrix, labels)), 4),
                min_cluster_share=round(float(counts.min() / len(labels)), 4),
            )
        )

    return results

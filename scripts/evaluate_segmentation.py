import argparse
import json
from pathlib import Path

import pandas as pd

from analysis.model_evaluation import evaluate_kmeans_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate K-Means cluster candidates.")
    parser.add_argument(
        "--input",
        default="customer_segments_output.csv",
        help="Path to the customer-level feature CSV.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/clustering_metrics.json",
        help="JSON output path.",
    )
    args = parser.parse_args()

    results = evaluate_kmeans_candidates(pd.read_csv(args.input))
    best = max(results, key=lambda result: result.silhouette)
    payload = {
        "selection_rule": "highest silhouette among k=2..6",
        "interpretation": (
            "Exploratory segmentation only. A silhouette below 0.25 indicates "
            "substantial overlap and should not be treated as ground-truth personas."
        ),
        "best_k": best.k,
        "best_silhouette": best.silhouette,
        "candidates": [result.to_dict() for result in results],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

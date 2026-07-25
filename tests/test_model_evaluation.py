import unittest

import numpy as np
import pandas as pd

from analysis.model_evaluation import (
    CLUSTERING_FEATURES,
    evaluate_kmeans_candidates,
    prepare_feature_matrix,
)


class ModelEvaluationTests(unittest.TestCase):
    def test_feature_matrix_is_finite_and_standardized(self):
        frame = pd.DataFrame(
            {
                feature: np.linspace(index + 1, index + 5, 12)
                for index, feature in enumerate(CLUSTERING_FEATURES)
            }
        )
        frame.loc[0, "avg_total_spend"] = np.nan

        matrix = prepare_feature_matrix(frame)

        self.assertEqual(matrix.shape, (12, len(CLUSTERING_FEATURES)))
        self.assertTrue(np.isfinite(matrix).all())
        self.assertTrue(np.allclose(matrix.mean(axis=0), 0, atol=1e-7))

    def test_candidate_evaluation_reports_multiple_quality_metrics(self):
        rng = np.random.default_rng(42)
        cluster_a = rng.normal(loc=-2, scale=0.2, size=(30, len(CLUSTERING_FEATURES)))
        cluster_b = rng.normal(loc=2, scale=0.2, size=(30, len(CLUSTERING_FEATURES)))
        frame = pd.DataFrame(
            np.vstack([cluster_a, cluster_b]),
            columns=CLUSTERING_FEATURES,
        )

        results = evaluate_kmeans_candidates(frame, k_values=(2, 3), sample_size=60)

        self.assertEqual([result.k for result in results], [2, 3])
        self.assertGreater(results[0].silhouette, results[1].silhouette)
        self.assertGreater(results[0].calinski_harabasz, 0)
        self.assertGreater(results[0].davies_bouldin, 0)
        self.assertGreaterEqual(results[0].min_cluster_share, 0)

    def test_rejects_missing_features(self):
        with self.assertRaisesRegex(ValueError, "missing clustering features"):
            prepare_feature_matrix(pd.DataFrame({"total_orders": [1, 2]}))

    def test_rejects_invalid_cluster_counts(self):
        frame = pd.DataFrame(
            {
                feature: np.linspace(index + 1, index + 3, 3)
                for index, feature in enumerate(CLUSTERING_FEATURES)
            }
        )

        with self.assertRaisesRegex(ValueError, "each k must be at least 2"):
            evaluate_kmeans_candidates(frame, k_values=(1,))
        with self.assertRaisesRegex(ValueError, "each k must be at least 2"):
            evaluate_kmeans_candidates(frame, k_values=(3,))


if __name__ == "__main__":
    unittest.main()

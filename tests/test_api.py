import unittest

from fastapi.testclient import TestClient

from app import app


class DashboardApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint_reports_loaded_data(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["orders"], 100_000)
        self.assertEqual(payload["customers"], 14_988)

    def test_segments_endpoint_returns_two_named_segments(self):
        response = self.client.get("/api/segments")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_orders"], 100_000)
        self.assertEqual(len(payload["segments"]), 2)
        self.assertTrue(all(segment["name"] for segment in payload["segments"]))

    def test_invalid_explorer_feature_returns_400(self):
        response = self.client.get(
            "/api/explorer",
            params={"feature_x": "not_a_feature", "feature_y": "total_orders"},
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()

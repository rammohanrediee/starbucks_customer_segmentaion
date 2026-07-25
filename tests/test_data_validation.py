import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from analysis.data_validation import sha256_file, validate_order_data


def valid_orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": ["CUST_1", "CUST_2"],
            "order_id": ["ORD_1", "ORD_2"],
            "order_date": ["2025-01-01", "2025-01-02"],
            "order_channel": ["Mobile App", "Drive-Thru"],
            "total_spend": [10.5, 8.25],
            "customer_satisfaction": [5, 3],
        }
    )


class DataValidationTests(unittest.TestCase):
    def test_accepts_a_valid_order_dataset(self):
        report = validate_order_data(valid_orders())

        self.assertTrue(report.is_valid)
        self.assertEqual(report.row_count, 2)
        self.assertEqual(report.unique_customers, 2)
        self.assertEqual(report.duplicate_order_ids, 0)

    def test_reports_missing_columns(self):
        data = valid_orders().drop(columns=["order_channel"])

        report = validate_order_data(data)

        self.assertFalse(report.is_valid)
        self.assertIn("missing required columns: order_channel", report.errors)

    def test_reports_duplicate_orders_and_invalid_ranges(self):
        data = valid_orders()
        data.loc[1, "order_id"] = "ORD_1"
        data.loc[1, "total_spend"] = -1
        data.loc[1, "customer_satisfaction"] = 6

        report = validate_order_data(data)

        self.assertFalse(report.is_valid)
        self.assertEqual(report.duplicate_order_ids, 1)
        self.assertIn("total_spend contains negative values", report.errors)
        self.assertIn("customer_satisfaction must be between 1 and 5", report.errors)

    def test_reports_empty_data_missing_customers_and_invalid_dates(self):
        empty_report = validate_order_data(pd.DataFrame())
        self.assertFalse(empty_report.is_valid)
        self.assertIn("dataset contains no rows", empty_report.errors)

        data = valid_orders()
        data.loc[0, "customer_id"] = None
        data.loc[1, "order_date"] = "not-a-date"

        report = validate_order_data(data)

        self.assertFalse(report.is_valid)
        self.assertIn("customer_id contains missing values", report.errors)
        self.assertIn("order_date contains invalid values", report.errors)

    def test_sha256_file_is_stable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_bytes(b"customer_id,order_id\nCUST_1,ORD_1\n")

            self.assertEqual(
                sha256_file(path),
                "710eb48ef03c2f7447850cf5be81f3773bcd3be96db1e7ab54c7ee2bfda51cc1",
            )


if __name__ == "__main__":
    unittest.main()

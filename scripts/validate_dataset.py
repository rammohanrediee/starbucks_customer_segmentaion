import argparse
import json
from pathlib import Path

import pandas as pd

from analysis.data_validation import sha256_file, validate_order_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the order dataset contract.")
    parser.add_argument(
        "--input",
        default="starbucks_customer_ordering_patterns.csv",
        help="Path to the raw order CSV.",
    )
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    input_path = Path(args.input)
    report = validate_order_data(pd.read_csv(input_path))
    payload = report.to_dict() | {
        "path": str(input_path),
        "sha256": sha256_file(input_path),
    }
    rendered = json.dumps(payload, indent=2)
    print(rendered)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

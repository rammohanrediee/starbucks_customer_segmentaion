from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

import pandas as pd

REQUIRED_ORDER_COLUMNS = {
    "customer_id",
    "order_id",
    "order_date",
    "order_channel",
    "total_spend",
    "customer_satisfaction",
}


@dataclass(frozen=True)
class ValidationReport:
    is_valid: bool
    row_count: int
    unique_customers: int
    duplicate_order_ids: int
    errors: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_order_data(data: pd.DataFrame) -> ValidationReport:
    errors: list[str] = []
    missing = sorted(REQUIRED_ORDER_COLUMNS.difference(data.columns))
    if missing:
        errors.append(f"missing required columns: {', '.join(missing)}")

    if data.empty:
        errors.append("dataset contains no rows")

    duplicate_order_ids = (
        int(data["order_id"].duplicated().sum()) if "order_id" in data else 0
    )
    if duplicate_order_ids:
        errors.append("order_id contains duplicate values")

    if "customer_id" in data and data["customer_id"].isna().any():
        errors.append("customer_id contains missing values")

    if "order_date" in data:
        invalid_dates = pd.to_datetime(data["order_date"], errors="coerce").isna().sum()
        if invalid_dates:
            errors.append("order_date contains invalid values")

    if "total_spend" in data and (data["total_spend"] < 0).any():
        errors.append("total_spend contains negative values")

    if "customer_satisfaction" in data:
        satisfaction = data["customer_satisfaction"]
        if (~satisfaction.between(1, 5)).any():
            errors.append("customer_satisfaction must be between 1 and 5")

    return ValidationReport(
        is_valid=not errors,
        row_count=len(data),
        unique_customers=(
            int(data["customer_id"].nunique()) if "customer_id" in data else 0
        ),
        duplicate_order_ids=duplicate_order_ids,
        errors=tuple(errors),
    )

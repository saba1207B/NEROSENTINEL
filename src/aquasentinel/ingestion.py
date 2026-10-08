"""Bounded CSV ingestion for user supplied monthly records.

Records are quarantined as unverified. They cannot silently replace the demo
fixture or become training data without a separate provenance review.
"""

import csv
import hashlib
import io
from datetime import date

from aquasentinel.units import finite

MAX_CSV_BYTES = 2_000_000
ALLOWED_VARIABLES = {"rainfall_mm", "oni_c"}


def ingest_monthly_csv(raw: bytes, *, source_id: str, region_id: str, declared_synthetic: bool = False) -> dict[str, object]:
    if not 0 < len(raw) <= MAX_CSV_BYTES:
        raise ValueError("CSV must be nonempty and at most 2 MB")
    if not source_id or len(source_id) > 80 or not region_id:
        raise ValueError("source and region identifiers are required")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    if reader.fieldnames != ["month", "variable", "value", "unit"]:
        raise ValueError("CSV columns must be month,variable,value,unit in that order")
    records = []
    keys = set()
    outlier_rows = []
    for index, row in enumerate(reader, start=2):
        if index > 10_001:
            raise ValueError("CSV has more than 10000 records")
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"row {index} has malformed columns")
        try:
            month = date.fromisoformat(row["month"])
        except ValueError as exc:
            raise ValueError(f"row {index} has invalid ISO month") from exc
        if month.day != 1:
            raise ValueError(f"row {index} month must be its first day")
        variable = row["variable"]
        if variable not in ALLOWED_VARIABLES:
            raise ValueError(f"row {index} has unsupported variable")
        unit = row["unit"]
        expected = "mm/month" if variable == "rainfall_mm" else "degrees_C_anomaly"
        if unit != expected:
            raise ValueError(f"row {index} unit must be {expected}")
        try:
            value = finite(float(row["value"]), f"row {index} value")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"row {index} has invalid finite numeric value") from exc
        if variable == "rainfall_mm" and value < 0:
            raise ValueError(f"row {index} rainfall cannot be negative")
        if (variable == "rainfall_mm" and value > 1500) or (variable == "oni_c" and abs(value) > 5):
            outlier_rows.append(index)
        key = (month, variable)
        if key in keys:
            raise ValueError(f"row {index} duplicates {month} {variable}")
        keys.add(key)
        records.append({"month": month.isoformat(), "variable": variable, "value": value, "unit": unit})
    if not records:
        raise ValueError("CSV has no records")
    records.sort(key=lambda item: (item["variable"], item["month"]))
    gaps = []
    for variable in sorted(ALLOWED_VARIABLES):
        months = [date.fromisoformat(item["month"]) for item in records if item["variable"] == variable]
        for left, right in zip(months, months[1:], strict=False):
            year, month = left.year, left.month + 1
            if month == 13:
                year, month = year + 1, 1
            if right != date(year, month, 1):
                gaps.append({"variable": variable, "after": left.isoformat(), "before": right.isoformat()})
    return {
        "source_id": source_id,
        "region_id": region_id,
        "checksum_sha256": hashlib.sha256(raw).hexdigest(),
        "record_count": len(records),
        "records": records,
        "quality": {"duplicate_count": 0, "gaps": gaps, "outlier_rows": outlier_rows, "outlier_method": "conservative range screen; requires manual review", "interpolated": False},
        "verification_status": "synthetic_user_supplied" if declared_synthetic else "user_supplied_unverified",
        "eligible_for_active_forecast": False,
    }

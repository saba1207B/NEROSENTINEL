"""Leakage-safe monthly baseline evaluation on supplied time series."""

from datetime import date
from math import sqrt

from aquasentinel.units import finite


def rolling_monthly_baselines(observations: list[tuple[date, float]], min_train: int = 24) -> dict[str, object]:
    if len(observations) < min_train + 6 or min_train < 24:
        raise ValueError("at least 24 training months and six holdout months are required")
    dates = [item[0] for item in observations]
    values = [finite(item[1], "monthly_rainfall_mm", minimum=0) for item in observations]
    if dates != sorted(set(dates)) or any(item.day != 1 for item in dates):
        raise ValueError("dates must be unique, sorted month starts")
    for left, right in zip(dates, dates[1:], strict=False):
        expected = date(left.year + (left.month == 12), left.month % 12 + 1, 1)
        if right != expected:
            raise ValueError("missing monthly observations; no interpolation is performed")
    records = []
    for origin in range(min_train, len(observations)):
        target_date = dates[origin]
        history = observations[:origin]
        same_month = [value for month, value in history if month.month == target_date.month]
        if not same_month:
            raise ValueError("seasonal climatology requires earlier observations for target month")
        records.append({
            "issue_month": dates[origin - 1].isoformat(),
            "valid_month": target_date.isoformat(),
            "actual_mm": values[origin],
            "seasonal_climatology_mm": sum(same_month) / len(same_month),
            "persistence_mm": values[origin - 1],
            "training_count": origin,
        })
    def metrics(key: str) -> dict[str, float]:
        errors = [item[key] - item["actual_mm"] for item in records]
        return {
            "mae_mm": sum(abs(error) for error in errors) / len(errors),
            "rmse_mm": sqrt(sum(error * error for error in errors) / len(errors)),
            "bias_mm": sum(errors) / len(errors),
        }
    return {
        "target": "one-month-ahead rainfall total",
        "validation": "expanding rolling origin; each prediction uses only prior months",
        "first_holdout_month": dates[min_train].isoformat(),
        "last_holdout_month": dates[-1].isoformat(),
        "holdout_count": len(records),
        "models": {"seasonal_climatology": metrics("seasonal_climatology_mm"), "persistence": metrics("persistence_mm")},
        "predictions": records,
        "activation_status": "research_evaluation_only",
    }

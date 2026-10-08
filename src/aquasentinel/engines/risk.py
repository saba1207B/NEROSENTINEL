from aquasentinel.schemas import Severity
from aquasentinel.units import finite


def drought_risk(rainfall_anomaly_pct: float, soil_moisture_anomaly_pct: float, storage_fraction: float, groundwater_index: float) -> dict[str, object]:
    for name, value in locals().items():
        finite(value, name)
    if not 0 <= storage_fraction <= 1 or not 0 <= groundwater_index <= 1:
        raise ValueError("storage and groundwater fractions must be between zero and one")
    if rainfall_anomaly_pct < -100 or soil_moisture_anomaly_pct < -100:
        raise ValueError("negative anomalies cannot be below -100 percent")
    factors = {
        "rainfall_deficit": max(0.0, -rainfall_anomaly_pct / 100),
        "soil_moisture_deficit": max(0.0, -soil_moisture_anomaly_pct / 100),
        "storage_deficit": max(0.0, 1 - storage_fraction),
        "groundwater_stress": max(0.0, 1 - groundwater_index),
    }
    weights = {"rainfall_deficit": 0.35, "soil_moisture_deficit": 0.25, "storage_deficit": 0.25, "groundwater_stress": 0.15}
    score = min(1.0, sum(factors[key] * weights[key] for key in factors))
    severity = Severity.LOW if score < 0.25 else Severity.MODERATE if score < 0.5 else Severity.HIGH if score < 0.75 else Severity.CRITICAL
    return {
        "hazard_type": "multi-indicator drought screening",
        "score": round(score, 4),
        "severity": severity,
        "factors": {key: round(value, 4) for key, value in factors.items()},
        "weights": weights,
        "uncertainty": "screening index; not a calibrated event probability",
    }

from collections.abc import Sequence

import numpy as np

from aquasentinel.units import finite


def classify_enso(oni_values: Sequence[float]) -> dict[str, object]:
    """Operational-style screening classification using five overlapping seasons.

    This is not an official NOAA declaration. A warm/cold phase requires the
    latest five supplied three-month ONI values to meet +/-0.5 C.
    """
    if len(oni_values) < 5:
        return {"phase": "insufficient_data", "confidence": 0.0, "basis": "fewer than five seasons"}
    recent = np.asarray([finite(value, "oni_anomaly_c") for value in oni_values[-5:]], dtype=float)
    if np.all(recent >= 0.5):
        phase = "el_nino"
    elif np.all(recent <= -0.5):
        phase = "la_nina"
    else:
        phase = "neutral_or_transition"
    return {
        "phase": phase,
        "confidence": None,
        "basis": "five-season ONI threshold screening; not an official declaration",
    }


def lagged_teleconnection(enso: Sequence[float], rainfall: Sequence[float], max_lag: int = 6) -> list[dict[str, float | int]]:
    if len(enso) != len(rainfall) or len(enso) < max_lag + 4:
        raise ValueError("aligned series must have equal length and enough observations")
    a = np.asarray([finite(value, "enso_anomaly") for value in enso], dtype=float)
    b = np.asarray([finite(value, "rainfall") for value in rainfall], dtype=float)
    output = []
    for lag in range(max_lag + 1):
        x, y = (a, b) if lag == 0 else (a[:-lag], b[lag:])
        corr = None if np.ptp(x) <= 1e-12 or np.ptp(y) <= 1e-12 else float(np.corrcoef(x, y)[0, 1])
        output.append({"lag_months": lag, "correlation": None if corr is None else round(corr, 4), "sample_size": len(x)})
    return output

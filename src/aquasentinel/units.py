"""Canonical physical units: m3, m2, mm, m3/s and UTC."""

from math import isfinite

M3_PER_MCM = 1_000_000.0
M2_PER_KM2 = 1_000_000.0
SECONDS_PER_DAY = 86_400.0


def finite(value: float, name: str, *, minimum: float | None = None) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and number < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return number


def mcm_to_m3(value: float) -> float:
    return finite(value, "volume_mcm") * M3_PER_MCM


def m3_to_mcm(value: float) -> float:
    return finite(value, "volume_m3") / M3_PER_MCM


def rainfall_volume_m3(rainfall_mm: float, area_m2: float) -> float:
    """Incident precipitation volume, before runoff or other losses."""
    return finite(rainfall_mm, "rainfall_mm", minimum=0) / 1000 * finite(
        area_m2, "area_m2", minimum=0
    )


def flow_to_volume_m3(flow_m3_s: float, seconds: float) -> float:
    return finite(flow_m3_s, "flow_m3_s", minimum=0) * finite(
        seconds, "seconds", minimum=0
    )

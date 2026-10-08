from dataclasses import dataclass
from math import exp

from aquasentinel.units import finite, m3_to_mcm, mcm_to_m3


@dataclass(frozen=True)
class ReservoirStep:
    storage_mcm: float
    spill_mcm: float
    release_mcm: float
    mass_balance_error_mcm: float
    evaporation_mcm: float
    other_losses_mcm: float
    evaporation_shortfall_mcm: float
    other_losses_shortfall_mcm: float
    requested_release_shortfall_mcm: float


def reservoir_step(
    storage_mcm: float,
    capacity_mcm: float,
    inflow_mcm: float,
    requested_release_mcm: float,
    evaporation_mcm: float,
    other_losses_mcm: float = 0,
    dead_storage_mcm: float = 0,
) -> ReservoirStep:
    """Conserve mass in cubic metres, then expose MCM for API compatibility."""
    for name, value in locals().items():
        finite(value, name, minimum=0)
    if capacity_mcm <= 0 or dead_storage_mcm > capacity_mcm:
        raise ValueError("capacity and minimum storage bounds are invalid")
    if storage_mcm > capacity_mcm:
        raise ValueError("initial storage exceeds capacity")
    initial = mcm_to_m3(storage_mcm)
    inflow = mcm_to_m3(inflow_mcm)
    available = initial + inflow
    requested_evaporation = mcm_to_m3(evaporation_mcm)
    evaporation = min(requested_evaporation, available)
    available -= evaporation
    requested_other = mcm_to_m3(other_losses_mcm)
    other = min(requested_other, available)
    available -= other
    requested_release = mcm_to_m3(requested_release_mcm)
    release = min(requested_release, max(0.0, available - mcm_to_m3(dead_storage_mcm)))
    available -= release
    spill = max(0.0, available - mcm_to_m3(capacity_mcm))
    final = available - spill
    residual = initial + inflow - evaporation - other - release - spill - final
    if abs(residual) > 1e-6 * max(1.0, initial + inflow):
        raise ArithmeticError("reservoir mass balance violated")
    return ReservoirStep(
        storage_mcm=m3_to_mcm(final),
        spill_mcm=m3_to_mcm(spill),
        release_mcm=m3_to_mcm(release),
        mass_balance_error_mcm=m3_to_mcm(residual),
        evaporation_mcm=m3_to_mcm(evaporation),
        other_losses_mcm=m3_to_mcm(other),
        evaporation_shortfall_mcm=m3_to_mcm(requested_evaporation - evaporation),
        other_losses_shortfall_mcm=m3_to_mcm(requested_other - other),
        requested_release_shortfall_mcm=m3_to_mcm(requested_release - release),
    )


def fao56_reference_et0(temp_min_c: float, temp_max_c: float, temp_mean_c: float, solar_radiation_mj_m2_day: float) -> float:
    """Legacy empirical screening proxy, retained for API compatibility.

    The solar radiation argument is not extraterrestrial radiation, so this
    function must never be described as FAO-56 or Hargreaves-Samani ET0.
    """
    for name, value in locals().items():
        finite(value, name)
    if temp_max_c < temp_min_c or not temp_min_c <= temp_mean_c <= temp_max_c:
        raise ValueError("temperature range is inconsistent")
    if solar_radiation_mj_m2_day < 0:
        raise ValueError("solar radiation cannot be negative")
    extraterrestrial_equivalent_mm = solar_radiation_mj_m2_day * 0.408
    return max(0.0, 0.0023 * (temp_mean_c + 17.8) * (temp_max_c - temp_min_c) ** 0.5 * extraterrestrial_equivalent_mm)


def penman_monteith_daily_et0(
    temp_min_c: float,
    temp_max_c: float,
    temp_mean_c: float,
    net_radiation_mj_m2_day: float,
    soil_heat_flux_mj_m2_day: float,
    wind_speed_2m_m_s: float,
    actual_vapour_pressure_kpa: float,
    atmospheric_pressure_kpa: float,
) -> float:
    """FAO-56 daily grass-reference Penman-Monteith ET0 in mm/day."""
    for name, value in locals().items():
        finite(value, name)
    if not temp_min_c <= temp_mean_c <= temp_max_c:
        raise ValueError("temperature range is inconsistent")
    if temp_min_c < -80 or temp_max_c > 60:
        raise ValueError("temperature outside supported meteorological range")
    if net_radiation_mj_m2_day < soil_heat_flux_mj_m2_day or wind_speed_2m_m_s < 0:
        raise ValueError("radiation, heat flux or wind is invalid")
    if atmospheric_pressure_kpa <= 0 or actual_vapour_pressure_kpa < 0:
        raise ValueError("pressure must be physically valid")

    def saturation(temp_c: float) -> float:
        return 0.6108 * exp(17.27 * temp_c / (temp_c + 237.3))

    saturation_kpa = (saturation(temp_min_c) + saturation(temp_max_c)) / 2
    if actual_vapour_pressure_kpa > saturation_kpa:
        raise ValueError("actual vapour pressure exceeds saturation pressure")
    slope = 4098 * saturation(temp_mean_c) / (temp_mean_c + 237.3) ** 2
    psychrometric = 0.000665 * atmospheric_pressure_kpa
    numerator = 0.408 * slope * (net_radiation_mj_m2_day - soil_heat_flux_mj_m2_day)
    numerator += psychrometric * 900 / (temp_mean_c + 273) * wind_speed_2m_m_s * (
        saturation_kpa - actual_vapour_pressure_kpa
    )
    denominator = slope + psychrometric * (1 + 0.34 * wind_speed_2m_m_s)
    return numerator / denominator

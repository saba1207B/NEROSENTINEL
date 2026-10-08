# Scientific validation

Status: IMPLEMENTED for physical invariants; PARTIAL for empirical model validation.

The single-reservoir step now accounts for actual evaporation, other losses, release, spill and final storage in canonical cubic metres. Loss requests above available water are curtailed and their shortfalls are reported. The district simulator reports each month's inflow, gross release, delivered supply, conveyance loss, evaporation, spill and mass residual. It raises if the internal residual exceeds `1e-6 * max(1, total input)` in cubic metres.

`pytest --cov=aquasentinel.engines --cov-branch` passed 44 tests at the V2 scientific checkpoint. Scientific engine coverage was 97% combined, including more than 90% of measured branches. Hypothesis generated 100 valid reservoir cases and checked storage bounds and mass conservation. Tests also cover zero demand, extreme rainfall, spill, dead storage, excessive evaporation, nonfinite inputs and leap-year month labels.

The full FAO-56 Penman-Monteith endpoint was compared with [FAO-56 Chapter 4, Example 17](https://www.fao.org/4/x0490e/x0490e08.htm): 5.72 mm/day within the source's rounding tolerance. The older temperature/solar proxy remains for API compatibility and is labeled an empirical screen; its numerical output is not a FAO-56 reference calculation.

No observed Coimbatore storage, groundwater or demand series has been supplied. The lumped model has not been calibrated or validated against field measurements. Reported scenario intervals represent declared Monte Carlo input distributions, not calibrated forecast confidence.


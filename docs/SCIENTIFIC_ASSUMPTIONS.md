# Scientific assumptions

The pilot is an engineering demonstration, not an operational forecast.

- Rainfall-runoff uses a lumped monthly coefficient of 0.16 over a synthetic 420 km2 catchment.
- Reservoir accounting follows `S(t+1) = S(t) + inflow - release - evaporation - other losses - spill`, bounded by dead storage and capacity.
- Distribution losses begin at 18%; leakage intervention reduces that fraction rather than creating water.
- Groundwater is a bounded screening index updated from rainfall recharge and pumping pressure. Missing aquifer parameters prohibit volume claims.
- The drought score is a transparent weighted screening index: rainfall 35%, soil moisture 25%, storage 25%, groundwater 15%. It is not a calibrated probability.
- The legacy irrigation endpoint uses an empirical temperature/radiation screening proxy. The new `/agriculture/et0/fao56` endpoint implements daily FAO-56 Penman-Monteith when complete meteorological inputs are supplied.
- The allocation optimizer maximizes explicit sector benefit weights under physical availability and essential minimums. Weights are policy assumptions.
- Monte Carlo inputs are normal perturbations clipped at physically meaningful bounds. Percentiles describe those chosen assumptions.

No model accuracy is reported because no predictive model has been fitted to an authorized observed dataset in this deliverable.

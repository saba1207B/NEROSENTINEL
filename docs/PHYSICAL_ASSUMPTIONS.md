# Physical assumptions

Status: IMPLEMENTED for explicit units and deterministic pilot equations; PARTIAL for representation of real hydrology.

- Internal reservoir arithmetic uses cubic metres; existing API fields ending in `_mcm` remain million cubic metres. `1 MCM = 1,000,000 m3`.
- Incident rain volume is `rainfall_mm / 1000 * catchment_area_m2`. A synthetic runoff coefficient of 0.16 converts that incident volume into modeled reservoir inflow. Incident rain is never directly counted as usable supply.
- The synthetic catchment is 420 km2 within a distinct 4,723 km2 district placeholder. The rectangular GeoJSON is not an official boundary.
- Reservoir capacity is 105 MCM, initial storage 78 MCM and minimum operating storage 8 MCM in the pilot. Evaporation is a synthetic 1.2 MCM/month assumption, not a measured surface-area calculation.
- Gross release is split into delivered water and conveyance loss. Conservation changes demand; leakage reduction changes the loss fraction; emergency supply adds an external input. No component is credited twice.
- Groundwater is a dimensionless screening index. It is not an aquifer storage volume or a validated water-table forecast.
- Monthly input profiles represent month totals, so they are not multiplied by a fixed 30 days. Simulation outputs carry first-of-month valid labels and handle year rollover, including leap years.
- The optimizer's allocation weights are stated policy assumptions. Intervention costs come solely from caller input and are not a calibrated regional cost model.


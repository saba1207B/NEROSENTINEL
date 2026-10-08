# Data provenance and source status

Status: IMPLEMENTED for the synthetic fixture manifest and quarantined local CSV import; PARTIAL for durable lineage; BLOCKED for official live feeds.

The included Coimbatore pilot contains a 12-month synthetic seasonal profile, a synthetic reservoir and synthetic demand assumptions. It contains no 2014–2025 observation series. The prior source label implying that period was corrected. Synthetic records are separate from user supplied CSV imports.

The `POST /ingestion/monthly-csv` endpoint accepts at most 2 MB of UTF-8 `month,variable,value,unit` records. It enforces first-of-month ISO dates, explicit units, finite values, nonnegative rainfall, duplicate rejection, gap reporting, conservative outlier screening and a SHA-256 content checksum. Uploads are marked `user_supplied_unverified` and are not eligible for active forecasts. Ingestion is currently memory backed; revision history and durable object storage are planned.

## Provider review

- [NOAA PSL monthly indices](https://psl.noaa.gov/data/timeseries/month/) provide documented monthly ENSO series. [NOAA CPC's ONI page](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/index.php) describes the historical five overlapping-season threshold and warns about revisions. [CPC's RONI announcement](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/announcement.php) states that RONI became its official monitoring index in 2026. The demo's ONI-like sequence is not either official series.
- [NASA POWER daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) confirms daily point/regional formats, source spatial resolution and explicit UTC/LST time standards. No adapter is yet active.
- [CHIRPS v3 documentation](https://chc.ucsb.edu/data/chirps3) distinguishes preliminary and final products and identifies the 0.05° land grid. No raster adapter is yet active. [The CHIRPS v2 page](https://chc.ucsb.edu/data/chirps) points users to v3 and documents its public-domain terms; v3 use terms must be checked for the exact files selected before ingestion.
- IMD, CWC, CGWB and India-WRIS access, terms, temporal granularity and usable pilot coverage remain unverified. Authorized official exports can use the local CSV contract after manual review; no public real-time API is assumed.

No provider document has been treated as proof that a current district-specific dataset was downloaded or validated.


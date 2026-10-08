# Model evaluation

Status: IMPLEMENTED for leakage-safe evaluation code; BLOCKED for observed-data skill claims.

`rolling_monthly_baselines` evaluates one-month-ahead seasonal climatology and persistence with an expanding rolling origin. It requires at least 24 prior monthly observations and six holdout months, rejects gaps and unsorted dates, and uses only observations earlier than each target month. It reports MAE, RMSE, bias, holdout dates and individual predictions. No model is activated automatically.

The automated test uses a deliberately repeated 36-month synthetic pattern. Seasonal climatology has zero error on that constructed pattern. That figure is a test oracle, **not** a pilot accuracy result. There are no observed holdout metrics, calibration plots, probabilistic scores, or trained XGBoost/PyTorch artifacts in this release.

The `/forecasts` demonstration remains synthetic. Its old `rainfall_anomaly_pct` and interval fields are retained for frontend compatibility, but `meta.source_type` is now `synthetic`; they must not be presented as an operational forecast.


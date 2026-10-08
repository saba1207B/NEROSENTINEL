# Local performance measurements

Status: IMPLEMENTED measurement script; PARTIAL environment coverage.

`scripts/benchmark.py` ran on the bundled Windows Python 3.12 CPU runtime on 2026-10-08. These figures are one local process, not deployment service-level objectives.

| Operation | Runs | p50 ms | p95 ms | p99 ms |
| --- | ---: | ---: | ---: | ---: |
| TestClient health request | 50 | 0.890 | 1.200 | 1.335 |
| TestClient dashboard request | 50 | 1.078 | 1.372 | 1.425 |
| 12-month digital twin | 50 | 0.239 | 0.297 | 0.392 |
| Monte Carlo, 100 iterations | 5 | 26.496 | 28.968 | 29.439 |
| SciPy allocation LP | 20 | 1.049 | 1.436 | 2.145 |

This benchmark excludes network latency, database storage, process contention and container startup. The Monte Carlo p99 is based on only five runs and is illustrative. No queue or ingestion-lag benchmark exists because those services are not implemented.

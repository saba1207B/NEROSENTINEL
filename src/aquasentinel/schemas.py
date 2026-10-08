from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class ScientificInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class SourceType(StrEnum):
    OBSERVED = "observed"
    FORECAST = "forecast"
    MODELED = "modeled"
    SYNTHETIC = "synthetic"
    UNVERIFIED = "unverified"


class Severity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SourceRef(BaseModel):
    source_id: str
    name: str
    url: str | None = None
    license: str | None = None
    observation_period: str | None = None


class ResponseMeta(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    region_id: str | None = None
    source_type: SourceType
    data_as_of: datetime
    model_version: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    limitations: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    units: dict[str, str] = Field(default_factory=dict)
    synthetic: bool = True
    geographic_resolution: str | None = None
    data_quality_status: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


class ApiError(BaseModel):
    code: str
    message: str
    request_id: UUID
    details: list[dict[str, Any]] = Field(default_factory=list)


class Region(BaseModel):
    id: str
    name: str
    region_type: str
    state: str
    country: str = "India"
    area_km2: float = Field(gt=0)
    centroid: tuple[float, float]
    source_type: SourceType = SourceType.SYNTHETIC


class EnsoObservation(BaseModel):
    period: date
    nino34_anomaly_c: float
    soi: float | None = None
    phase: str
    classification_basis: str


class WaterState(ScientificInput):
    storage_mcm: float = Field(ge=0)
    groundwater_index: float = Field(ge=0, le=1)
    rainfall_mm: float = Field(ge=0)
    inflow_mcm: float = Field(ge=0)
    evaporation_mcm: float = Field(ge=0)
    other_losses_mcm: float = Field(default=0, ge=0)
    capacity_mcm: float = Field(gt=0)


class SectorDemand(ScientificInput):
    domestic_mcm: float = Field(ge=0)
    agriculture_mcm: float = Field(ge=0)
    industrial_mcm: float = Field(ge=0)
    environmental_mcm: float = Field(ge=0)

    @property
    def total_mcm(self) -> float:
        return sum((self.domestic_mcm, self.agriculture_mcm, self.industrial_mcm, self.environmental_mcm))


class ScenarioCreate(ScientificInput):
    name: str = Field(min_length=3, max_length=100)
    region_id: str = "tn-coimbatore"
    months: int = Field(default=12, ge=1, le=120)
    rainfall_multiplier: float = Field(default=1, ge=0, le=3)
    temperature_delta_c: float = Field(default=0, ge=-5, le=10)
    demand_growth: float = Field(default=0, ge=-0.5, le=3)
    leakage_reduction: float = Field(default=0, ge=0, le=0.9)
    conservation: float = Field(default=0, ge=0, le=0.8)
    pumping_restriction: float = Field(default=0, ge=0, le=1)
    emergency_supply_mcm: float = Field(default=0, ge=0)
    seed: int = 42
    start_month: date = date(2026, 1, 1)

    @model_validator(mode="after")
    def month_start(self) -> "ScenarioCreate":
        if self.start_month.day != 1:
            raise ValueError("start_month must be the first day of a month")
        return self


class ScenarioRecord(ScenarioCreate):
    id: UUID = Field(default_factory=uuid4)
    status: str = "created"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MonthlyResult(BaseModel):
    month: int
    storage_mcm: float
    groundwater_index: float
    supply_mcm: float
    demand_mcm: float
    unmet_mcm: float
    spill_mcm: float
    valid_month: date | None = None
    inflow_mcm: float | None = None
    evaporation_mcm: float | None = None
    gross_release_mcm: float | None = None
    conveyance_loss_mcm: float | None = None
    mass_balance_residual_mcm: float | None = None


class ScenarioResult(BaseModel):
    scenario_id: UUID
    region_id: str
    trajectory: list[MonthlyResult]
    total_unmet_mcm: float
    reliability: float = Field(ge=0, le=1)
    mass_balance_error_mcm: float
    assumptions: list[str]
    initial_storage_mcm: float | None = None
    final_storage_mcm: float | None = None
    shortage_onset_month: int | None = None
    physical_constraint_violations: list[str] = Field(default_factory=list)


class MonteCarloRequest(ScientificInput):
    scenario: ScenarioCreate
    iterations: int = Field(default=250, ge=20, le=5000)
    rainfall_std_fraction: float = Field(default=0.15, gt=0, le=1)
    demand_std_fraction: float = Field(default=0.08, gt=0, le=1)


class OptimizationRequest(ScientificInput):
    region_id: str = "tn-coimbatore"
    available_water_mcm: float = Field(gt=0)
    demand: SectorDemand
    budget_million_inr: float = Field(default=100, ge=0)
    preserve_reserve_mcm: float = Field(default=10, ge=0)
    minimum_domestic_fraction: float = Field(default=0.9, ge=0, le=1)
    minimum_environmental_fraction: float = Field(default=0.6, ge=0, le=1)

    @model_validator(mode="after")
    def reserve_is_possible(self) -> "OptimizationRequest":
        if self.preserve_reserve_mcm >= self.available_water_mcm:
            raise ValueError("preserve_reserve_mcm must be below available_water_mcm")
        return self


class AdvisoryRequest(ScientificInput):
    region_id: str = "tn-coimbatore"
    audience: str = "households"
    language: str = Field(default="en", pattern="^(en|ta|hi)$")
    severity: Severity = Severity.MODERATE
    timeframe: str = "next 30 days"


class AssistantQuery(ScientificInput):
    question: str = Field(min_length=3, max_length=1000)
    region_id: str = "tn-coimbatore"


class MonthlyForecastPoint(ScientificInput):
    month: date
    rainfall_mm: float = Field(ge=0)


class BacktestRequest(ScientificInput):
    region_id: str = "tn-coimbatore"
    source_id: str = Field(min_length=3, max_length=80)
    observations: list[MonthlyForecastPoint] = Field(min_length=30, max_length=1200)
    min_train: int = Field(default=24, ge=24)
    synthetic: bool = False


class Fao56DailyInputs(ScientificInput):
    temp_min_c: float = Field(ge=-80, le=60)
    temp_max_c: float = Field(ge=-80, le=60)
    temp_mean_c: float = Field(ge=-80, le=60)
    net_radiation_mj_m2_day: float = Field(ge=0)
    soil_heat_flux_mj_m2_day: float = 0
    wind_speed_2m_m_s: float = Field(ge=0, le=100)
    actual_vapour_pressure_kpa: float = Field(ge=0)
    atmospheric_pressure_kpa: float = Field(ge=50, le=110)

    @model_validator(mode="after")
    def physically_consistent(self) -> "Fao56DailyInputs":
        if not self.temp_min_c <= self.temp_mean_c <= self.temp_max_c:
            raise ValueError("temperature range is inconsistent")
        if self.net_radiation_mj_m2_day < self.soil_heat_flux_mj_m2_day:
            raise ValueError("net radiation must be at least soil heat flux")
        return self


class InterventionOption(ScientificInput):
    kind: str = Field(pattern="^(conservation|leakage_reduction|emergency_supply)$")
    intensity: float = Field(gt=0)
    cost_million_inr: Decimal = Field(ge=0, max_digits=12, decimal_places=3)

    @model_validator(mode="after")
    def physical_limit(self) -> "InterventionOption":
        if self.kind in {"conservation", "leakage_reduction"} and self.intensity > 0.9:
            raise ValueError("fractional intervention intensity cannot exceed 0.9")
        return self


class InterventionPlanRequest(ScientificInput):
    scenario: ScenarioCreate
    budget_million_inr: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    options: list[InterventionOption] = Field(min_length=1, max_length=5)
    rainfall_cases: list[float] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def unique_options(self) -> "InterventionPlanRequest":
        if len({option.kind for option in self.options}) != len(self.options):
            raise ValueError("one option per intervention kind is allowed")
        if any(not 0 <= value <= 3 for value in self.rainfall_cases):
            raise ValueError("rainfall case multipliers must be between zero and three")
        for option in self.options:
            if option.kind == "conservation" and 1 - (1 - self.scenario.conservation) * (1 - option.intensity) > 0.8:
                raise ValueError("combined conservation exceeds scenario limit")
            if option.kind == "leakage_reduction" and 1 - (1 - self.scenario.leakage_reduction) * (1 - option.intensity) > 0.9:
                raise ValueError("combined leakage reduction exceeds scenario limit")
        return self


class ProposalCreate(ScientificInput):
    plan_id: UUID
    responsible_authority: str = Field(min_length=3, max_length=120)
    review_by: date
    rationale: str = Field(min_length=10, max_length=1000)


class ActionRecordCreate(ScientificInput):
    action_reference: str = Field(min_length=3, max_length=160)
    recorded_at: datetime
    note: str = Field(min_length=5, max_length=1000)

    @model_validator(mode="after")
    def utc_timestamp(self) -> "ActionRecordCreate":
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("recorded_at must include a timezone")
        return self


class OutcomeCreate(ScientificInput):
    observed_unmet_mcm: float = Field(ge=0)
    observation_source_id: str = Field(min_length=3, max_length=80)
    measured_at: datetime
    synthetic: bool = False

    @model_validator(mode="after")
    def utc_timestamp(self) -> "OutcomeCreate":
        if self.measured_at.tzinfo is None or self.measured_at.utcoffset() is None:
            raise ValueError("measured_at must include a timezone")
        return self

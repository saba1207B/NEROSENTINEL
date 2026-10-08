// Generated from the verified FastAPI OpenAPI schema. Do not edit by hand.
export type ActionRecordCreate = { action_reference: string; recorded_at: string; note: string; };
export type AdvisoryRequest = { region_id?: string; audience?: string; language?: string; severity?: Severity; timeframe?: string; };
export type AssistantQuery = { question: string; region_id?: string; };
export type BacktestRequest = { region_id?: string; source_id: string; observations: Array<MonthlyForecastPoint>; min_train?: number; synthetic?: boolean; };
export type Fao56DailyInputs = { temp_min_c: number; temp_max_c: number; temp_mean_c: number; net_radiation_mj_m2_day: number; soil_heat_flux_mj_m2_day?: number; wind_speed_2m_m_s: number; actual_vapour_pressure_kpa: number; atmospheric_pressure_kpa: number; };
export type HTTPValidationError = { detail?: Array<ValidationError>; };
export type InterventionOption = { kind: string; intensity: number; cost_million_inr: number | string; };
export type InterventionPlanRequest = { scenario: ScenarioCreate; budget_million_inr: number | string; options: Array<InterventionOption>; rainfall_cases: Array<number>; };
export type MonteCarloRequest = { scenario: ScenarioCreate; iterations?: number; rainfall_std_fraction?: number; demand_std_fraction?: number; };
export type MonthlyForecastPoint = { month: string; rainfall_mm: number; };
export type OptimizationRequest = { region_id?: string; available_water_mcm: number; demand: SectorDemand; budget_million_inr?: number; preserve_reserve_mcm?: number; minimum_domestic_fraction?: number; minimum_environmental_fraction?: number; };
export type OutcomeCreate = { observed_unmet_mcm: number; observation_source_id: string; measured_at: string; synthetic?: boolean; };
export type ProposalCreate = { plan_id: string; responsible_authority: string; review_by: string; rationale: string; };
export type ScenarioCreate = { name: string; region_id?: string; months?: number; rainfall_multiplier?: number; temperature_delta_c?: number; demand_growth?: number; leakage_reduction?: number; conservation?: number; pumping_restriction?: number; emergency_supply_mcm?: number; seed?: number; start_month?: string; };
export type SectorDemand = { domestic_mcm: number; agriculture_mcm: number; industrial_mcm: number; environmental_mcm: number; };
export type Severity = "low" | "moderate" | "high" | "critical";
export type ValidationError = { loc: Array<string | number>; msg: string; type: string; };

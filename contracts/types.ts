// Stable hand-authored frontend surface. Generate full clients from openapi.json.
export type SourceType = "observed" | "forecast" | "modeled" | "synthetic" | "unverified";

export interface SourceRef {
  source_id: string;
  name: string;
  url: string | null;
  license: string | null;
  observation_period: string | null;
}

export interface ResponseMeta {
  request_id: string;
  generated_at: string;
  region_id: string | null;
  source_type: SourceType;
  data_as_of: string;
  model_version: string | null;
  confidence: number | null;
  limitations: string[];
  sources: SourceRef[];
  units: Record<string, string>;
  synthetic: boolean;
  geographic_resolution: string | null;
  data_quality_status: string | null;
}

export interface ApiResponse<T> { data: T; meta: ResponseMeta; }

export interface ScenarioCreate {
  name: string;
  region_id?: string;
  months?: number;
  rainfall_multiplier?: number;
  temperature_delta_c?: number;
  demand_growth?: number;
  leakage_reduction?: number;
  conservation?: number;
  pumping_restriction?: number;
  emergency_supply_mcm?: number;
  seed?: number;
  start_month?: string;
}

export interface ScenarioResult {
  scenario_id: string;
  region_id: string;
  trajectory: Array<{month: number; valid_month: string | null; storage_mcm: number; groundwater_index: number; supply_mcm: number; demand_mcm: number; unmet_mcm: number; spill_mcm: number; inflow_mcm: number | null; evaporation_mcm: number | null; gross_release_mcm: number | null; conveyance_loss_mcm: number | null; mass_balance_residual_mcm: number | null}>;
  total_unmet_mcm: number;
  reliability: number;
  mass_balance_error_mcm: number;
  assumptions: string[];
  initial_storage_mcm: number | null;
  final_storage_mcm: number | null;
  shortage_onset_month: number | null;
  physical_constraint_violations: string[];
}

export type UserRole = 
  | 'Admin'
  | 'Sustainability Manager'
  | 'ESG Analyst'
  | 'Auditor'
  | 'Supplier'
  | 'C-Suite';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id?: string;
  facility_permissions?: string[];
  created_at?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  switchRole: (role: UserRole) => Promise<void>;
}

export interface HierarchyTreeNode {
  id: string;
  name: string;
  type: 'organization' | 'entity' | 'facility' | 'department' | 'cost_center';
  code: string;
  metadata?: Record<string, any>;
  children?: HierarchyTreeNode[];
}

export interface EmissionFactor {
  id: string;
  name: string;
  category: string;
  gas_type: string;
  factor_value: number;
  unit_numerator: string;
  unit_denominator: string;
  source: string;
  version: string;
  uncertainty_pct: number;
  description?: string;
  is_active: boolean;
}

export interface ActivityData {
  id: string;
  organization_id: string;
  entity_id: string;
  facility_id: string;
  scope: number;
  category: string;
  activity_type: string;
  quantity: number;
  unit: string;
  start_date: string;
  end_date: string;
  reporting_period: string;
  completeness_score: number;
  confidence_tier: 'high' | 'medium' | 'low' | 'estimated';
  validation_status: 'pending' | 'passed' | 'flagged' | 'rejected';
  anomaly_flag: boolean;
  source_document?: string;
  notes?: string;
  created_at: string;
}

export interface EmissionRecord {
  id: string;
  organization_id: string;
  entity_id: string;
  facility_id: string;
  activity_data_id: string;
  emission_factor_id: string;
  factor_version: string;
  scope: number;
  category: string;
  reporting_period: string;
  gross_emissions_tco2e: number;
  net_emissions_tco2e: number;
  rec_offset_tco2e: number;
  formula_string: string;
  unit_conversions_applied: string;
  allocation_method: string;
  approved_by?: string;
  approved_at?: string;
  is_scenario: boolean;
  scenario_id?: string;
  created_at: string;
}

export interface AuditLineageData {
  emission_record_id: string;
  scope: number;
  category: string;
  gross_emissions_tco2e: number;
  net_emissions_tco2e: number;
  formula_string: string;
  unit_conversions_applied: string;
  allocation_method: string;
  factor_version: string;
  factor_name: string;
  factor_source: string;
  factor_uncertainty_pct: number;
  source_activity: {
    id: string;
    quantity: number;
    unit: string;
    activity_type: string;
    completeness_score: number;
    confidence_tier: string;
    validation_status: string;
    anomaly_flag: boolean;
    source_document?: string;
  };
  governance: {
    approved_by?: string;
    approved_at?: string;
    created_at: string;
  };
}

export interface ProductItem {
  id: string;
  sku: string;
  name: string;
  category?: string;
  description?: string;
  functional_unit: string;
  unit_weight_kg: number;
  boms_count: number;
  latest_pcf_kgco2e?: number;
  latest_boundary?: string;
  created_at: string;
}

export interface SupplierItem {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  contact_name?: string;
  contact_email: string;
  tier: string;
  country: string;
  category: string;
  onboarding_status: string;
  spend_usd: number;
  scorecard?: {
    maturity_score: number;
    rating: string;
    emissions_scope1_2_tco2e: number;
    yoy_change_pct: number;
    sbti_committed: boolean;
    renewable_energy_pct: number;
  };
  action_plans_count: number;
  created_at: string;
}

export interface ScenarioItem {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  baseline_year: number;
  target_year: number;
  levers: Array<{
    name: string;
    scope: number;
    reduction_pct: number;
  }>;
  projected_reduction_tco2e: number;
  projected_reduction_pct: number;
  is_active: boolean;
  created_at: string;
}

export interface ReductionInitiative {
  id: string;
  name: string;
  lever_type: string;
  target_reduction_tco2e: number;
  actual_reduction_tco2e: number;
  capex_usd: number;
  opex_annual_usd: number;
  payback_years: number;
  status: string;
  created_at: string;
}

export interface ComplianceFramework {
  id: string;
  name: string;
  code: string;
  version: string;
  description?: string;
  jurisdiction: string;
}

export interface ComplianceDataPoint {
  id: string;
  framework_id: string;
  code: string;
  name: string;
  requirement_text: string;
  reported_value?: string;
  unit?: string;
  status: 'draft' | 'in_review' | 'verified' | 'approved' | 'submitted';
  calculation_link?: string;
  evidence_url?: string;
}

export interface ActionPlanResponse {
  id: string;
  supplier_id: string;
  initiative_name: string;
  description?: string;
  target_reduction_tco2e: number;
  due_date: string;
  status: string;
  assigned_to?: string;
  created_at: string;
}

export interface CBAMRecord {
  id: string;
  product_code: string;
  product_description: string;
  country_of_origin: string;
  reporting_quarter: string;
  imported_volume_tonnes: number;
  direct_embedded_emissions: number;
  indirect_embedded_emissions: number;
  total_embedded_emissions_tco2e: number;
  carbon_price_due_eur: number;
}

export interface ConnectorConfig {
  id: string;
  name: string;
  connector_type: string;
  status: 'active' | 'error' | 'idle';
  last_sync?: string;
  records_synced: number;
  error_message?: string;
  sync_frequency: string;
}

export interface WebhookLog {
  id: string;
  event_type: string;
  source: string;
  status: string;
  payload_preview: string;
  timestamp: string;
}

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime

class EmissionFactorBase(BaseModel):
    name: str
    category: str
    gas_type: str = "CO2e"
    factor_value: float
    unit_numerator: str = "tCO2e"
    unit_denominator: str
    source: str = "EPA"
    version: str = "2024.1"
    uncertainty_pct: float = 5.0
    description: Optional[str] = None
    is_active: bool = True

class EmissionFactorCreate(EmissionFactorBase):
    pass

class EmissionFactorResponse(EmissionFactorBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class ActivityDataBase(BaseModel):
    organization_id: str
    entity_id: str
    facility_id: str
    scope: int = Field(..., ge=1, le=3)
    category: str
    activity_type: str
    quantity: float
    unit: str
    start_date: date
    end_date: date
    reporting_period: str
    completeness_score: float = 1.0
    confidence_tier: str = "high"
    validation_status: str = "passed"
    anomaly_flag: bool = False
    source_document: Optional[str] = None
    notes: Optional[str] = None

class ActivityDataCreate(ActivityDataBase):
    emission_factor_id: Optional[str] = None
    allocation_pct: float = 100.0

class ActivityDataResponse(ActivityDataBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class EmissionRecordResponse(BaseModel):
    id: str
    organization_id: str
    entity_id: str
    facility_id: str
    activity_data_id: str
    emission_factor_id: str
    factor_version: str
    scope: int
    category: str
    reporting_period: str
    gross_emissions_tco2e: float
    net_emissions_tco2e: float
    rec_offset_tco2e: float
    formula_string: str
    unit_conversions_applied: str
    allocation_method: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    is_scenario: bool
    scenario_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class BaselineBase(BaseModel):
    organization_id: str
    base_year: int
    scope1_tco2e: float
    scope2_location_tco2e: float
    scope2_market_tco2e: float
    scope3_tco2e: float
    total_tco2e: float
    is_locked: bool = True
    restatement_reason: Optional[str] = None

class BaselineCreate(BaselineBase):
    pass

class BaselineResponse(BaselineBase):
    id: str
    restated_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class TargetBase(BaseModel):
    organization_id: str
    name: str
    target_type: str = "Absolute"
    scope_coverage: str = "Scope 1+2+3"
    baseline_year: int
    target_year: int
    target_reduction_pct: float
    current_progress_pct: float = 0.0
    trajectory_json: Optional[Any] = None

class TargetCreate(TargetBase):
    pass

class TargetResponse(TargetBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class RecalculatePreviewRequest(BaseModel):
    emission_factor_id: str
    new_factor_value: float
    new_version: str

class RecalculatePreviewResponse(BaseModel):
    factor_id: str
    affected_records_count: int
    current_total_tco2e: float
    projected_total_tco2e: float
    delta_tco2e: float
    delta_pct: float

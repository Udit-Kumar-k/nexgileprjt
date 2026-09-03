from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class ReductionLever(BaseModel):
    name: str
    scope: int
    reduction_pct: float
    category: Optional[str] = None

class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    baseline_year: int = 2023
    target_year: int = 2030
    levers: List[ReductionLever]

class ScenarioCreate(ScenarioBase):
    organization_id: str

class ScenarioResponse(ScenarioBase):
    id: str
    organization_id: str
    projected_reduction_tco2e: float
    projected_reduction_pct: float
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ScenarioSimulateRequest(BaseModel):
    baseline_year: int = 2023
    levers: List[ReductionLever]

class ReductionInitiativeBase(BaseModel):
    name: str
    lever_type: str
    target_reduction_tco2e: float
    actual_reduction_tco2e: float = 0.0
    capex_usd: float = 0.0
    opex_annual_usd: float = 0.0
    payback_years: float = 0.0
    status: str = "active"

class ReductionInitiativeCreate(ReductionInitiativeBase):
    organization_id: str

class ReductionInitiativeResponse(ReductionInitiativeBase):
    id: str
    organization_id: str
    created_at: datetime
    class Config:
        from_attributes = True

class AnomalyResolveRequest(BaseModel):
    status: str # reviewed, resolved, dismissed
    resolution_notes: Optional[str] = None

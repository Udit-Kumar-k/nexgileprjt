from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import date, datetime

class SupplierBase(BaseModel):
    name: str
    code: str
    contact_name: Optional[str] = None
    contact_email: EmailStr
    tier: str = "Tier 1"
    country: str
    category: str
    spend_usd: float = 0.0
    onboarding_status: str = "invited"

class SupplierCreate(SupplierBase):
    organization_id: str

class SupplierResponse(SupplierBase):
    id: str
    organization_id: str
    created_at: datetime
    class Config:
        from_attributes = True

class QuestionnaireBase(BaseModel):
    title: str
    description: Optional[str] = None
    materiality_category: str = "Manufacturing & Energy"
    questions: List[Any]

class QuestionnaireCreate(QuestionnaireBase):
    organization_id: str

class QuestionnaireResponse(QuestionnaireBase):
    id: str
    organization_id: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    questionnaire_id: str
    supplier_id: str
    responses: Any
    attestation_name: Optional[str] = None
    status: str = "submitted"

class ScorecardBase(BaseModel):
    supplier_id: str
    reporting_year: int
    emissions_scope1_2_tco2e: float
    emissions_intensity: Optional[float] = None
    maturity_score: float
    rating: str = "B"
    yoy_change_pct: float = 0.0
    cdp_score: Optional[str] = "B"
    sbti_committed: bool = False
    renewable_energy_pct: float = 0.0

class ScorecardCreate(ScorecardBase):
    pass

class ScorecardResponse(ScorecardBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class ActionPlanBase(BaseModel):
    supplier_id: str
    initiative_name: str
    description: Optional[str] = None
    target_reduction_tco2e: float
    due_date: date
    status: str = "in_progress"
    assigned_to: Optional[str] = None

class ActionPlanCreate(ActionPlanBase):
    pass

class ActionPlanResponse(ActionPlanBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SupplierInviteRequest(BaseModel):
    email: EmailStr
    supplier_name: str
    tier: str = "Tier 1"
    country: str
    category: str
    questionnaire_id: Optional[str] = None

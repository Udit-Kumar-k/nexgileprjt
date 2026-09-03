from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class FrameworkBase(BaseModel):
    name: str
    code: str
    version: str = "2024"
    description: Optional[str] = None
    jurisdiction: str = "EU / Global"

class FrameworkResponse(FrameworkBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class DataPointBase(BaseModel):
    framework_id: str
    code: str
    name: str
    requirement_text: str
    reported_value: Optional[str] = None
    unit: Optional[str] = None
    status: str = "draft"
    calculation_link: Optional[str] = None
    evidence_url: Optional[str] = None

class DataPointCreate(DataPointBase):
    pass

class DataPointResponse(DataPointBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class DataPointStatusUpdate(BaseModel):
    status: str
    reported_value: Optional[str] = None

class EvidenceBase(BaseModel):
    title: str
    file_name: str
    file_size_kb: float = 120.0
    content_type: str = "application/pdf"
    file_url: str
    verification_status: str = "verified"
    linked_data_points: List[str] = []

class EvidenceCreate(EvidenceBase):
    organization_id: str

class EvidenceResponse(EvidenceBase):
    id: str
    organization_id: str
    created_at: datetime
    class Config:
        from_attributes = True

class CBAMRecordBase(BaseModel):
    product_code: str
    product_description: str
    country_of_origin: str
    reporting_quarter: str
    imported_volume_tonnes: float
    direct_embedded_emissions: float
    indirect_embedded_emissions: float
    total_embedded_emissions_tco2e: float
    carbon_price_due_eur: float = 0.0

class CBAMRecordCreate(CBAMRecordBase):
    organization_id: str

class CBAMRecordResponse(CBAMRecordBase):
    id: str
    organization_id: str
    created_at: datetime
    class Config:
        from_attributes = True

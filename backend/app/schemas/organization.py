from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# CostCenter
class CostCenterBase(BaseModel):
    name: str
    code: str
    budget_currency: str = "USD"

class CostCenterCreate(CostCenterBase):
    department_id: str

class CostCenterResponse(CostCenterBase):
    id: str
    department_id: str
    created_at: datetime
    class Config:
        from_attributes = True

# Department
class DepartmentBase(BaseModel):
    name: str
    code: str

class DepartmentCreate(DepartmentBase):
    facility_id: str

class DepartmentResponse(DepartmentBase):
    id: str
    facility_id: str
    cost_centers: List[CostCenterResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

# Facility
class FacilityBase(BaseModel):
    name: str
    code: str
    facility_type: str = "Manufacturing"
    address: Optional[str] = None
    country: str
    grid_region: Optional[str] = None

class FacilityCreate(FacilityBase):
    entity_id: str

class FacilityResponse(FacilityBase):
    id: str
    entity_id: str
    departments: List[DepartmentResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

# Reporting Boundary
class ReportingBoundaryBase(BaseModel):
    reporting_year: int
    boundary_type: str = "Operational Control"
    consolidation_approach: str = "100% Operational Control"
    is_active: str = "Active"
    notes: Optional[str] = None

class ReportingBoundaryCreate(ReportingBoundaryBase):
    entity_id: str

class ReportingBoundaryResponse(ReportingBoundaryBase):
    id: str
    entity_id: str
    created_at: datetime
    class Config:
        from_attributes = True

# Entity
class EntityBase(BaseModel):
    name: str
    code: str
    country: str
    consolidation_method: str = "Operational Control"
    ownership_percentage: float = 100.0

class EntityCreate(EntityBase):
    organization_id: str

class EntityResponse(EntityBase):
    id: str
    organization_id: str
    facilities: List[FacilityResponse] = []
    boundaries: List[ReportingBoundaryResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

# Organization
class OrganizationBase(BaseModel):
    name: str
    code: str
    sector: Optional[str] = None
    country: Optional[str] = None
    reporting_currency: str = "USD"

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    id: str
    entities: List[EntityResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

class HierarchyTreeNode(BaseModel):
    id: str
    name: str
    type: str  # organization, entity, facility, department, cost_center
    code: str
    metadata: Optional[dict] = None
    children: List["HierarchyTreeNode"] = []

HierarchyTreeNode.model_rebuild()

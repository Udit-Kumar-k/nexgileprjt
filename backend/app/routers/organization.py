from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.core.rbac import get_current_user, require_roles, Role, EDIT_ROLES, READ_ONLY_ROLES
from app.models.auth import User
from app.models.organization import (
    Organization,
    Entity,
    Facility,
    Department,
    CostCenter,
    ReportingBoundary
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    EntityCreate,
    EntityResponse,
    FacilityCreate,
    FacilityResponse,
    DepartmentCreate,
    DepartmentResponse,
    CostCenterCreate,
    CostCenterResponse,
    ReportingBoundaryCreate,
    ReportingBoundaryResponse,
    HierarchyTreeNode
)

router = APIRouter(prefix="/organization", tags=["Organization Hierarchy"])

@router.get("/tree", response_model=List[HierarchyTreeNode])
def get_hierarchy_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the full hierarchical ownership tree for the user's organization."""
    query = db.query(Organization).filter(Organization.is_deleted == False)
    if current_user.organization_id:
        query = query.filter(Organization.id == current_user.organization_id)
    
    orgs = query.all()
    tree: List[HierarchyTreeNode] = []

    for org in orgs:
        org_node = HierarchyTreeNode(
            id=org.id,
            name=org.name,
            code=org.code,
            type="organization",
            metadata={"sector": org.sector, "country": org.country, "currency": org.reporting_currency},
            children=[]
        )
        
        entities = db.query(Entity).filter(Entity.organization_id == org.id, Entity.is_deleted == False).all()
        for ent in entities:
            ent_node = HierarchyTreeNode(
                id=ent.id,
                name=ent.name,
                code=ent.code,
                type="entity",
                metadata={"country": ent.country, "consolidation": ent.consolidation_method, "ownership": ent.ownership_percentage},
                children=[]
            )
            
            facilities = db.query(Facility).filter(Facility.entity_id == ent.id, Facility.is_deleted == False).all()
            for fac in facilities:
                # Check user facility permissions if not Admin
                if current_user.role != Role.ADMIN.value and current_user.facility_permissions and fac.id not in current_user.facility_permissions:
                    continue
                
                fac_node = HierarchyTreeNode(
                    id=fac.id,
                    name=fac.name,
                    code=fac.code,
                    type="facility",
                    metadata={"type": fac.facility_type, "country": fac.country, "grid_region": fac.grid_region},
                    children=[]
                )
                
                depts = db.query(Department).filter(Department.facility_id == fac.id, Department.is_deleted == False).all()
                for dep in depts:
                    dep_node = HierarchyTreeNode(
                        id=dep.id,
                        name=dep.name,
                        code=dep.code,
                        type="department",
                        metadata={},
                        children=[]
                    )
                    
                    ccs = db.query(CostCenter).filter(CostCenter.department_id == dep.id, CostCenter.is_deleted == False).all()
                    for cc in ccs:
                        cc_node = HierarchyTreeNode(
                            id=cc.id,
                            name=cc.name,
                            code=cc.code,
                            type="cost_center",
                            metadata={"currency": cc.budget_currency},
                            children=[]
                        )
                        dep_node.children.append(cc_node)
                    fac_node.children.append(dep_node)
                ent_node.children.append(fac_node)
            org_node.children.append(ent_node)
        tree.append(org_node)
    
    return tree

# Organizations CRUD
@router.get("", response_model=List[OrganizationResponse])
def list_organizations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Organization).filter(Organization.is_deleted == False).all()

@router.post("", response_model=OrganizationResponse)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN, Role.SUSTAINABILITY_MANAGER]))
):
    org = Organization(**payload.model_dump(), created_by=current_user.id)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

# Entities CRUD
@router.get("/entities", response_model=List[EntityResponse])
def list_entities(org_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Entity).filter(Entity.is_deleted == False)
    if org_id:
        q = q.filter(Entity.organization_id == org_id)
    return q.all()

@router.post("/entities", response_model=EntityResponse)
def create_entity(
    payload: EntityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    entity = Entity(**payload.model_dump(), created_by=current_user.id)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity

# Facilities CRUD
@router.get("/facilities", response_model=List[FacilityResponse])
def list_facilities(entity_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Facility).filter(Facility.is_deleted == False)
    if entity_id:
        q = q.filter(Facility.entity_id == entity_id)
    facilities = q.all()
    if current_user.role != Role.ADMIN.value and current_user.facility_permissions:
        facilities = [f for f in facilities if f.id in current_user.facility_permissions]
    return facilities

@router.post("/facilities", response_model=FacilityResponse)
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    fac = Facility(**payload.model_dump(), created_by=current_user.id)
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac

# Departments CRUD
@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(facility_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Department).filter(Department.is_deleted == False)
    if facility_id:
        q = q.filter(Department.facility_id == facility_id)
    return q.all()

@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    dep = Department(**payload.model_dump(), created_by=current_user.id)
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep

# Cost Centers CRUD
@router.get("/cost-centers", response_model=List[CostCenterResponse])
def list_cost_centers(department_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(CostCenter).filter(CostCenter.is_deleted == False)
    if department_id:
        q = q.filter(CostCenter.department_id == department_id)
    return q.all()

@router.post("/cost-centers", response_model=CostCenterResponse)
def create_cost_center(
    payload: CostCenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    cc = CostCenter(**payload.model_dump(), created_by=current_user.id)
    db.add(cc)
    db.commit()
    db.refresh(cc)
    return cc

# Reporting Boundaries CRUD
@router.get("/boundaries", response_model=List[ReportingBoundaryResponse])
def list_boundaries(entity_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(ReportingBoundary).filter(ReportingBoundary.is_deleted == False)
    if entity_id:
        q = q.filter(ReportingBoundary.entity_id == entity_id)
    return q.all()

@router.post("/boundaries", response_model=ReportingBoundaryResponse)
def create_boundary(
    payload: ReportingBoundaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    b = ReportingBoundary(**payload.model_dump(), created_by=current_user.id)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io

from app.db import get_db
from app.core.rbac import get_current_user, require_roles, Role, EDIT_ROLES
from app.models.auth import User
from app.models.compliance import (
    Framework,
    Disclosure,
    DataPoint,
    Evidence,
    AssuranceRequest,
    CreditOffset,
    CBAMRecord
)
from app.schemas.compliance import (
    FrameworkResponse,
    DataPointCreate,
    DataPointResponse,
    DataPointStatusUpdate,
    EvidenceCreate,
    EvidenceResponse,
    CBAMRecordCreate,
    CBAMRecordResponse
)

router = APIRouter(prefix="/compliance", tags=["Regulatory Compliance & Disclosure"])

# ==============================================================================
# Frameworks & Data Points Checklist
# ==============================================================================

@router.get("/frameworks", response_model=List[FrameworkResponse])
def list_frameworks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Framework).filter(Framework.is_deleted == False).all()

@router.get("/frameworks/{framework_id}/datapoints", response_model=List[DataPointResponse])
def list_datapoints(
    framework_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(DataPoint).filter(
        DataPoint.framework_id == framework_id,
        DataPoint.is_deleted == False
    )
    if status:
        q = q.filter(DataPoint.status == status)
    return q.order_by(DataPoint.code.asc()).all()

@router.put("/datapoints/{id}/status", response_model=DataPointResponse)
def update_datapoint_status(
    id: str,
    payload: DataPointStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    dp = db.query(DataPoint).filter(DataPoint.id == id, DataPoint.is_deleted == False).first()
    if not dp:
        raise HTTPException(status_code=404, detail="DataPoint not found")
    
    dp.status = payload.status
    if payload.reported_value is not None:
        dp.reported_value = payload.reported_value
    
    db.commit()
    db.refresh(dp)
    return dp

# ==============================================================================
# Evidence Library
# ==============================================================================

@router.get("/evidence", response_model=List[EvidenceResponse])
def list_evidence(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Evidence).filter(Evidence.is_deleted == False).all()

@router.post("/evidence", response_model=EvidenceResponse)
def create_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    ev = Evidence(**payload.model_dump(), created_by=current_user.id)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev

# ==============================================================================
# CBAM Module
# ==============================================================================

@router.get("/cbam", response_model=List[CBAMRecordResponse])
def list_cbam_records(
    quarter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(CBAMRecord).filter(CBAMRecord.is_deleted == False)
    if quarter:
        q = q.filter(CBAMRecord.reporting_quarter == quarter)
    return q.all()

@router.post("/cbam", response_model=CBAMRecordResponse)
def create_cbam_record(
    payload: CBAMRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    rec = CBAMRecord(**payload.model_dump(), created_by=current_user.id)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

# ==============================================================================
# Export: Disclosure Table as CSV
# ==============================================================================

@router.get("/export/csv")
def export_disclosure_csv(
    framework_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(DataPoint).filter(DataPoint.is_deleted == False)
    if framework_id:
        q = q.filter(DataPoint.framework_id == framework_id)
    datapoints = q.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["DataPoint Code", "Requirement Name", "Reported Value", "Unit", "Verification Status", "Source Calculation", "Evidence Reference"])

    for dp in datapoints:
        writer.writerow([
            dp.code,
            dp.name,
            dp.reported_value or "Pending",
            dp.unit or "",
            dp.status,
            dp.calculation_link or "",
            dp.evidence_url or ""
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=decarbx_compliance_disclosure.csv"}
    )

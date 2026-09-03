from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.db import get_db
from app.core.rbac import get_current_user, require_roles, Role, EDIT_ROLES, READ_ONLY_ROLES, verify_facility_access
from app.models.auth import User
from app.models.carbon import (
    EmissionFactor,
    ActivityData,
    Calculation,
    EmissionRecord,
    Baseline,
    Target
)
from app.schemas.carbon import (
    EmissionFactorCreate,
    EmissionFactorResponse,
    ActivityDataCreate,
    ActivityDataResponse,
    EmissionRecordResponse,
    BaselineCreate,
    BaselineResponse,
    TargetCreate,
    TargetResponse,
    RecalculatePreviewRequest,
    RecalculatePreviewResponse
)
from app.services.calc_engine import calculate_emissions
from app.services.csv_import import parse_and_import_activity_csv

ANOMALY_THRESHOLD_PCT = 0.30  # Standardized 30% deviation threshold across platform

router = APIRouter(prefix="/carbon", tags=["Enterprise Carbon Accounting"])

# ==============================================================================
# Emission Factor Library (CRUD, Versioning, Recalculation Impact Preview)
# ==============================================================================

@router.get("/factors", response_model=List[EmissionFactorResponse])
def list_emission_factors(
    category: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(EmissionFactor).filter(EmissionFactor.is_deleted == False)
    if category:
        q = q.filter(EmissionFactor.category == category)
    if source:
        q = q.filter(EmissionFactor.source == source)
    if search:
        q = q.filter(EmissionFactor.name.ilike(f"%{search}%"))
    return q.all()

@router.post("/factors", response_model=EmissionFactorResponse)
def create_emission_factor(
    payload: EmissionFactorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    factor = EmissionFactor(**payload.model_dump(), created_by=current_user.id)
    db.add(factor)
    db.commit()
    db.refresh(factor)
    return factor

@router.put("/factors/{id}", response_model=EmissionFactorResponse)
def update_emission_factor(
    id: str,
    payload: EmissionFactorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == id, EmissionFactor.is_deleted == False).first()
    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")
    
    for key, value in payload.model_dump().items():
        setattr(factor, key, value)
    
    db.commit()
    db.refresh(factor)
    return factor

@router.delete("/factors/{id}")
def delete_emission_factor(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN, Role.SUSTAINABILITY_MANAGER]))
):
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == id, EmissionFactor.is_deleted == False).first()
    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")
    
    factor.is_deleted = True
    db.commit()
    return {"message": "Emission factor soft-deleted successfully", "id": id}

@router.post("/factors/recalculate-preview", response_model=RecalculatePreviewResponse)
def preview_factor_recalculation(
    payload: RecalculatePreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    """Calculation Governance: Changes to factor versions trigger impact preview."""
    records = db.query(EmissionRecord).filter(
        EmissionRecord.emission_factor_id == payload.emission_factor_id,
        EmissionRecord.is_scenario == False,
        EmissionRecord.is_deleted == False
    ).all()

    current_total = sum(r.gross_emissions_tco2e for r in records)
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == payload.emission_factor_id).first()
    
    if not factor or factor.factor_value == 0:
        return RecalculatePreviewResponse(
            factor_id=payload.emission_factor_id,
            affected_records_count=len(records),
            current_total_tco2e=round(current_total, 4),
            projected_total_tco2e=round(current_total, 4),
            delta_tco2e=0.0,
            delta_pct=0.0
        )

    ratio = payload.new_factor_value / factor.factor_value
    projected_total = current_total * ratio
    delta = projected_total - current_total
    delta_pct = (delta / current_total * 100.0) if current_total > 0 else 0.0

    return RecalculatePreviewResponse(
        factor_id=payload.emission_factor_id,
        affected_records_count=len(records),
        current_total_tco2e=round(current_total, 4),
        projected_total_tco2e=round(projected_total, 4),
        delta_tco2e=round(delta, 4),
        delta_pct=round(delta_pct, 2)
    )

@router.post("/factors/{id}/apply")
def apply_factor_recalculation(
    id: str,
    payload: RecalculatePreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN, Role.SUSTAINABILITY_MANAGER]))
):
    """Applies factor version update and recalculates all associated historical emission records."""
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == id, EmissionFactor.is_deleted == False).first()
    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    old_val = factor.factor_value
    factor.factor_value = payload.new_factor_value
    factor.version = payload.new_version or f"{factor.version}.1"

    records = db.query(EmissionRecord).filter(
        EmissionRecord.emission_factor_id == id,
        EmissionRecord.is_scenario == False,
        EmissionRecord.is_deleted == False
    ).all()

    ratio = payload.new_factor_value / old_val if old_val > 0 else 1.0
    for r in records:
        r.gross_emissions_tco2e = round(r.gross_emissions_tco2e * ratio, 6)
        r.net_emissions_tco2e = round(r.net_emissions_tco2e * ratio, 6)
        r.factor_version = factor.version

    db.commit()
    return {
        "message": f"Successfully updated factor to v{factor.version} and recalculated {len(records)} records.",
        "factor_id": factor.id,
        "new_version": factor.version,
        "affected_records": len(records)
    }

# ==============================================================================
# Activity Data Ledger & Automatic Calculation with Audit Lineage
# ==============================================================================

@router.get("/activity", response_model=List[ActivityDataResponse])
def list_activity_data(
    scope: Optional[int] = None,
    facility_id: Optional[str] = None,
    validation_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(ActivityData).filter(ActivityData.is_deleted == False)
    if current_user.role != Role.ADMIN.value and current_user.facility_permissions:
        q = q.filter(ActivityData.facility_id.in_(current_user.facility_permissions))
    if scope:
        q = q.filter(ActivityData.scope == scope)
    if facility_id:
        q = q.filter(ActivityData.facility_id == facility_id)
    if validation_status:
        q = q.filter(ActivityData.validation_status == validation_status)
    return q.order_by(ActivityData.start_date.desc()).all()

@router.post("/activity", response_model=ActivityDataResponse)
def create_activity_data(
    payload: ActivityDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    # Rule 4: Tenant/facility segregation
    if current_user.role != Role.ADMIN.value and current_user.facility_permissions:
        if payload.facility_id not in current_user.facility_permissions:
            raise HTTPException(status_code=403, detail="Not authorized to submit activity data for this facility")

    # Find factor
    factor = None
    if payload.emission_factor_id:
        factor = db.query(EmissionFactor).filter(
            EmissionFactor.id == payload.emission_factor_id,
            EmissionFactor.is_deleted == False
        ).first()
    
    # Auto-match factor by category if not explicitly specified
    if not factor:
        factor = db.query(EmissionFactor).filter(
            EmissionFactor.category.ilike(f"%{payload.category}%"),
            EmissionFactor.is_active == True,
            EmissionFactor.is_deleted == False
        ).first()

    if not factor:
        # Fallback default factor to prevent calculation failure
        factor = db.query(EmissionFactor).filter(EmissionFactor.is_active == True).first()

    data_dict = payload.model_dump()
    emission_factor_id = data_dict.pop("emission_factor_id", None)
    allocation_pct = data_dict.pop("allocation_pct", 100.0)

    # Anomaly detection check (standardized 30% deviation threshold against facility rolling average)
    recent_activities = db.query(ActivityData).filter(
        ActivityData.facility_id == payload.facility_id,
        ActivityData.activity_type == payload.activity_type,
        ActivityData.is_deleted == False
    ).limit(6).all()

    anomaly_detected = False
    if recent_activities:
        avg_quantity = sum(a.quantity for a in recent_activities) / len(recent_activities)
        if avg_quantity > 0:
            pct_diff = abs(payload.quantity - avg_quantity) / avg_quantity
            if pct_diff > ANOMALY_THRESHOLD_PCT:  # 30% deviation
                anomaly_detected = True

    activity = ActivityData(
        **data_dict,
        anomaly_flag=anomaly_detected,
        created_by=current_user.id
    )
    db.add(activity)
    db.flush()

    # Rule 1: Audit lineage & Backend Calculation Engine
    if factor:
        calc_result = calculate_emissions(
            quantity=activity.quantity,
            unit=activity.unit,
            factor_value=factor.factor_value,
            factor_denominator=factor.unit_denominator,
            uncertainty_pct=factor.uncertainty_pct,
            allocation_pct=allocation_pct
        )

        calculation = Calculation(
            activity_data_id=activity.id,
            factor_id=factor.id,
            factor_version=factor.version,
            formula_applied=calc_result["formula_string"],
            unit_conversion_factor=calc_result["unit_conversion_factor"],
            allocation_pct=allocation_pct,
            emissions_tco2e=calc_result["gross_emissions_tco2e"],
            uncertainty_min_tco2e=calc_result["uncertainty_min_tco2e"],
            uncertainty_max_tco2e=calc_result["uncertainty_max_tco2e"],
            created_by=current_user.id
        )
        db.add(calculation)

        emission_record = EmissionRecord(
            organization_id=activity.organization_id,
            entity_id=activity.entity_id,
            facility_id=activity.facility_id,
            activity_data_id=activity.id,
            emission_factor_id=factor.id,
            factor_version=factor.version,
            scope=activity.scope,
            category=activity.category,
            reporting_period=activity.reporting_period,
            gross_emissions_tco2e=calc_result["gross_emissions_tco2e"],
            net_emissions_tco2e=calc_result["net_emissions_tco2e"],
            rec_offset_tco2e=calc_result["rec_offset_tco2e"],
            formula_string=calc_result["formula_string"],
            unit_conversions_applied=calc_result["unit_conversions_applied"],
            allocation_method=f"{allocation_pct}% Allocation",
            is_scenario=False,
            created_by=current_user.id
        )
        db.add(emission_record)

    db.commit()
    db.refresh(activity)
    return activity

@router.put("/activity/{id}", response_model=ActivityDataResponse)
def update_activity_data(
    id: str,
    payload: ActivityDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    activity = db.query(ActivityData).filter(ActivityData.id == id, ActivityData.is_deleted == False).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity data record not found")

    data_dict = payload.model_dump()
    data_dict.pop("emission_factor_id", None)
    data_dict.pop("allocation_pct", None)

    for key, value in data_dict.items():
        setattr(activity, key, value)

    # Recalculate linked emission record
    calc = db.query(Calculation).filter(Calculation.activity_data_id == id, Calculation.is_deleted == False).first()
    rec = db.query(EmissionRecord).filter(EmissionRecord.activity_data_id == id, Calculation.is_deleted == False).first()
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == calc.factor_id).first() if calc else None

    if calc and rec and factor:
        calc_res = calculate_emissions(
            quantity=activity.quantity,
            unit=activity.unit,
            factor_value=factor.factor_value,
            factor_denominator=factor.unit_denominator,
            uncertainty_pct=factor.uncertainty_pct,
            allocation_pct=calc.allocation_pct
        )
        calc.emissions_tco2e = calc_res["gross_emissions_tco2e"]
        calc.formula_applied = calc_res["formula_string"]
        rec.gross_emissions_tco2e = calc_res["gross_emissions_tco2e"]
        rec.net_emissions_tco2e = calc_res["net_emissions_tco2e"]
        rec.formula_string = calc_res["formula_string"]

    db.commit()
    db.refresh(activity)
    return activity

@router.delete("/activity/{id}")
def delete_activity_data(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    activity = db.query(ActivityData).filter(ActivityData.id == id, ActivityData.is_deleted == False).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity data record not found")

    activity.is_deleted = True
    # Soft delete linked calculation and emission record
    db.query(Calculation).filter(Calculation.activity_data_id == id).update({"is_deleted": True})
    db.query(EmissionRecord).filter(EmissionRecord.activity_data_id == id).update({"is_deleted": True})

    db.commit()
    return {"message": "Activity data record soft-deleted successfully", "id": id}

@router.post("/activity/import")
async def import_activity_csv_file(
    file: UploadFile = File(...),
    organization_id: str = Query(...),
    entity_id: str = Query(...),
    facility_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    """Batch activity CSV file upload calling the calculation and data quality ingestion engine."""
    content = await file.read()
    csv_text = content.decode("utf-8-sig")

    result = parse_and_import_activity_csv(
        csv_content=csv_text,
        organization_id=organization_id,
        entity_id=entity_id,
        facility_id=facility_id,
        user_id=current_user.id,
        db=db
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to import CSV"))

    return result

# ==============================================================================
# Emission Records & Audit Lineage Inspection
# ==============================================================================

@router.get("/emissions", response_model=List[EmissionRecordResponse])
def list_emission_records(
    scope: Optional[int] = None,
    facility_id: Optional[str] = None,
    period: Optional[str] = None,
    activity_data_id: Optional[str] = None,
    include_scenarios: bool = False,
    scenario_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Strict Rule 3: Scenario isolation - scenarios excluded from actuals queries by default."""
    q = db.query(EmissionRecord).filter(EmissionRecord.is_deleted == False)

    if current_user.role != Role.ADMIN.value and current_user.facility_permissions:
        q = q.filter(EmissionRecord.facility_id.in_(current_user.facility_permissions))

    if not include_scenarios and not scenario_id:
        q = q.filter(EmissionRecord.is_scenario == False)
    elif scenario_id:
        q = q.filter(EmissionRecord.scenario_id == scenario_id)

    if scope:
        q = q.filter(EmissionRecord.scope == scope)
    if facility_id:
        q = q.filter(EmissionRecord.facility_id == facility_id)
    if period:
        q = q.filter(EmissionRecord.reporting_period == period)
    if activity_data_id:
        q = q.filter(EmissionRecord.activity_data_id == activity_data_id)

    return q.order_by(EmissionRecord.created_at.desc()).all()

@router.get("/emissions/by-activity/{activity_data_id}", response_model=EmissionRecordResponse)
def get_emission_by_activity(
    activity_data_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct lookup of emission record by activity ID (O(1) lookup avoiding full table scans)."""
    record = db.query(EmissionRecord).filter(
        EmissionRecord.activity_data_id == activity_data_id,
        EmissionRecord.is_deleted == False
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Emission record not found for this activity")
    return record

@router.get("/emissions/{id}/audit")
def get_emission_audit_lineage(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rule 1: Audit lineage viewer returning source activity, factor version, formula string, and approvals."""
    record = db.query(EmissionRecord).filter(EmissionRecord.id == id, EmissionRecord.is_deleted == False).first()
    if not record:
        raise HTTPException(status_code=404, detail="Emission record not found")
    
    activity = db.query(ActivityData).filter(ActivityData.id == record.activity_data_id).first()
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == record.emission_factor_id).first()

    return {
        "emission_record_id": record.id,
        "scope": record.scope,
        "category": record.category,
        "gross_emissions_tco2e": record.gross_emissions_tco2e,
        "net_emissions_tco2e": record.net_emissions_tco2e,
        "formula_string": record.formula_string,
        "unit_conversions_applied": record.unit_conversions_applied or "Direct factor unit match",
        "allocation_method": record.allocation_method,
        "factor_version": record.factor_version,
        "factor_name": factor.name if factor else "Standard Emission Factor",
        "factor_source": factor.source if factor else "DEFRA / EPA",
        "factor_uncertainty_pct": factor.uncertainty_pct if factor else 5.0,
        "source_activity": {
            "id": activity.id if activity else None,
            "quantity": activity.quantity if activity else None,
            "unit": activity.unit if activity else None,
            "activity_type": activity.activity_type if activity else "N/A",
            "completeness_score": activity.completeness_score if activity else 1.0,
            "confidence_tier": activity.confidence_tier if activity else "high",
            "validation_status": activity.validation_status if activity else None,
            "anomaly_flag": activity.anomaly_flag if activity else False,
            "source_document": activity.source_document if activity else "Direct Entry"
        },
        "governance": {
            "approved_by": record.approved_by,
            "approved_at": record.approved_at,
            "created_at": record.created_at
        }
    }

@router.put("/emissions/{id}/approve", response_model=EmissionRecordResponse)
def approve_emission_record(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN, Role.SUSTAINABILITY_MANAGER, Role.AUDITOR]))
):
    record = db.query(EmissionRecord).filter(EmissionRecord.id == id, EmissionRecord.is_deleted == False).first()
    if not record:
        raise HTTPException(status_code=404, detail="Emission record not found")

    record.approved_by = current_user.email
    record.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record

# ==============================================================================
# Baselines & Target Trajectories (Tenant Isolated)
# ==============================================================================

@router.get("/baselines", response_model=List[BaselineResponse])
def list_baselines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Baseline).filter(Baseline.is_deleted == False)
    if current_user.organization_id:
        q = q.filter(Baseline.organization_id == current_user.organization_id)
    return q.all()

@router.post("/baselines", response_model=BaselineResponse)
def create_baseline(
    payload: BaselineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN, Role.SUSTAINABILITY_MANAGER]))
):
    org_id = payload.organization_id or current_user.organization_id
    base = Baseline(**payload.model_dump(), organization_id=org_id, created_by=current_user.id)
    db.add(base)
    db.commit()
    db.refresh(base)
    return base

@router.put("/baselines/{id}/restate", response_model=BaselineResponse)
def restate_baseline(
    id: str,
    restatement_reason: str,
    new_scope1: float,
    new_scope2_loc: float,
    new_scope2_mkt: float,
    new_scope3: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN, Role.SUSTAINABILITY_MANAGER]))
):
    """Baseline Restatement: recalculates total gross emissions including Location Scope 2."""
    q = db.query(Baseline).filter(Baseline.id == id, Baseline.is_deleted == False)
    if current_user.organization_id:
        q = q.filter(Baseline.organization_id == current_user.organization_id)
    base = q.first()
    if not base:
        raise HTTPException(status_code=404, detail="Baseline not found")

    base.scope1_tco2e = new_scope1
    base.scope2_location_tco2e = new_scope2_loc
    base.scope2_market_tco2e = new_scope2_mkt
    base.scope3_tco2e = new_scope3
    # Correct calculation: total gross baseline includes Location Scope 2 per GHG Protocol
    base.total_tco2e = round(new_scope1 + new_scope2_loc + new_scope3, 4)
    base.restatement_reason = restatement_reason
    base.restated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(base)
    return base

@router.get("/targets", response_model=List[TargetResponse])
def list_targets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Target).filter(Target.is_deleted == False)
    if current_user.organization_id:
        q = q.filter(Target.organization_id == current_user.organization_id)
    return q.all()

@router.post("/targets", response_model=TargetResponse)
def create_target(
    payload: TargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN, Role.SUSTAINABILITY_MANAGER]))
):
    org_id = payload.organization_id or current_user.organization_id
    tgt = Target(**payload.model_dump(), organization_id=org_id, created_by=current_user.id)
    db.add(tgt)
    db.commit()
    db.refresh(tgt)
    return tgt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db import get_db
from app.core.rbac import get_current_user, require_roles, Role, EDIT_ROLES
from app.models.auth import User
from app.models.carbon import EmissionRecord, ActivityData
from app.models.organization import Facility
from app.models.analytics import Scenario, ReductionInitiative, AnomalyRecord
from app.schemas.analytics import (
    ScenarioCreate,
    ScenarioResponse,
    ScenarioSimulateRequest,
    ReductionInitiativeCreate,
    ReductionInitiativeResponse,
    AnomalyResolveRequest
)
from app.services.analytics_service import (
    calculate_pareto_analysis,
    project_scenario_reduction,
    detect_anomalies
)

router = APIRouter(prefix="/analytics", tags=["AI Analytics & Reduction Planning"])

@router.get("/pareto")
def get_hotspot_pareto(
    scope: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hotspot Pareto chart data: ranks emissions by category descending with cumulative % curve."""
    q = db.query(
        EmissionRecord.category,
        EmissionRecord.scope,
        func.sum(EmissionRecord.gross_emissions_tco2e).label("total_emissions")
    ).filter(
        EmissionRecord.is_scenario == False,
        EmissionRecord.is_deleted == False
    )
    if scope:
        q = q.filter(EmissionRecord.scope == scope)

    results = q.group_by(EmissionRecord.category, EmissionRecord.scope).all()

    sources = [
        {"name": r.category, "scope": r.scope, "emissions_tco2e": float(r.total_emissions or 0.0)}
        for r in results
    ]

    return calculate_pareto_analysis(sources)

@router.post("/scenarios/simulate")
def simulate_scenario(
    payload: ScenarioSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """What-if scenario builder: select reduction levers, enter % reduction, see projected impact.
    Strictly isolated: does not alter actuals.
    """
    # Fetch actual approved totals by scope
    scope_totals = {1: 0.0, 2: 0.0, 3: 0.0}
    actuals = db.query(
        EmissionRecord.scope,
        func.sum(EmissionRecord.gross_emissions_tco2e).label("total")
    ).filter(
        EmissionRecord.is_scenario == False,
        EmissionRecord.is_deleted == False
    ).group_by(EmissionRecord.scope).all()

    for row in actuals:
        if row.scope in scope_totals:
            scope_totals[row.scope] = float(row.total or 0.0)

    sim = project_scenario_reduction(
        actual_emissions_by_scope=scope_totals,
        levers=[l.model_dump() for l in payload.levers]
    )
    return sim

@router.get("/scenarios", response_model=List[ScenarioResponse])
def list_scenarios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Scenario).filter(Scenario.is_deleted == False).all()

@router.post("/scenarios", response_model=ScenarioResponse)
def create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    # Calculate projection
    scope_totals = {1: 0.0, 2: 0.0, 3: 0.0}
    actuals = db.query(
        EmissionRecord.scope,
        func.sum(EmissionRecord.gross_emissions_tco2e).label("total")
    ).filter(
        EmissionRecord.is_scenario == False,
        EmissionRecord.is_deleted == False
    ).group_by(EmissionRecord.scope).all()

    for row in actuals:
        if row.scope in scope_totals:
            scope_totals[row.scope] = float(row.total or 0.0)

    sim = project_scenario_reduction(
        actual_emissions_by_scope=scope_totals,
        levers=[l.model_dump() for l in payload.levers]
    )

    scenario = Scenario(
        organization_id=payload.organization_id,
        name=payload.name,
        description=payload.description,
        baseline_year=payload.baseline_year,
        target_year=payload.target_year,
        levers=[l.model_dump() for l in payload.levers],
        projected_reduction_tco2e=sim["total_reduction_tco2e"],
        projected_reduction_pct=sim["overall_reduction_pct"],
        created_by=current_user.id
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario

@router.get("/initiatives", response_model=List[ReductionInitiativeResponse])
def list_initiatives(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ReductionInitiative).filter(ReductionInitiative.is_deleted == False).all()

@router.post("/initiatives", response_model=ReductionInitiativeResponse)
def create_initiative(
    payload: ReductionInitiativeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    init = ReductionInitiative(**payload.model_dump(), created_by=current_user.id)
    db.add(init)
    db.commit()
    db.refresh(init)
    return init

@router.get("/anomalies")
def list_anomalies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    anomalies = db.query(AnomalyRecord).filter(AnomalyRecord.is_deleted == False).all()
    if not anomalies:
        # Check active activities dynamically
        activities = db.query(ActivityData).filter(ActivityData.is_deleted == False).all()
        fac_map = {f.id: f.name for f in db.query(Facility).all()}
        
        recs = []
        for a in activities:
            recs.append({
                "id": a.id,
                "facility_id": a.facility_id,
                "facility_name": fac_map.get(a.facility_id, "Facility"),
                "activity_type": a.activity_type,
                "quantity": a.quantity,
                "reporting_period": a.reporting_period
            })
        detected = detect_anomalies(recs)
        for d in detected:
            rec = AnomalyRecord(
                organization_id=current_user.organization_id or "default-org",
                activity_data_id=d["activity_id"],
                facility_name=d["facility_name"],
                metric_name=d["activity_type"],
                actual_value=d["actual_value"],
                expected_value=d["expected_mean"],
                deviation_pct=d["deviation_pct"],
                status="flagged",
                created_by=current_user.id
            )
            db.add(rec)
        db.commit()
        anomalies = db.query(AnomalyRecord).filter(AnomalyRecord.is_deleted == False).all()

    return anomalies

@router.put("/anomalies/{id}/resolve")
def resolve_anomaly(
    id: str,
    payload: AnomalyResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    rec = db.query(AnomalyRecord).filter(AnomalyRecord.id == id, AnomalyRecord.is_deleted == False).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Anomaly record not found")
    rec.status = payload.status
    db.commit()
    return {"id": rec.id, "status": rec.status}

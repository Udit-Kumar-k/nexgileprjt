from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, date

from app.db import get_db
from app.core.rbac import get_current_user, require_roles, Role, EDIT_ROLES
from app.models.auth import User
from app.models.supplier import (
    Supplier,
    Questionnaire,
    QuestionnaireSubmission,
    Scorecard,
    ActionPlan
)
from app.schemas.supplier import (
    SupplierCreate,
    SupplierResponse,
    SupplierInviteRequest,
    QuestionnaireCreate,
    QuestionnaireResponse,
    SubmissionCreate,
    ScorecardCreate,
    ScorecardResponse,
    ActionPlanCreate,
    ActionPlanResponse
)

router = APIRouter(prefix="/supplier", tags=["Supplier Engagement & Scope 3"])

# ==============================================================================
# Suppliers Directory & Onboarding
# ==============================================================================

@router.get("/suppliers")
def list_suppliers(
    category: Optional[str] = None,
    country: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Supplier).filter(Supplier.is_deleted == False)
    if category:
        q = q.filter(Supplier.category == category)
    if country:
        q = q.filter(Supplier.country == country)
    if tier:
        q = q.filter(Supplier.tier == tier)
    if search:
        q = q.filter(Supplier.name.ilike(f"%{search}%"))

    suppliers = q.all()
    results = []
    for s in suppliers:
        scorecard = db.query(Scorecard).filter(
            Scorecard.supplier_id == s.id,
            Scorecard.is_deleted == False
        ).order_by(Scorecard.reporting_year.desc()).first()

        action_count = db.query(ActionPlan).filter(
            ActionPlan.supplier_id == s.id,
            ActionPlan.is_deleted == False
        ).count()

        results.append({
            "id": s.id,
            "organization_id": s.organization_id,
            "name": s.name,
            "code": s.code,
            "contact_name": s.contact_name,
            "contact_email": s.contact_email,
            "tier": s.tier,
            "country": s.country,
            "category": s.category,
            "onboarding_status": s.onboarding_status,
            "spend_usd": s.spend_usd,
            "scorecard": {
                "maturity_score": scorecard.maturity_score if scorecard else None,
                "rating": scorecard.rating if scorecard else "N/A",
                "emissions_scope1_2_tco2e": scorecard.emissions_scope1_2_tco2e if scorecard else None,
                "yoy_change_pct": scorecard.yoy_change_pct if scorecard else None,
                "sbti_committed": scorecard.sbti_committed if scorecard else False,
                "renewable_energy_pct": scorecard.renewable_energy_pct if scorecard else 0.0
            } if scorecard else None,
            "action_plans_count": action_count,
            "created_at": s.created_at
        })

    # Sort descending by spend or maturity
    return results

@router.post("/invite")
def invite_supplier(
    payload: SupplierInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    """Simulate supplier onboarding invitation with progress tracking."""
    code = f"SUP-{payload.supplier_name[:3].upper()}-{int(datetime.now().timestamp()) % 10000}"
    supplier = Supplier(
        organization_id=current_user.organization_id or "default-org",
        name=payload.supplier_name,
        code=code,
        contact_email=payload.email,
        tier=payload.tier,
        country=payload.country,
        category=payload.category,
        onboarding_status="invited",
        created_by=current_user.id
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    print(f"[INVITE LOG] Invitation dispatched to {payload.email} for supplier {payload.supplier_name} (Code: {code})")
    return {
        "status": "invited",
        "supplier_id": supplier.id,
        "email": payload.email,
        "invitation_link": f"/supplier-portal/{supplier.id}"
    }

# ==============================================================================
# Questionnaires & Submissions
# ==============================================================================

@router.get("/questionnaires", response_model=List[QuestionnaireResponse])
def list_questionnaires(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Questionnaire).filter(Questionnaire.is_deleted == False).all()

@router.post("/questionnaires", response_model=QuestionnaireResponse)
def create_questionnaire(
    payload: QuestionnaireCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    q = Questionnaire(**payload.model_dump(), created_by=current_user.id)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

@router.post("/submissions")
def submit_questionnaire(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = QuestionnaireSubmission(
        questionnaire_id=payload.questionnaire_id,
        supplier_id=payload.supplier_id,
        responses=payload.responses,
        status=payload.status,
        submitted_at=datetime.now(timezone.utc),
        attestation_name=payload.attestation_name,
        attestation_date=date.today(),
        created_by=current_user.id
    )
    db.add(sub)
    
    # Update supplier status
    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if supplier:
        supplier.onboarding_status = "submitted"
    
    db.commit()
    return {"status": "success", "submission_id": sub.id}

# ==============================================================================
# Scorecards & Action Plans
# ==============================================================================

@router.get("/scorecards", response_model=List[ScorecardResponse])
def list_scorecards(supplier_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Scorecard).filter(Scorecard.is_deleted == False)
    if supplier_id:
        q = q.filter(Scorecard.supplier_id == supplier_id)
    return q.order_by(Scorecard.maturity_score.desc()).all()

@router.post("/scorecards", response_model=ScorecardResponse)
def create_scorecard(
    payload: ScorecardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    sc = Scorecard(**payload.model_dump(), created_by=current_user.id)
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc

@router.get("/action-plans", response_model=List[ActionPlanResponse])
def list_action_plans(supplier_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(ActionPlan).filter(ActionPlan.is_deleted == False)
    if supplier_id:
        q = q.filter(ActionPlan.supplier_id == supplier_id)
    return q.all()

@router.post("/action-plans", response_model=ActionPlanResponse)
def create_action_plan(
    payload: ActionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    ap = ActionPlan(**payload.model_dump(), created_by=current_user.id)
    db.add(ap)
    db.commit()
    db.refresh(ap)
    return ap

@router.put("/action-plans/{id}/status")
def update_action_plan_status(
    id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    ap = db.query(ActionPlan).filter(ActionPlan.id == id, ActionPlan.is_deleted == False).first()
    if not ap:
        raise HTTPException(status_code=404, detail="Action plan not found")
    ap.status = status
    db.commit()
    return {"id": ap.id, "status": ap.status}

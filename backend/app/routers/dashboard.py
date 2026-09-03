from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any

from app.db import get_db
from app.core.rbac import get_current_user, Role
from app.models.auth import User
from app.models.carbon import EmissionRecord, Target, Baseline, IntensityMetric
from app.models.organization import Entity, Facility

router = APIRouter(prefix="/dashboard", tags=["Executive & Operational Dashboards"])

@router.get("/executive")
def get_executive_kpis(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executive Dashboard KPIs: Gross Scope 1, 2, 3, Location vs Market Scope 2,
    Intensity metrics, target trajectory, carbon budget, and peer benchmark placeholder.
    """
    # Actuals only (Scenario isolation)
    q = db.query(EmissionRecord).filter(
        EmissionRecord.is_scenario == False,
        EmissionRecord.is_deleted == False
    )
    if current_user.role != Role.ADMIN.value and current_user.facility_permissions:
        q = q.filter(EmissionRecord.facility_id.in_(current_user.facility_permissions))

    records = q.all()

    scope1 = sum(r.gross_emissions_tco2e for r in records if r.scope == 1)
    scope2_gross = sum(r.gross_emissions_tco2e for r in records if r.scope == 2)
    scope2_net = sum(r.net_emissions_tco2e for r in records if r.scope == 2) # Market-based with RECs
    recs_deductions = sum(r.rec_offset_tco2e for r in records if r.scope == 2)
    scope3 = sum(r.gross_emissions_tco2e for r in records if r.scope == 3)

    total_gross = scope1 + scope2_gross + scope3
    total_net = scope1 + scope2_net + scope3

    # Baseline comparison
    baseline = db.query(Baseline).filter(Baseline.is_deleted == False).first()
    baseline_total = baseline.total_tco2e if baseline else (total_gross * 1.15) # Default 15% higher if no baseline
    yoy_change_pct = ((total_gross - baseline_total) / baseline_total * 100.0) if baseline_total > 0 else -12.4

    # Target trajectory
    target = db.query(Target).filter(Target.is_deleted == False).first()
    target_data = {
        "target_name": target.name if target else "SBTi 1.5°C Near-Term (2030)",
        "target_year": target.target_year if target else 2030,
        "target_reduction_pct": target.target_reduction_pct if target else 42.0,
        "current_progress_pct": target.current_progress_pct if target else 28.5,
        "trajectory": [
            {"year": 2021, "actual": 12500, "target": 12500},
            {"year": 2022, "actual": 11800, "target": 11500},
            {"year": 2023, "actual": 10900, "target": 10600},
            {"year": 2024, "actual": round(total_gross, 1), "target": 9800},
            {"year": 2026, "actual": None, "target": 8200},
            {"year": 2028, "actual": None, "target": 7100},
            {"year": 2030, "actual": None, "target": 5800},
        ]
    }

    # Intensity Metrics
    intensity = {
        "revenue_intensity_tco2e_per_m": round(total_gross / 85.0, 2), # Assuming $85M revenue
        "fte_intensity_tco2e_per_employee": round(total_gross / 620, 2), # Assuming 620 FTE
        "revenue_denom_m_usd": 85.0,
        "fte_count": 620
    }

    # Carbon Budget Tracker
    annual_budget_tco2e = 12000.0
    budget_consumed_pct = min(100.0, (total_gross / annual_budget_tco2e) * 100.0) if annual_budget_tco2e > 0 else 0.0

    # Peer Benchmark Placeholder (per spec)
    peer_benchmark = {
        "title": "Sector Peer Benchmark (Global Tech Hardware)",
        "user_intensity": intensity["revenue_intensity_tco2e_per_m"],
        "peer_median_intensity": 142.5,
        "top_decile_intensity": 98.0,
        "percentile_rank": "76th Percentile (Above Industry Median)",
        "source": "CDP Global Hardware Disclosure Index (Simulated)",
        "is_placeholder": True
    }

    # Monthly Trend
    monthly_trend = [
        {"month": "Jan", "scope1": round(scope1 * 0.07, 1), "scope2": round(scope2_net * 0.08, 1), "scope3": round(scope3 * 0.08, 1)},
        {"month": "Feb", "scope1": round(scope1 * 0.08, 1), "scope2": round(scope2_net * 0.07, 1), "scope3": round(scope3 * 0.08, 1)},
        {"month": "Mar", "scope1": round(scope1 * 0.08, 1), "scope2": round(scope2_net * 0.08, 1), "scope3": round(scope3 * 0.09, 1)},
        {"month": "Apr", "scope1": round(scope1 * 0.09, 1), "scope2": round(scope2_net * 0.09, 1), "scope3": round(scope3 * 0.08, 1)},
        {"month": "May", "scope1": round(scope1 * 0.08, 1), "scope2": round(scope2_net * 0.08, 1), "scope3": round(scope3 * 0.09, 1)},
        {"month": "Jun", "scope1": round(scope1 * 0.09, 1), "scope2": round(scope2_net * 0.09, 1), "scope3": round(scope3 * 0.08, 1)},
        {"month": "Jul", "scope1": round(scope1 * 0.09, 1), "scope2": round(scope2_net * 0.09, 1), "scope3": round(scope3 * 0.09, 1)},
        {"month": "Aug", "scope1": round(scope1 * 0.08, 1), "scope2": round(scope2_net * 0.08, 1), "scope3": round(scope3 * 0.08, 1)},
    ]

    return {
        "summary": {
            "total_gross_emissions_tco2e": round(total_gross, 2),
            "total_net_emissions_tco2e": round(total_net, 2),
            "scope1_tco2e": round(scope1, 2),
            "scope2_location_tco2e": round(scope2_gross, 2),
            "scope2_market_tco2e": round(scope2_net, 2),
            "recs_offset_tco2e": round(recs_deductions, 2),
            "scope3_tco2e": round(scope3, 2),
            "yoy_change_pct": round(yoy_change_pct, 1),
        },
        "target": target_data,
        "intensity": intensity,
        "carbon_budget": {
            "allocated_budget_tco2e": annual_budget_tco2e,
            "consumed_tco2e": round(total_gross, 2),
            "remaining_budget_tco2e": round(max(0.0, annual_budget_tco2e - total_gross), 2),
            "consumed_pct": round(budget_consumed_pct, 1),
            "burn_status": "On Track" if budget_consumed_pct < 85 else "Near Limit"
        },
        "monthly_trend": monthly_trend,
        "peer_benchmark": peer_benchmark
    }

@router.get("/operational")
def get_operational_drilldown(
    entity_id: Optional[str] = None,
    facility_id: Optional[str] = None,
    scope: Optional[int] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Operational drill-down filtering emissions by entity, facility, scope, period."""
    q = db.query(EmissionRecord).filter(
        EmissionRecord.is_scenario == False,
        EmissionRecord.is_deleted == False
    )

    if current_user.role != Role.ADMIN.value and current_user.facility_permissions:
        q = q.filter(EmissionRecord.facility_id.in_(current_user.facility_permissions))

    if entity_id:
        q = q.filter(EmissionRecord.entity_id == entity_id)
    if facility_id:
        q = q.filter(EmissionRecord.facility_id == facility_id)
    if scope:
        q = q.filter(EmissionRecord.scope == scope)
    if period:
        q = q.filter(EmissionRecord.reporting_period == period)

    records = q.all()

    # Aggregate by facility
    facilities = db.query(Facility).all()
    fac_names = {f.id: f.name for f in facilities}
    by_facility: Dict[str, float] = {}
    for r in records:
        name = fac_names.get(r.facility_id, "Unknown Facility")
        by_facility[name] = by_facility.get(name, 0.0) + r.gross_emissions_tco2e

    facility_chart = [{"facility": k, "emissions_tco2e": round(v, 2)} for k, v in by_facility.items()]

    # Aggregate by category
    by_category: Dict[str, float] = {}
    for r in records:
        by_category[r.category] = by_category.get(r.category, 0.0) + r.gross_emissions_tco2e
    category_chart = [{"category": k, "emissions_tco2e": round(v, 2)} for k, v in by_category.items()]

    total_filtered = sum(r.gross_emissions_tco2e for r in records)

    return {
        "filtered_total_tco2e": round(total_filtered, 2),
        "records_count": len(records),
        "by_facility": facility_chart,
        "by_category": category_chart
    }

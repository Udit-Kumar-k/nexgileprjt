from sqlalchemy import Column, String, Float, Integer, Text, Boolean, JSON, DateTime
from app.db import Base
from app.models.base import AuditBaseMixin, utc_now

class Scenario(Base, AuditBaseMixin):
    """What-if scenario modeling strictly isolated from actuals."""
    __tablename__ = "scenarios"

    organization_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    baseline_year = Column(Integer, default=2023, nullable=False)
    target_year = Column(Integer, default=2030, nullable=False)
    
    # Selected levers e.g. [{"lever": "100% On-site Solar", "target_pct": 50, "scope": 2}]
    levers = Column(JSON, nullable=False)
    
    projected_reduction_tco2e = Column(Float, default=0.0, nullable=False)
    projected_reduction_pct = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class ReductionInitiative(Base, AuditBaseMixin):
    __tablename__ = "reduction_initiatives"

    organization_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    lever_type = Column(String(100), nullable=False) 
    # Energy Efficiency, Renewable Electricity, Fleet Electrification, Low-Carbon Materials, Heat Pumps
    target_reduction_tco2e = Column(Float, nullable=False)
    actual_reduction_tco2e = Column(Float, default=0.0, nullable=False)
    capex_usd = Column(Float, default=0.0, nullable=False)
    opex_annual_usd = Column(Float, default=0.0, nullable=False)
    payback_years = Column(Float, default=0.0, nullable=False)
    status = Column(String(30), default="active", nullable=False) # planned, active, completed, on_hold

class AnomalyRecord(Base, AuditBaseMixin):
    __tablename__ = "anomaly_records"

    organization_id = Column(String(36), nullable=False, index=True)
    activity_data_id = Column(String(36), nullable=False, index=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    facility_name = Column(String(255), nullable=False)
    metric_name = Column(String(100), nullable=False)
    actual_value = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=False) # 3-month rolling average
    deviation_pct = Column(Float, nullable=False)
    rule_triggered = Column(String(255), default="3-month rolling average outlier (>30% variance)", nullable=False)
    status = Column(String(30), default="flagged", nullable=False) # flagged, reviewed, resolved, dismissed

from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, Boolean, JSON, Date, DateTime
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import AuditBaseMixin, utc_now

class Supplier(Base, AuditBaseMixin):
    __tablename__ = "suppliers"

    organization_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=False)
    tier = Column(String(20), default="Tier 1", nullable=False) # Tier 1, Tier 2, Tier 3
    country = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False) # Raw Materials, Packaging, Electronics, Logistics, Services
    onboarding_status = Column(String(30), default="invited", nullable=False) # invited, in_progress, submitted, verified
    spend_usd = Column(Float, default=0.0, nullable=False)

    submissions = relationship("QuestionnaireSubmission", back_populates="supplier", cascade="all, delete-orphan")
    scorecards = relationship("Scorecard", back_populates="supplier", cascade="all, delete-orphan")
    action_plans = relationship("ActionPlan", back_populates="supplier", cascade="all, delete-orphan")

class Questionnaire(Base, AuditBaseMixin):
    __tablename__ = "questionnaires"

    organization_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    materiality_category = Column(String(100), default="Manufacturing & Energy", nullable=False)
    questions = Column(JSON, nullable=False) 
    # [{"id": "q1", "text": "Do you measure Scope 1 & 2 emissions?", "type": "boolean", "materiality": "high"}]
    is_active = Column(Boolean, default=True, nullable=False)

    submissions = relationship("QuestionnaireSubmission", back_populates="questionnaire", cascade="all, delete-orphan")

class QuestionnaireSubmission(Base, AuditBaseMixin):
    __tablename__ = "questionnaire_submissions"

    questionnaire_id = Column(String(36), ForeignKey("questionnaires.id"), nullable=False, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    responses = Column(JSON, nullable=False)
    status = Column(String(30), default="draft", nullable=False) # draft, submitted, under_review, approved
    submitted_at = Column(DateTime, nullable=True)
    attestation_name = Column(String(255), nullable=True)
    attestation_date = Column(Date, nullable=True)

    questionnaire = relationship("Questionnaire", back_populates="submissions")
    supplier = relationship("Supplier", back_populates="submissions")

class Scorecard(Base, AuditBaseMixin):
    __tablename__ = "scorecards"

    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    reporting_year = Column(Integer, nullable=False)
    emissions_scope1_2_tco2e = Column(Float, nullable=False)
    emissions_intensity = Column(Float, nullable=True) # tCO2e / $100k spend
    maturity_score = Column(Float, nullable=False) # 0 to 100
    rating = Column(String(5), default="B", nullable=False) # A, B, C, D
    yoy_change_pct = Column(Float, default=0.0, nullable=False) # e.g. -4.5% reduction
    cdp_score = Column(String(10), nullable=True) # A, A-, B, B-, C, D
    sbti_committed = Column(Boolean, default=False, nullable=False)
    renewable_energy_pct = Column(Float, default=0.0, nullable=False)

    supplier = relationship("Supplier", back_populates="scorecards")

class ActionPlan(Base, AuditBaseMixin):
    __tablename__ = "action_plans"

    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    initiative_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_reduction_tco2e = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), default="in_progress", nullable=False) # planned, in_progress, completed, delayed
    assigned_to = Column(String(255), nullable=True)

    supplier = relationship("Supplier", back_populates="action_plans")

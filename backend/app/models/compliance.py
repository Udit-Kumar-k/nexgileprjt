from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import AuditBaseMixin, utc_now

class Framework(Base, AuditBaseMixin):
    __tablename__ = "frameworks"

    name = Column(String(100), nullable=False) # CSRD, CBAM, TCFD, EU Taxonomy, SEC Climate, CDP
    code = Column(String(50), unique=True, nullable=False, index=True)
    version = Column(String(50), default="2024", nullable=False)
    description = Column(Text, nullable=True)
    jurisdiction = Column(String(100), default="EU / Global", nullable=False)

    data_points = relationship("DataPoint", back_populates="framework", cascade="all, delete-orphan")
    disclosures = relationship("Disclosure", back_populates="framework", cascade="all, delete-orphan")

class Disclosure(Base, AuditBaseMixin):
    __tablename__ = "disclosures"

    organization_id = Column(String(36), nullable=False, index=True)
    framework_id = Column(String(36), ForeignKey("frameworks.id"), nullable=False, index=True)
    reporting_year = Column(Integer, nullable=False)
    status = Column(String(30), default="draft", nullable=False) # draft, in_review, approved, submitted
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    framework = relationship("Framework", back_populates="disclosures")

class DataPoint(Base, AuditBaseMixin):
    __tablename__ = "data_points"

    framework_id = Column(String(36), ForeignKey("frameworks.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True) # e.g. E1-6, CC2.1, CBAM-01
    name = Column(String(255), nullable=False)
    requirement_text = Column(Text, nullable=False)
    reported_value = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    status = Column(String(30), default="draft", nullable=False) # draft, in_review, verified, submitted
    calculation_link = Column(String(255), nullable=True) # e.g. "Scope 1 Stationary Combustion Total"
    evidence_url = Column(String(255), nullable=True)

    framework = relationship("Framework", back_populates="data_points")

class Evidence(Base, AuditBaseMixin):
    __tablename__ = "evidence"

    organization_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_kb = Column(Float, default=120.0, nullable=False)
    content_type = Column(String(100), default="application/pdf", nullable=False)
    file_url = Column(String(500), nullable=False)
    verification_status = Column(String(30), default="verified", nullable=False) # unverified, pending, verified
    linked_data_points = Column(JSON, default=list, nullable=False)

class AssuranceRequest(Base, AuditBaseMixin):
    __tablename__ = "assurance_requests"

    organization_id = Column(String(36), nullable=False, index=True)
    framework_id = Column(String(36), ForeignKey("frameworks.id"), nullable=False)
    reporting_year = Column(Integer, nullable=False)
    auditor_firm = Column(String(255), nullable=False) # e.g. PwC, EY, KPMG, Deloitte
    auditor_name = Column(String(255), nullable=False)
    assurance_type = Column(String(50), default="Limited Assurance", nullable=False) # Limited Assurance, Reasonable Assurance
    status = Column(String(30), default="in_review", nullable=False) # requested, in_review, approved, rejected
    requested_at = Column(DateTime, default=utc_now, nullable=False)
    signoff_at = Column(DateTime, nullable=True)

class CreditOffset(Base, AuditBaseMixin):
    __tablename__ = "credit_offsets"

    organization_id = Column(String(36), nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    project_type = Column(String(100), nullable=False) # Reforestation, Direct Air Capture, Cookstoves, Renewable
    registry = Column(String(50), default="Verra (VCS)", nullable=False) # Verra, Gold Standard, American Carbon Registry
    vintage_year = Column(Integer, nullable=False)
    quantity_tco2e = Column(Float, nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    retirement_status = Column(String(30), default="retired", nullable=False) # active, reserved, retired
    retirement_beneficiary = Column(String(255), nullable=True)

class CBAMRecord(Base, AuditBaseMixin):
    __tablename__ = "cbam_records"

    organization_id = Column(String(36), nullable=False, index=True)
    product_code = Column(String(50), nullable=False, index=True) # CN code, e.g. 7208 (Flat-rolled iron/steel)
    product_description = Column(String(255), nullable=False)
    country_of_origin = Column(String(100), nullable=False)
    reporting_quarter = Column(String(20), nullable=False) # e.g. 2024-Q1
    imported_volume_tonnes = Column(Float, nullable=False)
    direct_embedded_emissions = Column(Float, nullable=False) # tCO2e / tonne
    indirect_embedded_emissions = Column(Float, nullable=False) # tCO2e / tonne
    total_embedded_emissions_tco2e = Column(Float, nullable=False)
    carbon_price_due_eur = Column(Float, default=0.0, nullable=False)

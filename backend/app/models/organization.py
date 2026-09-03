from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import AuditBaseMixin

class Organization(Base, AuditBaseMixin):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    sector = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    reporting_currency = Column(String(10), default="USD", nullable=False)
    
    entities = relationship("Entity", back_populates="organization", cascade="all, delete-orphan")

class Entity(Base, AuditBaseMixin):
    __tablename__ = "entities"

    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    country = Column(String(100), nullable=False)
    consolidation_method = Column(String(50), default="Operational Control", nullable=False)
    # Operational Control, Financial Control, Equity Share
    ownership_percentage = Column(Float, default=100.0, nullable=False)

    organization = relationship("Organization", back_populates="entities")
    facilities = relationship("Facility", back_populates="entity", cascade="all, delete-orphan")
    boundaries = relationship("ReportingBoundary", back_populates="entity", cascade="all, delete-orphan")

class Facility(Base, AuditBaseMixin):
    __tablename__ = "facilities"

    entity_id = Column(String(36), ForeignKey("entities.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    facility_type = Column(String(50), default="Manufacturing", nullable=False)
    # Manufacturing, Office, Warehouse, Data Center, R&D
    address = Column(String(255), nullable=True)
    country = Column(String(100), nullable=False)
    grid_region = Column(String(100), nullable=True) # e.g. US-CAMX, US-RFCW, EU-CENTRAL

    entity = relationship("Entity", back_populates="facilities")
    departments = relationship("Department", back_populates="facility", cascade="all, delete-orphan")

class Department(Base, AuditBaseMixin):
    __tablename__ = "departments"

    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)

    facility = relationship("Facility", back_populates="departments")
    cost_centers = relationship("CostCenter", back_populates="department", cascade="all, delete-orphan")

class CostCenter(Base, AuditBaseMixin):
    __tablename__ = "cost_centers"

    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    budget_currency = Column(String(10), default="USD", nullable=False)

    department = relationship("Department", back_populates="cost_centers")

class ReportingBoundary(Base, AuditBaseMixin):
    __tablename__ = "reporting_boundaries"

    entity_id = Column(String(36), ForeignKey("entities.id"), nullable=False, index=True)
    reporting_year = Column(Integer, nullable=False)
    boundary_type = Column(String(50), default="Operational Control", nullable=False)
    consolidation_approach = Column(String(100), default="100% Operational Control", nullable=False)
    is_active = Column(String(20), default="Active", nullable=False)
    notes = Column(Text, nullable=True)

    entity = relationship("Entity", back_populates="boundaries")

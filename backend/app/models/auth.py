from sqlalchemy import Column, String, Boolean, JSON, ForeignKey
from app.db import Base
from app.models.base import AuditBaseMixin

class User(Base, AuditBaseMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="ESG Analyst") 
    # Roles: Admin, Sustainability Manager, ESG Analyst, Auditor, Supplier, C-Suite
    
    organization_id = Column(String(36), nullable=True) # Scoped organization
    facility_permissions = Column(JSON, default=list, nullable=False) # List of permitted facility IDs
    is_active = Column(Boolean, default=True, nullable=False)

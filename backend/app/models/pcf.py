from sqlalchemy import Column, String, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import AuditBaseMixin

class Product(Base, AuditBaseMixin):
    __tablename__ = "products"

    organization_id = Column(String(36), nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    functional_unit = Column(String(100), default="1 Unit", nullable=False) # e.g. "1 Unit", "1 kg", "1 Server"
    unit_weight_kg = Column(Float, default=1.0, nullable=False)
    
    boms = relationship("BOM", back_populates="product", cascade="all, delete-orphan")
    processes = relationship("Process", back_populates="product", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="product", cascade="all, delete-orphan")
    packagings = relationship("Packaging", back_populates="product", cascade="all, delete-orphan")
    pcf_records = relationship("PCFRecord", back_populates="product", cascade="all, delete-orphan")

class Material(Base, AuditBaseMixin):
    __tablename__ = "materials"

    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False) # Metals, Polymers, Electronics, Chemicals, Glass
    default_emission_factor_id = Column(String(36), nullable=True)
    recycled_content_pct = Column(Float, default=0.0, nullable=False)
    density_kg_m3 = Column(Float, nullable=True)

class BOM(Base, AuditBaseMixin):
    """Bill of Materials - Multi-level Component Mapping."""
    __tablename__ = "boms"

    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    component_name = Column(String(255), nullable=False)
    material_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), default="kg", nullable=False)
    scrap_rate_pct = Column(Float, default=2.0, nullable=False)
    supplier_id = Column(String(36), nullable=True)
    parent_component_id = Column(String(36), nullable=True) # Enables multi-level BOM nesting

    product = relationship("Product", back_populates="boms")

class Process(Base, AuditBaseMixin):
    """Process Modeling for manufacturing & production energy/scrap."""
    __tablename__ = "processes"

    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    stage = Column(String(50), default="Manufacturing", nullable=False) 
    # Raw Material Acquisition, Manufacturing, Distribution, Use Phase, End of Life
    process_name = Column(String(255), nullable=False)
    electricity_kwh = Column(Float, default=0.0, nullable=False)
    thermal_energy_mj = Column(Float, default=0.0, nullable=False)
    direct_emissions_kgco2e = Column(Float, default=0.0, nullable=False)
    scrap_loss_pct = Column(Float, default=0.0, nullable=False)

    product = relationship("Product", back_populates="processes")

class Route(Base, AuditBaseMixin):
    """Multimodal Logistics Route Modeling."""
    __tablename__ = "routes"

    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    origin = Column(String(150), nullable=False)
    destination = Column(String(150), nullable=False)
    distance_km = Column(Float, nullable=False)
    transport_mode = Column(String(50), default="Road Freight", nullable=False) # Road Freight, Ocean Cargo, Air Freight, Rail

    product = relationship("Product", back_populates="routes")

class Packaging(Base, AuditBaseMixin):
    __tablename__ = "packagings"

    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    packaging_type = Column(String(100), nullable=False) # Corrugated Box, Polybag, Pallet, Molded Pulp
    material_type = Column(String(100), nullable=False)
    weight_kg = Column(Float, nullable=False)
    recyclability_pct = Column(Float, default=100.0, nullable=False)

    product = relationship("Product", back_populates="packagings")

class PCFRecord(Base, AuditBaseMixin):
    """Product Carbon Footprint calculation record aligned with ISO 14067."""
    __tablename__ = "pcf_records"

    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    boundary = Column(String(50), default="cradle-to-gate", nullable=False) 
    # cradle-to-gate, gate-to-gate, cradle-to-grave
    functional_unit = Column(String(100), nullable=False)
    allocation_method = Column(String(50), default="Mass Allocation", nullable=False)
    
    total_pcf_kgco2e = Column(Float, nullable=False)
    stage_breakdown = Column(JSON, nullable=False) 
    # {"raw_materials": 12.4, "manufacturing": 4.2, "packaging": 0.8, "logistics": 2.1, "use_phase": 0.0, "end_of_life": 0.5}
    
    iso_14067_compliant = Column(Boolean, default=True, nullable=False)
    calculation_details = Column(JSON, nullable=True)

    product = relationship("Product", back_populates="pcf_records")

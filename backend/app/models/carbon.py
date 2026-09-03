from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, Boolean, Date, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import AuditBaseMixin, utc_now

class EmissionFactor(Base, AuditBaseMixin):
    __tablename__ = "emission_factors"

    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True) # Fuels, Electricity, Freight, Materials, Travel
    gas_type = Column(String(50), default="CO2e", nullable=False) # CO2, CH4, N2O, CO2e
    factor_value = Column(Float, nullable=False) # e.g. 0.000385 (tCO2e per kWh)
    unit_numerator = Column(String(20), default="tCO2e", nullable=False)
    unit_denominator = Column(String(50), nullable=False) # kWh, Liters, Therms, kg, passenger-km, USD
    source = Column(String(100), default="EPA", nullable=False) # EPA, ecoinvent, DEFRA, IEA, Custom
    version = Column(String(20), default="2024.1", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    uncertainty_pct = Column(Float, default=5.0, nullable=False) # e.g. 5.0 -> +/- 5%
    description = Column(Text, nullable=True)

class ActivityData(Base, AuditBaseMixin):
    __tablename__ = "activity_data"

    organization_id = Column(String(36), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    facility_id = Column(String(36), nullable=False, index=True)
    
    scope = Column(Integer, nullable=False, index=True) # 1, 2, 3
    category = Column(String(100), nullable=False, index=True) # Stationary Combustion, Electricity, Business Travel, etc.
    activity_type = Column(String(100), nullable=False) # Natural Gas, Grid Electricity, Diesel Fleet, Air Travel
    
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False) # kWh, MWh, Therms, Liters, Gallons, Miles, km, USD
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reporting_period = Column(String(20), nullable=False) # e.g. 2024-Q1, 2024-01
    
    # Data Quality Rules (completeness, confidence, validation, anomaly)
    completeness_score = Column(Float, default=1.0, nullable=False) # 0.0 to 1.0
    confidence_tier = Column(String(20), default="high", nullable=False) # high, medium, low, estimated
    validation_status = Column(String(20), default="passed", nullable=False) # pending, passed, flagged, rejected
    anomaly_flag = Column(Boolean, default=False, nullable=False, index=True)
    
    source_document = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    calculations = relationship("Calculation", back_populates="activity_data", cascade="all, delete-orphan")
    emission_records = relationship("EmissionRecord", back_populates="activity_data", cascade="all, delete-orphan")

class MeterReading(Base, AuditBaseMixin):
    __tablename__ = "meter_readings"

    facility_id = Column(String(36), nullable=False, index=True)
    meter_identifier = Column(String(100), nullable=False)
    meter_type = Column(String(50), nullable=False) # Electricity, Natural Gas, Water, Steam
    reading_value = Column(Float, nullable=False)
    reading_unit = Column(String(50), nullable=False)
    reading_timestamp = Column(DateTime, default=utc_now, nullable=False)
    status = Column(String(20), default="verified", nullable=False)

class Calculation(Base, AuditBaseMixin):
    __tablename__ = "calculations"

    activity_data_id = Column(String(36), ForeignKey("activity_data.id"), nullable=False, index=True)
    factor_id = Column(String(36), ForeignKey("emission_factors.id"), nullable=False)
    factor_version = Column(String(20), nullable=False)
    
    formula_applied = Column(Text, nullable=False)
    unit_conversion_factor = Column(Float, default=1.0, nullable=False)
    allocation_pct = Column(Float, default=100.0, nullable=False)
    
    emissions_tco2e = Column(Float, nullable=False)
    uncertainty_min_tco2e = Column(Float, nullable=False)
    uncertainty_max_tco2e = Column(Float, nullable=False)
    
    calculated_at = Column(DateTime, default=utc_now, nullable=False)
    
    activity_data = relationship("ActivityData", back_populates="calculations")

class Allocation(Base, AuditBaseMixin):
    __tablename__ = "allocations"

    organization_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    allocation_method = Column(String(50), default="Floor Area", nullable=False) 
    # Floor Area, Headcount, Revenue, Production Output
    allocation_percentage = Column(Float, default=100.0, nullable=False)
    target_facility_id = Column(String(36), nullable=True)

class EmissionRecord(Base, AuditBaseMixin):
    """Audit-Grade Lineage Record.
    Every EmissionRecord stores source ActivityData ID, EmissionFactor ID+version,
    calculation formula string, unit conversions applied, allocation method, timestamp,
    approved_by user ID.
    Enforces Scenario Isolation with is_scenario flag.
    """
    __tablename__ = "emission_records"

    organization_id = Column(String(36), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    facility_id = Column(String(36), nullable=False, index=True)
    
    activity_data_id = Column(String(36), ForeignKey("activity_data.id"), nullable=False, index=True)
    emission_factor_id = Column(String(36), ForeignKey("emission_factors.id"), nullable=False)
    factor_version = Column(String(20), nullable=False)
    
    scope = Column(Integer, nullable=False, index=True) # 1, 2, 3
    category = Column(String(100), nullable=False, index=True)
    reporting_period = Column(String(20), nullable=False, index=True)
    
    # Emissions metrics
    gross_emissions_tco2e = Column(Float, nullable=False)
    net_emissions_tco2e = Column(Float, nullable=False)
    rec_offset_tco2e = Column(Float, default=0.0, nullable=False) # Deducted RECs or offsets
    
    # Audit Lineage (Strict functional rule)
    formula_string = Column(Text, nullable=False)
    unit_conversions_applied = Column(String(255), nullable=False) # e.g. "MWh -> kWh (*1000)"
    allocation_method = Column(String(100), default="100% Operational Control", nullable=False)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Scenario Isolation (Strict functional rule)
    is_scenario = Column(Boolean, default=False, nullable=False, index=True)
    scenario_id = Column(String(36), nullable=True, index=True)

    activity_data = relationship("ActivityData", back_populates="emission_records")

class IntensityMetric(Base, AuditBaseMixin):
    __tablename__ = "intensity_metrics"

    organization_id = Column(String(36), nullable=False, index=True)
    reporting_year = Column(Integer, nullable=False)
    revenue_m_usd = Column(Float, nullable=True)
    fte_employees = Column(Integer, nullable=True)
    production_volume_tons = Column(Float, nullable=True)
    
    scope1_2_intensity_rev = Column(Float, nullable=True) # tCO2e / $M
    total_intensity_fte = Column(Float, nullable=True) # tCO2e / FTE

class Baseline(Base, AuditBaseMixin):
    __tablename__ = "baselines"

    organization_id = Column(String(36), nullable=False, index=True)
    base_year = Column(Integer, nullable=False)
    scope1_tco2e = Column(Float, nullable=False)
    scope2_location_tco2e = Column(Float, nullable=False)
    scope2_market_tco2e = Column(Float, nullable=False)
    scope3_tco2e = Column(Float, nullable=False)
    total_tco2e = Column(Float, nullable=False)
    
    is_locked = Column(Boolean, default=True, nullable=False)
    restatement_reason = Column(Text, nullable=True)
    restated_at = Column(DateTime, nullable=True)

class Target(Base, AuditBaseMixin):
    __tablename__ = "targets"

    organization_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    target_type = Column(String(50), default="Absolute", nullable=False) # Absolute, Intensity
    scope_coverage = Column(String(50), default="Scope 1+2+3", nullable=False)
    baseline_year = Column(Integer, nullable=False)
    target_year = Column(Integer, nullable=False) # e.g. 2030, 2050
    target_reduction_pct = Column(Float, nullable=False) # e.g. 42.0 for SBTi 1.5C
    current_progress_pct = Column(Float, default=0.0, nullable=False)
    trajectory_json = Column(JSON, nullable=True) # Array of projected milestones

from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class BOMItem(BaseModel):
    component_name: str
    material_name: str
    quantity: float
    unit: str = "kg"
    scrap_rate_pct: float = 2.0
    supplier_id: Optional[str] = None

class ProcessItem(BaseModel):
    stage: str = "Manufacturing"
    process_name: str
    electricity_kwh: float = 0.0
    thermal_energy_mj: float = 0.0
    direct_emissions_kgco2e: float = 0.0

class RouteItem(BaseModel):
    origin: str
    destination: str
    distance_km: float
    transport_mode: str = "Road Freight"

class PackagingItem(BaseModel):
    packaging_type: str
    material_type: str
    weight_kg: float
    recyclability_pct: float = 100.0

class ProductBase(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    functional_unit: str = "1 Unit"
    unit_weight_kg: float = 1.0

class ProductCreate(ProductBase):
    organization_id: str
    boms: Optional[List[BOMItem]] = []
    processes: Optional[List[ProcessItem]] = []
    routes: Optional[List[RouteItem]] = []
    packagings: Optional[List[PackagingItem]] = []

class ProductResponse(ProductBase):
    id: str
    organization_id: str
    created_at: datetime
    class Config:
        from_attributes = True

class PCFCalculateRequest(BaseModel):
    product_id: str
    boundary: str = "cradle-to-gate"  # cradle-to-gate, gate-to-gate, cradle-to-grave
    allocation_method: str = "Mass Allocation"
    use_phase_kwh_per_year: float = 0.0
    lifespan_years: float = 1.0
    recycling_rate_pct: float = 85.0

class PCFCompareItem(BaseModel):
    product_id: str
    name: str
    sku: str
    total_pcf_kgco2e: float
    boundary: str
    stage_breakdown: Any

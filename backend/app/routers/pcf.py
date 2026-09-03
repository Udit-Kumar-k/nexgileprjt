from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.core.rbac import get_current_user, require_roles, Role, EDIT_ROLES
from app.models.auth import User
from app.models.pcf import (
    Product,
    BOM,
    Process,
    Route,
    Packaging,
    PCFRecord
)
from app.schemas.pcf import (
    ProductCreate,
    ProductResponse,
    PCFCalculateRequest,
    PCFCompareItem
)
from app.services.pcf_engine import calculate_pcf

router = APIRouter(prefix="/pcf", tags=["Product LCA & PCF"])

@router.get("/products")
def list_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Product).filter(Product.is_deleted == False)
    if category:
        q = q.filter(Product.category == category)
    products = q.all()
    
    result = []
    for p in products:
        latest_pcf = db.query(PCFRecord).filter(
            PCFRecord.product_id == p.id,
            PCFRecord.is_deleted == False
        ).order_by(PCFRecord.created_at.desc()).first()

        boms_count = db.query(BOM).filter(BOM.product_id == p.id, BOM.is_deleted == False).count()
        
        result.append({
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "category": p.category,
            "description": p.description,
            "functional_unit": p.functional_unit,
            "unit_weight_kg": p.unit_weight_kg,
            "boms_count": boms_count,
            "latest_pcf_kgco2e": latest_pcf.total_pcf_kgco2e if latest_pcf else None,
            "latest_boundary": latest_pcf.boundary if latest_pcf else None,
            "created_at": p.created_at
        })
    return result

@router.get("/products/{id}")
def get_product_details(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    boms = db.query(BOM).filter(BOM.product_id == id, BOM.is_deleted == False).all()
    processes = db.query(Process).filter(Process.product_id == id, Process.is_deleted == False).all()
    routes = db.query(Route).filter(Route.product_id == id, Route.is_deleted == False).all()
    packagings = db.query(Packaging).filter(Packaging.product_id == id, Packaging.is_deleted == False).all()
    pcf_records = db.query(PCFRecord).filter(PCFRecord.product_id == id, PCFRecord.is_deleted == False).all()

    return {
        "product": {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "functional_unit": product.functional_unit,
            "unit_weight_kg": product.unit_weight_kg,
        },
        "boms": [{"id": b.id, "component_name": b.component_name, "material_name": b.material_name, "quantity": b.quantity, "unit": b.unit, "scrap_rate_pct": b.scrap_rate_pct} for b in boms],
        "processes": [{"id": pr.id, "stage": pr.stage, "process_name": pr.process_name, "electricity_kwh": pr.electricity_kwh, "thermal_energy_mj": pr.thermal_energy_mj, "direct_emissions_kgco2e": pr.direct_emissions_kgco2e} for pr in processes],
        "routes": [{"id": r.id, "origin": r.origin, "destination": r.destination, "distance_km": r.distance_km, "transport_mode": r.transport_mode} for r in routes],
        "packagings": [{"id": pk.id, "packaging_type": pk.packaging_type, "material_type": pk.material_type, "weight_kg": pk.weight_kg, "recyclability_pct": pk.recyclability_pct} for pk in packagings],
        "pcf_records": [{"id": pcf.id, "boundary": pcf.boundary, "total_pcf_kgco2e": pcf.total_pcf_kgco2e, "stage_breakdown": pcf.stage_breakdown, "created_at": pcf.created_at} for pcf in pcf_records]
    }

@router.post("/products")
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    product = Product(
        organization_id=payload.organization_id,
        sku=payload.sku,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        functional_unit=payload.functional_unit,
        unit_weight_kg=payload.unit_weight_kg,
        created_by=current_user.id
    )
    db.add(product)
    db.flush()

    for b in (payload.boms or []):
        db.add(BOM(product_id=product.id, **b.model_dump(), created_by=current_user.id))
    for p in (payload.processes or []):
        db.add(Process(product_id=product.id, **p.model_dump(), created_by=current_user.id))
    for r in (payload.routes or []):
        db.add(Route(product_id=product.id, **r.model_dump(), created_by=current_user.id))
    for pkg in (payload.packagings or []):
        db.add(Packaging(product_id=product.id, **pkg.model_dump(), created_by=current_user.id))

    db.commit()
    db.refresh(product)
    return {"id": product.id, "sku": product.sku, "name": product.name}

@router.post("/calculate")
def calculate_product_pcf(
    payload: PCFCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    boms = db.query(BOM).filter(BOM.product_id == product.id, BOM.is_deleted == False).all()
    processes = db.query(Process).filter(Process.product_id == product.id, Process.is_deleted == False).all()
    routes = db.query(Route).filter(Route.product_id == product.id, Route.is_deleted == False).all()
    packagings = db.query(Packaging).filter(Packaging.product_id == product.id, Packaging.is_deleted == False).all()

    calc_res = calculate_pcf(
        product_sku=product.sku,
        functional_unit=product.functional_unit,
        boundary=payload.boundary,
        boms=[{"component_name": b.component_name, "material_name": b.material_name, "quantity": b.quantity, "scrap_rate_pct": b.scrap_rate_pct} for b in boms],
        processes=[{"stage": p.stage, "process_name": p.process_name, "electricity_kwh": p.electricity_kwh, "thermal_energy_mj": p.thermal_energy_mj, "direct_emissions_kgco2e": p.direct_emissions_kgco2e} for p in processes],
        packagings=[{"packaging_type": pk.packaging_type, "material_type": pk.material_type, "weight_kg": pk.weight_kg} for pk in packagings],
        routes=[{"origin": r.origin, "destination": r.destination, "distance_km": r.distance_km, "transport_mode": r.transport_mode} for r in routes],
        allocation_method=payload.allocation_method,
        use_phase_kwh_per_year=payload.use_phase_kwh_per_year,
        lifespan_years=payload.lifespan_years,
        recycling_rate_pct=payload.recycling_rate_pct
    )

    record = PCFRecord(
        product_id=product.id,
        boundary=payload.boundary,
        functional_unit=product.functional_unit,
        allocation_method=payload.allocation_method,
        total_pcf_kgco2e=calc_res["total_pcf_kgco2e"],
        stage_breakdown=calc_res["stage_breakdown"],
        iso_14067_compliant=True,
        calculation_details=calc_res,
        created_by=current_user.id
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    calc_res["record_id"] = record.id
    calc_res["product_name"] = product.name
    return calc_res

@router.get("/compare", response_model=List[PCFCompareItem])
def compare_product_pcfs(
    product_ids: List[str] = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """SKU-level PCF comparison view."""
    results = []
    for pid in product_ids:
        product = db.query(Product).filter(Product.id == pid, Product.is_deleted == False).first()
        if not product:
            continue
        latest = db.query(PCFRecord).filter(PCFRecord.product_id == pid, PCFRecord.is_deleted == False).order_by(PCFRecord.created_at.desc()).first()
        if latest:
            results.append(PCFCompareItem(
                product_id=product.id,
                name=product.name,
                sku=product.sku,
                total_pcf_kgco2e=latest.total_pcf_kgco2e,
                boundary=latest.boundary,
                stage_breakdown=latest.stage_breakdown
            ))
    return results

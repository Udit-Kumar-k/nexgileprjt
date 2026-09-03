"""Seed script populating realistic, audit-grade dummy data for DecarbX platform.

Requirements:
- 1 Organization with 3 Entities, 2 Facilities each
- 5+ Users across all roles (Admin, Sustainability Manager, ESG Analyst, Auditor, Supplier, C-Suite)
- 50 ActivityData records (mix of Scope 1/2/3) with corresponding Calculations and EmissionRecords
- 30 EmissionFactor records (energy, transport, materials, travel)
- 10 Suppliers with questionnaires and scorecards
- 5 Products with BOM and PCF calculations
- 3 Scenarios
- 2 Frameworks configured (CSRD + CDP)
- 4 Connectors & Webhooks
"""

from datetime import date, datetime, timedelta, timezone
from app.db import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.auth import User
from app.models.organization import (
    Organization, Entity, Facility, Department, CostCenter, ReportingBoundary
)
from app.models.carbon import (
    EmissionFactor, ActivityData, Calculation, EmissionRecord, Baseline, Target
)
from app.models.pcf import (
    Product, BOM, Process, Route, Packaging, PCFRecord
)
from app.models.supplier import (
    Supplier, Questionnaire, QuestionnaireSubmission, Scorecard, ActionPlan
)
from app.models.analytics import (
    Scenario, ReductionInitiative, AnomalyRecord
)
from app.models.compliance import (
    Framework, DataPoint, Evidence, Disclosure, CBAMRecord
)
from app.models.integration import (
    ConnectorConfig, WebhookLog
)
from app.services.calc_engine import calculate_emissions
from app.services.pcf_engine import calculate_pcf

def seed_database():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Organization).first():
            print("Database already contains data. Skipping full re-seed.")
            return

        print("Seeding Nexgile DecarbX Platform database...")

        # ----------------------------------------------------------------------
        # 1. Organization, Entities, Facilities, Departments, CostCenters
        # ----------------------------------------------------------------------
        org = Organization(
            name="Nexgile Global Technologies Inc.",
            code="NEX-GLBL",
            sector="Technology Hardware & Manufacturing",
            country="United States",
            reporting_currency="USD"
        )
        db.add(org)
        db.flush()

        entities_data = [
            {"name": "Americas Operations Corp", "code": "ENT-AMER", "country": "United States", "method": "Operational Control"},
            {"name": "EMEA Logistics & Systems B.V.", "code": "ENT-EMEA", "country": "Netherlands", "method": "Operational Control"},
            {"name": "APAC Manufacturing Ltd", "code": "ENT-APAC", "country": "Singapore", "method": "Operational Control"}
        ]

        entities = []
        facilities = []

        for e_idx, ed in enumerate(entities_data):
            entity = Entity(
                organization_id=org.id,
                name=ed["name"],
                code=ed["code"],
                country=ed["country"],
                consolidation_method=ed["method"],
                ownership_percentage=100.0
            )
            db.add(entity)
            db.flush()
            entities.append(entity)

            # Reporting Boundary
            boundary = ReportingBoundary(
                entity_id=entity.id,
                reporting_year=2024,
                boundary_type="Operational Control",
                consolidation_approach="100% Operational Control",
                is_active="Active",
                notes="Includes all leased and owned sites"
            )
            db.add(boundary)

            # 2 Facilities per Entity (6 total)
            fac_types = [("Manufacturing Plant", "Manufacturing", "camx"), ("Regional Distribution Center", "Warehouse", "rfce")]
            for f_idx, (fname_suffix, ftype, grid) in enumerate(fac_types):
                fac = Facility(
                    entity_id=entity.id,
                    name=f"{entity.name} - {fname_suffix} {f_idx+1}",
                    code=f"FAC-{entity.code[-4:]}-{f_idx+1}",
                    facility_type=ftype,
                    country=entity.country,
                    grid_region=f"GRID-{entity.country[:2]}-{grid}",
                    address=f"{100 * (f_idx+1)} Industrial Parkway"
                )
                db.add(fac)
                db.flush()
                facilities.append(fac)

                # Department & Cost Center
                dept = Department(
                    facility_id=fac.id,
                    name=f"Operations & Production D-{f_idx+1}",
                    code=f"DEPT-{fac.code[-6:]}"
                )
                db.add(dept)
                db.flush()

                cc = CostCenter(
                    department_id=dept.id,
                    name=f"Cost Center {fac.code[-4:]}",
                    code=f"CC-{fac.code[-4:]}",
                    budget_currency="USD"
                )
                db.add(cc)

        # ----------------------------------------------------------------------
        # 2. Users across all roles
        # ----------------------------------------------------------------------
        password_hash = get_password_hash("DecarbX2024!")
        users_data = [
            {"email": "admin@nexgile.com", "name": "Sarah Connor", "role": "Admin", "permissions": []},
            {"email": "sustainability@nexgile.com", "name": "Elena Rostova", "role": "Sustainability Manager", "permissions": []},
            {"email": "analyst@nexgile.com", "name": "Marcus Chen", "role": "ESG Analyst", "permissions": [facilities[0].id, facilities[1].id]},
            {"email": "auditor@pwc-assurance.com", "name": "David Thorne", "role": "Auditor", "permissions": []},
            {"email": "supplier@foxconn-tech.com", "name": "Wei Zhang", "role": "Supplier", "permissions": []},
            {"email": "csuite@nexgile.com", "name": "Victoria Sterling (CSO)", "role": "C-Suite", "permissions": []},
        ]

        users = {}
        for ud in users_data:
            u = User(
                email=ud["email"],
                hashed_password=password_hash,
                full_name=ud["name"],
                role=ud["role"],
                organization_id=org.id,
                facility_permissions=ud["permissions"],
                is_active=True
            )
            db.add(u)
            db.flush()
            users[ud["role"]] = u

        admin_user_id = users["Admin"].id

        # ----------------------------------------------------------------------
        # 3. 30 EmissionFactor records
        # ----------------------------------------------------------------------
        factors_data = [
            # Scope 1 - Fuels
            ("Natural Gas (Stationary)", "Stationary Combustion", "CO2e", 0.0053, "therms", "EPA", "2024.1", 3.0),
            ("Diesel Fuel (Stationary)", "Stationary Combustion", "CO2e", 0.00268, "liters", "EPA", "2024.1", 4.0),
            ("Propane (Stationary)", "Stationary Combustion", "CO2e", 0.00151, "liters", "EPA", "2024.1", 5.0),
            ("Fuel Oil #2", "Stationary Combustion", "CO2e", 0.00296, "liters", "EPA", "2024.1", 4.0),
            ("Heavy Fuel Oil", "Stationary Combustion", "CO2e", 0.00318, "liters", "DEFRA", "2024.1", 5.0),
            # Scope 1 - Mobile
            ("Fleet Gasoline (Passenger Cars)", "Mobile Combustion", "CO2e", 0.00231, "liters", "EPA", "2024.1", 4.0),
            ("Fleet Diesel (Light Duty)", "Mobile Combustion", "CO2e", 0.00268, "liters", "EPA", "2024.1", 4.0),
            ("Heavy Duty Commercial Truck Diesel", "Mobile Combustion", "CO2e", 0.000162, "km", "DEFRA", "2024.1", 5.0),
            ("Fleet Delivery Van (Diesel)", "Mobile Combustion", "CO2e", 0.000215, "km", "DEFRA", "2024.1", 5.0),
            ("Compressed Natural Gas Fleet", "Mobile Combustion", "CO2e", 0.000054, "km", "EPA", "2024.1", 6.0),
            # Scope 1 - Fugitive
            ("Refrigerant R-410A (GWP 2088)", "Fugitive Emissions", "CO2e", 2.088, "kg", "EPA", "2024.1", 8.0),
            ("Refrigerant R-134a (GWP 1430)", "Fugitive Emissions", "CO2e", 1.430, "kg", "EPA", "2024.1", 8.0),
            ("Refrigerant R-404A (GWP 3922)", "Fugitive Emissions", "CO2e", 3.922, "kg", "EPA", "2024.1", 8.0),
            # Scope 2 - Electricity Grids
            ("US Grid Electricity (CAMX Average)", "Purchased Electricity", "CO2e", 0.000225, "kWh", "EPA eGRID", "2024.1", 3.5),
            ("US Grid Electricity (RFCW Average)", "Purchased Electricity", "CO2e", 0.000452, "kWh", "EPA eGRID", "2024.1", 3.5),
            ("EU Central Grid Electricity (NL)", "Purchased Electricity", "CO2e", 0.000318, "kWh", "IEA", "2024.1", 4.0),
            ("APAC Grid Electricity (SG)", "Purchased Electricity", "CO2e", 0.000408, "kWh", "IEA", "2024.1", 4.5),
            ("District Steam / Heating", "Purchased Steam", "CO2e", 0.000066, "MJ", "ecoinvent", "2024.1", 6.0),
            # Scope 3 - Materials (Category 1)
            ("Aluminum Ingot (Primary)", "Purchased Goods", "CO2e", 0.00824, "kg", "ecoinvent", "2024.1", 7.0),
            ("Steel Sheet (Cold Rolled)", "Purchased Goods", "CO2e", 0.00215, "kg", "ecoinvent", "2024.1", 6.0),
            ("Copper Wire & Cathode", "Purchased Goods", "CO2e", 0.00410, "kg", "ecoinvent", "2024.1", 8.0),
            ("Polycarbonate Plastic Resin", "Purchased Goods", "CO2e", 0.00540, "kg", "ecoinvent", "2024.1", 7.0),
            ("Printed Circuit Board Assembly", "Purchased Goods", "CO2e", 0.02850, "kg", "ecoinvent", "2024.1", 10.0),
            ("Corrugated Cardboard Packaging", "Purchased Packaging", "CO2e", 0.00095, "kg", "DEFRA", "2024.1", 5.0),
            # Scope 3 - Transport & Travel (Cat 4 & 6)
            ("Ocean Container Freight (Average)", "Upstream Transport", "CO2e", 0.000015, "t-km", "DEFRA", "2024.1", 9.0),
            ("Air Freight Cargo (Long Haul)", "Upstream Transport", "CO2e", 0.000602, "t-km", "DEFRA", "2024.1", 10.0),
            ("Heavy Road Freight (Articulated >33t)", "Upstream Transport", "CO2e", 0.000089, "t-km", "DEFRA", "2024.1", 7.0),
            ("Commercial Flight (Long Haul Business)", "Business Travel", "CO2e", 0.000192, "p-km", "DEFRA", "2024.1", 8.0),
            ("Commercial Flight (Short Haul Economy)", "Business Travel", "CO2e", 0.000156, "p-km", "DEFRA", "2024.1", 8.0),
            ("Hotel Stay (Average International)", "Business Travel", "CO2e", 0.02850, "room-night", "DEFRA", "2024.1", 12.0)
        ]

        factors = []
        for f_name, cat, gas, val, denom, src, ver, unc in factors_data:
            ef = EmissionFactor(
                name=f_name,
                category=cat,
                gas_type=gas,
                factor_value=val,
                unit_numerator="tCO2e",
                unit_denominator=denom,
                source=src,
                version=ver,
                uncertainty_pct=unc,
                is_active=True,
                created_by=admin_user_id
            )
            db.add(ef)
            db.flush()
            factors.append(ef)

        # Map factors for quick retrieval
        factor_map = {f.category: f for f in factors}

        # ----------------------------------------------------------------------
        # 4. 50 ActivityData records with Calculations & EmissionRecords
        # ----------------------------------------------------------------------
        periods = ["2024-Q1", "2024-Q2"]
        activity_templates = [
            # Scope 1
            (1, "Stationary Combustion", "Natural Gas", 12500, "therms", factors[0]),
            (1, "Stationary Combustion", "Diesel Generator Fuel", 2400, "liters", factors[1]),
            (1, "Mobile Combustion", "Fleet Delivery Vans", 18500, "km", factors[8]),
            (1, "Fugitive Emissions", "HVAC R-410A Top-up", 18.5, "kg", factors[10]),
            # Scope 2
            (2, "Purchased Electricity", "Grid Electricity (Location)", 185000, "kWh", factors[13]),
            (2, "Purchased Electricity", "Grid Electricity (Market)", 140000, "kWh", factors[14]),
            (2, "Purchased Steam", "Industrial Steam Network", 250000, "MJ", factors[17]),
            # Scope 3
            (3, "Purchased Goods", "Raw Aluminum Stock", 45000, "kg", factors[18]),
            (3, "Purchased Goods", "Cold Rolled Steel", 82000, "kg", factors[19]),
            (3, "Purchased Goods", "PCB Components", 12500, "kg", factors[22]),
            (3, "Purchased Packaging", "Cardboard Shipping Boxes", 14200, "kg", factors[23]),
            (3, "Upstream Transport", "Ocean Container Logistics", 850000, "t-km", factors[24]),
            (3, "Upstream Transport", "Air Cargo Express", 42000, "t-km", factors[25]),
            (3, "Business Travel", "International Executive Flights", 120000, "p-km", factors[27]),
            (3, "Business Travel", "Domestic Economy Flights", 65000, "p-km", factors[28]),
        ]

        act_count = 0
        while act_count < 50:
            for fac in facilities:
                if act_count >= 50:
                    break
                tmpl = activity_templates[act_count % len(activity_templates)]
                scope, cat, act_type, base_qty, unit, ef = tmpl
                
                period = periods[act_count % len(periods)]
                qty = base_qty * (0.85 + 0.3 * ((act_count * 7) % 10) / 10.0) # realistic variation

                # Occasional anomaly
                is_anomaly = (act_count == 7 or act_count == 23)
                if is_anomaly:
                    qty = qty * 2.8

                act = ActivityData(
                    organization_id=org.id,
                    entity_id=fac.entity_id,
                    facility_id=fac.id,
                    scope=scope,
                    category=cat,
                    activity_type=act_type,
                    quantity=round(qty, 2),
                    unit=unit,
                    start_date=date(2024, 1, 1) if period == "2024-Q1" else date(2024, 4, 1),
                    end_date=date(2024, 3, 31) if period == "2024-Q1" else date(2024, 6, 30),
                    reporting_period=period,
                    completeness_score=0.98,
                    confidence_tier="high",
                    validation_status="flagged" if is_anomaly else "passed",
                    anomaly_flag=is_anomaly,
                    source_document=f"MeterReading_{fac.code}_{period}.pdf",
                    created_by=admin_user_id
                )
                db.add(act)
                db.flush()

                # Calculate emissions
                calc_res = calculate_emissions(
                    quantity=act.quantity,
                    unit=act.unit,
                    factor_value=ef.factor_value,
                    factor_denominator=ef.unit_denominator,
                    uncertainty_pct=ef.uncertainty_pct
                )

                calc = Calculation(
                    activity_data_id=act.id,
                    factor_id=ef.id,
                    factor_version=ef.version,
                    formula_applied=calc_res["formula_string"],
                    unit_conversion_factor=calc_res["unit_conversion_factor"],
                    allocation_pct=100.0,
                    emissions_tco2e=calc_res["gross_emissions_tco2e"],
                    uncertainty_min_tco2e=calc_res["uncertainty_min_tco2e"],
                    uncertainty_max_tco2e=calc_res["uncertainty_max_tco2e"],
                    created_by=admin_user_id
                )
                db.add(calc)

                rec = EmissionRecord(
                    organization_id=org.id,
                    entity_id=fac.entity_id,
                    facility_id=fac.id,
                    activity_data_id=act.id,
                    emission_factor_id=ef.id,
                    factor_version=ef.version,
                    scope=scope,
                    category=cat,
                    reporting_period=period,
                    gross_emissions_tco2e=calc_res["gross_emissions_tco2e"],
                    net_emissions_tco2e=calc_res["net_emissions_tco2e"],
                    rec_offset_tco2e=0.0,
                    formula_string=calc_res["formula_string"],
                    unit_conversions_applied=calc_res["unit_conversions_applied"],
                    allocation_method="100% Operational Control",
                    approved_by=admin_user_id,
                    approved_at=datetime.now(timezone.utc),
                    is_scenario=False,
                    created_by=admin_user_id
                )
                db.add(rec)
                act_count += 1

        # ----------------------------------------------------------------------
        # 5. Baseline & Target
        # ----------------------------------------------------------------------
        baseline = Baseline(
            organization_id=org.id,
            base_year=2021,
            scope1_tco2e=1420.5,
            scope2_location_tco2e=3890.2,
            scope2_market_tco2e=3240.0,
            scope3_tco2e=7240.8,
            total_tco2e=11901.3,
            is_locked=True,
            created_by=admin_user_id
        )
        db.add(baseline)

        target = Target(
            organization_id=org.id,
            name="SBTi 1.5°C Committed Near-Term Target (42% by 2030)",
            target_type="Absolute",
            scope_coverage="Scope 1+2+3",
            baseline_year=2021,
            target_year=2030,
            target_reduction_pct=42.0,
            current_progress_pct=28.5,
            trajectory_json=[
                {"year": 2021, "milestone_tco2e": 11901},
                {"year": 2024, "milestone_tco2e": 9800},
                {"year": 2027, "milestone_tco2e": 8200},
                {"year": 2030, "milestone_tco2e": 6902},
            ],
            created_by=admin_user_id
        )
        db.add(target)

        # ----------------------------------------------------------------------
        # 6. 10 Suppliers with Questionnaires & Scorecards & Action Plans
        # ----------------------------------------------------------------------
        questionnaire = Questionnaire(
            organization_id=org.id,
            title="Scope 3 Upstream Decarbonization & Materiality Assessment 2024",
            description="Detailed ESG disclosure covering Scope 1 & 2 emissions, renewable energy share, and SBTi targets.",
            materiality_category="Manufacturing & Raw Materials",
            questions=[
                {"id": "q1", "text": "Do you calculate and audit Scope 1 & 2 GHG emissions?", "type": "boolean", "weight": 25},
                {"id": "q2", "text": "What percentage of your operational electricity is sourced from renewables?", "type": "percentage", "weight": 25},
                {"id": "q3", "text": "Do you have validated Science-Based Targets (SBTi)?", "type": "boolean", "weight": 25},
                {"id": "q4", "text": "What is your primary emission intensity per $10k output?", "type": "number", "weight": 25}
            ],
            is_active=True,
            created_by=admin_user_id
        )
        db.add(questionnaire)
        db.flush()

        suppliers_data = [
            ("Foxconn Precision Components", "Taiwan", "Tier 1", "Electronics", 92.5, "A", -8.2, 1420.0, 85.0, True),
            ("Nippon Steel Specialty Alloy", "Japan", "Tier 1", "Raw Materials", 81.0, "B", -4.5, 3850.0, 42.0, True),
            ("BASF Performance Polymers", "Germany", "Tier 1", "Raw Materials", 88.0, "A", -6.0, 2100.0, 70.0, True),
            ("Smurfit Kappa Packaging", "Ireland", "Tier 2", "Packaging", 78.5, "B", -3.2, 850.0, 50.0, False),
            ("TSMC Semiconductor Foundry", "Taiwan", "Tier 1", "Electronics", 96.0, "A", -11.5, 4200.0, 95.0, True),
            ("Maersk Global Logistics", "Denmark", "Tier 1", "Logistics", 84.0, "B", -5.8, 5100.0, 35.0, True),
            ("LG Chem Advanced Materials", "South Korea", "Tier 1", "Raw Materials", 72.0, "C", +1.2, 2900.0, 25.0, False),
            ("Stora Enso Fiber & Pulp", "Finland", "Tier 2", "Packaging", 89.0, "A", -7.4, 620.0, 80.0, True),
            ("Delta Electronics Power Systems", "Taiwan", "Tier 2", "Electronics", 86.5, "B", -4.9, 1150.0, 65.0, True),
            ("Schneider Electric Infrastructure", "France", "Tier 1", "Electronics", 94.0, "A", -9.8, 1800.0, 90.0, True),
        ]

        for s_name, country, tier, cat, mat_score, rating, yoy, s12_emissions, renew_pct, sbti in suppliers_data:
            code = f"SUP-{s_name[:3].upper()}-{abs(hash(s_name)) % 1000}"
            sup = Supplier(
                organization_id=org.id,
                name=s_name,
                code=code,
                contact_email=f"esg@{s_name.lower().replace(' ', '')[:8]}.com",
                contact_name=f"Contact at {s_name}",
                tier=tier,
                country=country,
                category=cat,
                spend_usd=round(abs(hash(s_name)) % 5000000 + 500000, 2),
                onboarding_status="verified",
                created_by=admin_user_id
            )
            db.add(sup)
            db.flush()

            # Scorecard
            sc = Scorecard(
                supplier_id=sup.id,
                reporting_year=2024,
                emissions_scope1_2_tco2e=s12_emissions,
                emissions_intensity=round(s12_emissions / (sup.spend_usd / 100000), 2),
                maturity_score=mat_score,
                rating=rating,
                yoy_change_pct=yoy,
                cdp_score="A" if rating == "A" else "B",
                sbti_committed=sbti,
                renewable_energy_pct=renew_pct,
                created_by=admin_user_id
            )
            db.add(sc)

            # Action plan
            ap = ActionPlan(
                supplier_id=sup.id,
                initiative_name=f"{s_name} - Clean Energy Transition PPA",
                description="Sign 10-year PPA to cover 80%+ factory load with solar/wind.",
                target_reduction_tco2e=round(s12_emissions * 0.25, 1),
                due_date=date(2025, 6, 30),
                status="in_progress",
                assigned_to=sup.contact_email,
                created_by=admin_user_id
            )
            db.add(ap)

        # ----------------------------------------------------------------------
        # 7. 5 Products with BOM and PCF Calculations
        # ----------------------------------------------------------------------
        products_data = [
            ("NX-SRV-1000", "Nexgile EdgeCompute Server X1", "Enterprise Servers", "1 Server Unit", 14.5),
            ("NX-ROUT-500", "DecarbX Smart Gateway Router", "Networking", "1 Router Unit", 2.2),
            ("NX-SENS-100", "IoT Environmental Sensor Pod", "IoT Sensors", "1 Sensor Pod", 0.35),
            ("NX-PWR-800", "EcoPower 800W Titanium PSU", "Power Systems", "1 Power Supply", 1.8),
            ("NX-MOD-200", "DecarbX Modular Battery Enclosure", "Energy Storage", "1 Enclosure", 24.0)
        ]

        for sku, pname, pcat, funit, weight in products_data:
            prod = Product(
                organization_id=org.id,
                sku=sku,
                name=pname,
                category=pcat,
                description=f"Enterprise high-efficiency {pname} engineered for circularity.",
                functional_unit=funit,
                unit_weight_kg=weight,
                created_by=admin_user_id
            )
            db.add(prod)
            db.flush()

            # BOM
            boms = [
                BOM(product_id=prod.id, component_name="Chassis Housing", material_name="Aluminum Ingot", quantity=weight * 0.45, scrap_rate_pct=2.5, created_by=admin_user_id),
                BOM(product_id=prod.id, component_name="Motherboard & Circuitry", material_name="Printed Circuit Board", quantity=weight * 0.30, scrap_rate_pct=1.0, created_by=admin_user_id),
                BOM(product_id=prod.id, component_name="Internal Connectors", material_name="Copper Wire", quantity=weight * 0.15, scrap_rate_pct=3.0, created_by=admin_user_id),
                BOM(product_id=prod.id, component_name="Bezel & Brackets", material_name="Polycarbonate Plastic Resin", quantity=weight * 0.10, scrap_rate_pct=2.0, created_by=admin_user_id)
            ]
            for b in boms:
                db.add(b)

            # Process
            proc = Process(
                product_id=prod.id,
                stage="Manufacturing",
                process_name="SMT Pick & Place Assembly",
                electricity_kwh=weight * 12.0,
                thermal_energy_mj=weight * 4.0,
                direct_emissions_kgco2e=0.15,
                created_by=admin_user_id
            )
            db.add(proc)

            # Packaging
            pkg = Packaging(
                product_id=prod.id,
                packaging_type="Corrugated Box with Molded Pulp",
                material_type="Corrugated Cardboard",
                weight_kg=weight * 0.12,
                recyclability_pct=100.0,
                created_by=admin_user_id
            )
            db.add(pkg)

            # Route
            rt = Route(
                product_id=prod.id,
                origin="Singapore Factory",
                destination="Rotterdam Hub",
                distance_km=14200.0,
                transport_mode="Ocean Cargo",
                created_by=admin_user_id
            )
            db.add(rt)

            # PCF Record
            pcf_calc = calculate_pcf(
                product_sku=prod.sku,
                functional_unit=prod.functional_unit,
                boundary="cradle-to-gate",
                boms=[{"component_name": b.component_name, "material_name": b.material_name, "quantity": b.quantity, "scrap_rate_pct": b.scrap_rate_pct} for b in boms],
                processes=[{"stage": proc.stage, "process_name": proc.process_name, "electricity_kwh": proc.electricity_kwh, "thermal_energy_mj": proc.thermal_energy_mj, "direct_emissions_kgco2e": proc.direct_emissions_kgco2e}],
                packagings=[{"packaging_type": pkg.packaging_type, "material_type": pkg.material_type, "weight_kg": pkg.weight_kg}],
                routes=[{"origin": rt.origin, "destination": rt.destination, "distance_km": rt.distance_km, "transport_mode": rt.transport_mode}]
            )

            pcf_record = PCFRecord(
                product_id=prod.id,
                boundary="cradle-to-gate",
                functional_unit=prod.functional_unit,
                allocation_method="Mass Allocation",
                total_pcf_kgco2e=pcf_calc["total_pcf_kgco2e"],
                stage_breakdown=pcf_calc["stage_breakdown"],
                iso_14067_compliant=True,
                calculation_details=pcf_calc,
                created_by=admin_user_id
            )
            db.add(pcf_record)

        # ----------------------------------------------------------------------
        # 8. 3 What-If Scenarios & Reduction Initiatives
        # ----------------------------------------------------------------------
        scenarios_data = [
            ("100% Renewable PPA for Global Facilities", "Procure virtual and on-site solar/wind contracts to replace grid electricity.", [
                {"name": "Renewable Electricity Procurement", "scope": 2, "reduction_pct": 85.0}
            ]),
            ("Fleet Electrification (EV Conversion by 2028)", "Replace 100% of internal combustion delivery and utility vehicles with battery EVs.", [
                {"name": "EV Fleet Replacement", "scope": 1, "reduction_pct": 70.0}
            ]),
            ("Low-Carbon Circular Steel & Aluminum Sourcing", "Require Tier-1 suppliers to transition to 80%+ recycled scrap feedstocks.", [
                {"name": "Recycled Material Mandate", "scope": 3, "reduction_pct": 35.0}
            ]),
        ]

        for s_title, s_desc, levers in scenarios_data:
            scen = Scenario(
                organization_id=org.id,
                name=s_title,
                description=s_desc,
                baseline_year=2023,
                target_year=2030,
                levers=levers,
                projected_reduction_tco2e=1450.0,
                projected_reduction_pct=22.4,
                is_active=True,
                created_by=admin_user_id
            )
            db.add(scen)

        initiatives_data = [
            ("Facility LED Retrofit & Smart HVAC Controls", "Energy Efficiency", 280.0, 240.0, 85000, 12000, 2.1, "active"),
            ("On-Site Rooftop Solar Array (Americas Plant)", "Renewable Electricity", 450.0, 410.0, 320000, 15000, 4.5, "active"),
            ("Electric Forklift & Yard Shunter Transition", "Fleet Electrification", 110.0, 95.0, 95000, 8000, 3.2, "completed"),
            ("Supplier Low-Carbon Scrap Packaging Standard", "Low-Carbon Materials", 320.0, 290.0, 40000, 5000, 1.4, "active"),
        ]
        for iname, ltype, tgt, act, capex, opex, pb, st in initiatives_data:
            db.add(ReductionInitiative(
                organization_id=org.id,
                name=iname,
                lever_type=ltype,
                target_reduction_tco2e=tgt,
                actual_reduction_tco2e=act,
                capex_usd=capex,
                opex_annual_usd=opex,
                payback_years=pb,
                status=st,
                created_by=admin_user_id
            ))

        # ----------------------------------------------------------------------
        # 9. 2 Configured Frameworks (CSRD + CDP) with Data Points & CBAM
        # ----------------------------------------------------------------------
        csrd = Framework(
            name="CSRD (Corporate Sustainability Reporting Directive) / ESRS E1",
            code="CSRD-ESRS-E1",
            version="2024",
            description="European Sustainability Reporting Standards E1 Climate Change disclosure requirements.",
            jurisdiction="European Union"
        )
        db.add(csrd)
        db.flush()

        cdp = Framework(
            name="CDP Climate Change Questionnaire",
            code="CDP-CLIMATE",
            version="2024",
            description="Global standard environmental disclosure system for investors and stakeholders.",
            jurisdiction="Global"
        )
        db.add(cdp)
        db.flush()

        csrd_datapoints = [
            ("E1-1", "Transition plan for climate change mitigation", "Approved 1.5°C Net Zero 2040 Plan", "Text", "approved", "SBTi Trajectory", "https://evidence.nexgile.com/transition_plan_2024.pdf"),
            ("E1-4", "Targets related to climate change mitigation", "42% Absolute Reduction by 2030", "%", "approved", "SBTi Near-Term Target", "https://evidence.nexgile.com/sbti_approval_letter.pdf"),
            ("E1-6.1", "Gross Scope 1 GHG emissions", "1,248.5", "tCO2e", "verified", "Scope 1 Stationary & Mobile Sum", "https://evidence.nexgile.com/scope1_audit_pack.pdf"),
            ("E1-6.2", "Gross Scope 2 GHG emissions (Location-based)", "2,840.1", "tCO2e", "verified", "Scope 2 Location Sum", "https://evidence.nexgile.com/utility_invoices_2024.pdf"),
            ("E1-6.3", "Gross Scope 2 GHG emissions (Market-based)", "2,150.4", "tCO2e", "verified", "Scope 2 Market + RECs Deductions", "https://evidence.nexgile.com/rec_retirement_certificates.pdf"),
            ("E1-6.4", "Gross Scope 3 GHG emissions (Significant Categories)", "6,410.8", "tCO2e", "in_review", "Scope 3 Categories 1, 4, 6 Sum", "https://evidence.nexgile.com/supplier_scope3_inventory.pdf"),
            ("E1-9", "Anticipated financial effects from climate risks", "4.2% EBITDA at Risk (Carbon Price)", "%", "draft", "Scenario Financial Model", "https://evidence.nexgile.com/tcfd_financial_quant.pdf"),
        ]

        for code, name, val, unit, st, clink, evurl in csrd_datapoints:
            db.add(DataPoint(
                framework_id=csrd.id,
                code=code,
                name=name,
                requirement_text=f"Full disclosure requirement for {name}.",
                reported_value=val,
                unit=unit,
                status=st,
                calculation_link=clink,
                evidence_url=evurl,
                created_by=admin_user_id
            ))

        cdp_datapoints = [
            ("C4.1", "Did you have an emissions target that was active in the reporting year?", "Yes, Absolute SBTi Target", "Text", "approved", "Target Registry", "https://evidence.nexgile.com/cdp_target_disclosure.pdf"),
            ("C6.1", "What were your organization's gross global Scope 1 emissions?", "1,248.5", "tCO2e", "verified", "Scope 1 Master Ledger", "https://evidence.nexgile.com/scope1_audit_pack.pdf"),
            ("C6.3", "What were your organization's gross global Scope 2 emissions?", "2,150.4", "tCO2e", "verified", "Scope 2 Market Ledger", "https://evidence.nexgile.com/rec_retirement_certificates.pdf"),
            ("C6.5", "Account for your organization's gross global Scope 3 emissions", "6,410.8", "tCO2e", "in_review", "Scope 3 Ledger", "https://evidence.nexgile.com/supplier_scope3_inventory.pdf"),
        ]

        for code, name, val, unit, st, clink, evurl in cdp_datapoints:
            db.add(DataPoint(
                framework_id=cdp.id,
                code=code,
                name=name,
                requirement_text=f"CDP question {code}: {name}.",
                reported_value=val,
                unit=unit,
                status=st,
                calculation_link=clink,
                evidence_url=evurl,
                created_by=admin_user_id
            ))

        # CBAM Records
        cbam_records = [
            ("CN 7208 51", "Flat-rolled products of iron/steel (width >= 600mm)", "South Korea", "2024-Q1", 420.0, 1.85, 0.42, 953.4, 62000.0),
            ("CN 7601 10", "Unwrought non-alloy aluminium ingots", "Bahrain", "2024-Q1", 280.0, 6.20, 1.80, 2240.0, 145000.0),
            ("CN 3102 10", "Urea and synthetic nitrogen fertilizers", "Egypt", "2024-Q2", 150.0, 2.10, 0.35, 367.5, 24000.0),
            ("CN 2523 29", "Portland cement clinker", "Turkey", "2024-Q2", 850.0, 0.78, 0.12, 765.0, 51000.0),
        ]
        for cn, desc, country, qtr, vol, direct, indirect, total, price in cbam_records:
            db.add(CBAMRecord(
                organization_id=org.id,
                product_code=cn,
                product_description=desc,
                country_of_origin=country,
                reporting_quarter=qtr,
                imported_volume_tonnes=vol,
                direct_embedded_emissions=direct,
                indirect_embedded_emissions=indirect,
                total_embedded_emissions_tco2e=total,
                carbon_price_due_eur=price,
                created_by=admin_user_id
            ))

        # ----------------------------------------------------------------------
        # 10. Connectors & Inbound Webhooks
        # ----------------------------------------------------------------------
        connectors = [
            ("SAP S/4HANA ERP Connector", "ERP", "active", datetime.now(timezone.utc) - timedelta(hours=3), 1420),
            ("Schneider EcoStruxure IoT Smart Meters", "SmartMeter", "active", datetime.now(timezone.utc) - timedelta(minutes=15), 84200),
            ("EDF Energy Utility Bill EDI Direct Feed", "Utility", "active", datetime.now(timezone.utc) - timedelta(days=1), 184),
            ("Geotab Commercial Fleet Telematics", "Telematics", "active", datetime.now(timezone.utc) - timedelta(hours=1), 4850),
        ]
        for cname, ctype, cst, lsync, recs in connectors:
            db.add(ConnectorConfig(
                name=cname,
                connector_type=ctype,
                status=cst,
                last_sync=lsync,
                records_synced=recs,
                created_by=admin_user_id
            ))

        webhooks = [
            ("meter_reading_ingested", "Schneider IoT MQTT Gateway", "success", '{"meter_id": "MTR-CAMX-01", "kwh": 4820.5, "facility": "FAC-AMER-1"}'),
            ("utility_invoice_received", "EDF Energy EDI 810 Service", "success", '{"invoice_id": "INV-2024-04-EDF", "total_therms": 12500, "facility": "FAC-EMEA-1"}'),
            ("supplier_questionnaire_completed", "Supplier Engagement Portal", "success", '{"supplier_id": "SUP-FOX-101", "submission_id": "SUB-8812", "rating": "A"}'),
            ("erp_goods_receipt_batch", "SAP S/4HANA OData v4", "success", '{"po_number": "PO-994120", "material": "Aluminum Ingot", "qty_kg": 25000}'),
        ]
        for etype, src, wst, preview in webhooks:
            db.add(WebhookLog(
                event_type=etype,
                source=src,
                status=wst,
                payload_preview=preview,
                created_by=admin_user_id
            ))

        db.commit()
        print("Nexgile DecarbX Platform database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

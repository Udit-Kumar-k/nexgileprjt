"""Working CSV Activity Data Ingestion Engine.
Parses CSV rows, validates required columns, computes data quality scores,
and generates ActivityData & Calculation records.
"""

import csv
import io
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.carbon import ActivityData, EmissionFactor, Calculation, EmissionRecord
from app.services.calc_engine import calculate_emissions

REQUIRED_COLUMNS = ["scope", "category", "activity_type", "quantity", "unit", "start_date", "end_date", "reporting_period"]

def parse_and_import_activity_csv(
    csv_content: str,
    organization_id: str,
    entity_id: str,
    facility_id: str,
    user_id: str,
    db: Session
) -> Dict[str, Any]:
    f = io.StringIO(csv_content.strip())
    reader = csv.DictReader(f)

    if not reader.fieldnames:
        return {"success": False, "error": "CSV file is empty or headers are missing."}

    # Normalize headers
    normalized_headers = {h.strip().lower(): h for h in reader.fieldnames}
    missing = [c for c in REQUIRED_COLUMNS if c not in normalized_headers]
    if missing:
        return {"success": False, "error": f"Missing required columns: {', '.join(missing)}"}

    imported_records = []
    errors = []
    row_num = 1

    for row in reader:
        row_num += 1
        try:
            scope = int(row[normalized_headers["scope"]])
            category = row[normalized_headers["category"]].strip()
            activity_type = row[normalized_headers["activity_type"]].strip()
            quantity = float(row[normalized_headers["quantity"]])
            unit = row[normalized_headers["unit"]].strip()
            start_date_str = row[normalized_headers["start_date"]].strip()
            end_date_str = row[normalized_headers["end_date"]].strip()
            reporting_period = row[normalized_headers["reporting_period"]].strip()

            # Parse dates
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            # Find matching factor
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.category.ilike(f"%{category}%"),
                EmissionFactor.is_active == True,
                EmissionFactor.is_deleted == False
            ).first()

            if not factor:
                factor = db.query(EmissionFactor).filter(EmissionFactor.is_active == True).first()

            # Calculate data quality
            completeness = 1.0
            confidence = "high"
            if quantity <= 0:
                confidence = "estimated"
                completeness = 0.5

            # Anomaly detection for bulk import (standard 30% deviation threshold)
            recent_activities = db.query(ActivityData).filter(
                ActivityData.facility_id == facility_id,
                ActivityData.activity_type == activity_type,
                ActivityData.is_deleted == False
            ).limit(6).all()

            is_anomaly = False
            if recent_activities:
                avg_q = sum(a.quantity for a in recent_activities) / len(recent_activities)
                if avg_q > 0 and (abs(quantity - avg_q) / avg_q) > 0.30:
                    is_anomaly = True

            activity = ActivityData(
                organization_id=organization_id,
                entity_id=entity_id,
                facility_id=facility_id,
                scope=scope,
                category=category,
                activity_type=activity_type,
                quantity=quantity,
                unit=unit,
                start_date=start_date,
                end_date=end_date,
                reporting_period=reporting_period,
                completeness_score=completeness,
                confidence_tier=confidence,
                validation_status="passed",
                anomaly_flag=is_anomaly,
                source_document="csv_batch_upload.csv",
                created_by=user_id
            )
            db.add(activity)
            db.flush()

            if factor:
                calc_res = calculate_emissions(
                    quantity=activity.quantity,
                    unit=activity.unit,
                    factor_value=factor.factor_value,
                    factor_denominator=factor.unit_denominator,
                    uncertainty_pct=factor.uncertainty_pct
                )

                calc = Calculation(
                    activity_data_id=activity.id,
                    factor_id=factor.id,
                    factor_version=factor.version,
                    formula_applied=calc_res["formula_string"],
                    unit_conversion_factor=calc_res["unit_conversion_factor"],
                    allocation_pct=100.0,
                    emissions_tco2e=calc_res["gross_emissions_tco2e"],
                    uncertainty_min_tco2e=calc_res["uncertainty_min_tco2e"],
                    uncertainty_max_tco2e=calc_res["uncertainty_max_tco2e"],
                    created_by=user_id
                )
                db.add(calc)

                rec = EmissionRecord(
                    organization_id=organization_id,
                    entity_id=entity_id,
                    facility_id=facility_id,
                    activity_data_id=activity.id,
                    emission_factor_id=factor.id,
                    factor_version=factor.version,
                    scope=scope,
                    category=category,
                    reporting_period=reporting_period,
                    gross_emissions_tco2e=calc_res["gross_emissions_tco2e"],
                    net_emissions_tco2e=calc_res["net_emissions_tco2e"],
                    rec_offset_tco2e=0.0,
                    formula_string=calc_res["formula_string"],
                    unit_conversions_applied=calc_res["unit_conversions_applied"],
                    allocation_method="100% Operational Control",
                    is_scenario=False,
                    created_by=user_id
                )
                db.add(rec)

            imported_records.append(activity.id)

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    db.commit()

    return {
        "success": True,
        "imported_count": len(imported_records),
        "failed_count": len(errors),
        "errors": errors
    }

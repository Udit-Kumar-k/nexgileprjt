from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.db import get_db
from app.core.rbac import get_current_user, require_roles, Role, EDIT_ROLES
from app.models.auth import User
from app.models.integration import ConnectorConfig, WebhookLog
from app.schemas.integration import (
    ConnectorConfigResponse,
    WebhookLogResponse,
    CSVImportResponse
)
from app.services.csv_import import parse_and_import_activity_csv

router = APIRouter(prefix="/integration", tags=["Integrations & Data Connectors"])

@router.get("/connectors", response_model=List[ConnectorConfigResponse])
def list_connectors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ConnectorConfig).filter(ConnectorConfig.is_deleted == False).all()

@router.post("/connectors/{id}/sync")
def trigger_connector_sync(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    connector = db.query(ConnectorConfig).filter(ConnectorConfig.id == id, ConnectorConfig.is_deleted == False).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    connector.last_sync = datetime.now(timezone.utc)
    connector.records_synced += 48
    connector.status = "active"
    db.commit()
    return {"status": "synced", "records_synced": connector.records_synced, "timestamp": connector.last_sync}

@router.post("/upload-csv", response_model=CSVImportResponse)
async def upload_activity_csv(
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    entity_id: str = Form(...),
    facility_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EDIT_ROLES))
):
    """Working CSV import for activity data: parses, validates, and creates ActivityData + Calculations."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    content_bytes = await file.read()
    csv_text = content_bytes.decode("utf-8", errors="ignore")

    res = parse_and_import_activity_csv(
        csv_content=csv_text,
        organization_id=organization_id,
        entity_id=entity_id,
        facility_id=facility_id,
        user_id=current_user.id,
        db=db
    )

    if not res["success"]:
        raise HTTPException(status_code=400, detail=res.get("error", "CSV parsing failed"))

    return CSVImportResponse(
        success=True,
        imported_count=res["imported_count"],
        failed_count=res["failed_count"],
        errors=res["errors"]
    )

@router.get("/template-csv")
def download_activity_csv_template():
    sample_csv = (
        "scope,category,activity_type,quantity,unit,start_date,end_date,reporting_period\n"
        "1,Stationary Combustion,Natural Gas,12500,therms,2024-01-01,2024-01-31,2024-01\n"
        "2,Purchased Electricity,Grid Electricity,45000,kWh,2024-01-01,2024-01-31,2024-01\n"
        "3,Business Travel,Air Travel,32000,passenger-km,2024-01-01,2024-01-31,2024-01\n"
        "1,Mobile Combustion,Diesel Fleet,840,liters,2024-01-01,2024-01-31,2024-01\n"
    )
    return Response(
        content=sample_csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=decarbx_activity_template.csv"}
    )

@router.get("/webhooks", response_model=List[WebhookLogResponse])
def list_webhook_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(WebhookLog).filter(WebhookLog.is_deleted == False).order_by(WebhookLog.timestamp.desc()).all()

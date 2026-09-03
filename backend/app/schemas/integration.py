from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class ConnectorConfigBase(BaseModel):
    name: str
    connector_type: str
    status: str = "active"
    last_sync: Optional[datetime] = None
    records_synced: int = 0
    error_message: Optional[str] = None
    sync_frequency: str = "Daily at 02:00 UTC"

class ConnectorConfigResponse(ConnectorConfigBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class WebhookLogResponse(BaseModel):
    id: str
    event_type: str
    source: str
    status: str
    payload_preview: str
    timestamp: datetime
    class Config:
        from_attributes = True

class CSVImportResponse(BaseModel):
    success: bool
    imported_count: int
    failed_count: int
    errors: List[str]

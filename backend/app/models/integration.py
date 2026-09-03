from sqlalchemy import Column, String, Integer, Text, JSON, DateTime
from app.db import Base
from app.models.base import AuditBaseMixin, utc_now

class ConnectorConfig(Base, AuditBaseMixin):
    __tablename__ = "connector_configs"

    name = Column(String(100), nullable=False) # SAP S/4HANA, Oracle ERP Cloud, Utility EDI, Schneider IoT Meter, Geotab Fleet
    connector_type = Column(String(50), nullable=False) # ERP, Utility, SmartMeter, Telematics, Travel
    status = Column(String(30), default="active", nullable=False) # active, error, idle
    last_sync = Column(DateTime, nullable=True)
    records_synced = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    sync_frequency = Column(String(50), default="Daily at 02:00 UTC", nullable=False)

class WebhookLog(Base, AuditBaseMixin):
    __tablename__ = "webhook_logs"

    event_type = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False) # e.g. "Utility Provider EDI", "Smart Meter MQTT"
    status = Column(String(30), default="success", nullable=False) # success, failed, pending
    payload_preview = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

class ImportBatch(Base, AuditBaseMixin):
    __tablename__ = "import_batches"

    file_name = Column(String(255), nullable=False)
    imported_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="completed", nullable=False) # completed, failed, processing
    errors_json = Column(JSON, default=list, nullable=False)

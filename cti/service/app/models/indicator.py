import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class CtiIndicator(Base):
    __tablename__ = "cti_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=False, index=True)
    confidence = Column(Integer, default=0)
    pattern = Column(Text, nullable=True)
    labels = Column(Text, nullable=True)  # JSON array stored as text
    metadata_json = Column("metadata", Text, nullable=True)  # JSON object stored as text
    severity = Column(String(20), nullable=True, index=True)
    cwe_id = Column(String(20), nullable=True, index=True)
    owasp_category = Column(String(20), nullable=True)
    port = Column(Integer, nullable=True)
    protocol = Column(String(10), nullable=True)
    service_name = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    url = Column(Text, nullable=True)
    ecosystem = Column(String(50), nullable=True)
    package_name = Column(String(256), nullable=True)
    package_version = Column(String(100), nullable=True)
    vuln_id = Column(String(50), nullable=True)
    cvss_score = Column(Float, nullable=True)
    check_id = Column(String(256), nullable=True)
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

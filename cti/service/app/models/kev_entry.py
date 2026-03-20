import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class CtiKevEntry(Base):
    __tablename__ = "cti_kev_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_id = Column(String(20), unique=True, index=True, nullable=False)
    vendor = Column(String(256), nullable=True)
    product = Column(String(256), nullable=True)
    vulnerability_name = Column(String(512), nullable=True)
    date_added = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    known_ransomware = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

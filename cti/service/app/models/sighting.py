import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class CtiSighting(Base):
    __tablename__ = "cti_sightings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("cti_indicators.id", ondelete="CASCADE"), nullable=True)
    source = Column(String(50), nullable=False, index=True)
    count = Column(Integer, default=1)
    severity = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)
    metadata_json = Column("metadata", Text, nullable=True)
    observed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

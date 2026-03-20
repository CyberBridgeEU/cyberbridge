import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class CtiThreatFeed(Base):
    __tablename__ = "cti_threat_feeds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_name = Column(String(50), unique=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(20), nullable=True)
    record_count = Column(Integer, default=0)

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class CtiAttackPattern(Base):
    __tablename__ = "cti_attack_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mitre_id = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(256), nullable=False)
    tactic = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

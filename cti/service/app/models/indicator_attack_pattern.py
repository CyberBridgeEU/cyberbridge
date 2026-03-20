from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class CtiIndicatorAttackPattern(Base):
    __tablename__ = "cti_indicator_attack_patterns"

    indicator_id = Column(UUID(as_uuid=True), ForeignKey("cti_indicators.id", ondelete="CASCADE"), primary_key=True)
    attack_pattern_id = Column(UUID(as_uuid=True), ForeignKey("cti_attack_patterns.id", ondelete="CASCADE"), primary_key=True)
    source = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

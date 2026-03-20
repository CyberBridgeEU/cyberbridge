from sqlalchemy.orm import Session

from ..repositories.indicator_repository import IndicatorRepository


def get_timeline(db: Session, days: int = 7) -> list[dict]:
    return IndicatorRepository.get_timeline_data(db, days)

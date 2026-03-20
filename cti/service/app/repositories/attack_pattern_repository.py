from sqlalchemy.orm import Session

from ..models.attack_pattern import CtiAttackPattern


class AttackPatternRepository:

    @staticmethod
    def get_by_mitre_id(db: Session, mitre_id: str) -> CtiAttackPattern | None:
        return db.query(CtiAttackPattern).filter(CtiAttackPattern.mitre_id == mitre_id).first()

    @staticmethod
    def get_all(db: Session) -> list[CtiAttackPattern]:
        return db.query(CtiAttackPattern).order_by(CtiAttackPattern.created_at.desc()).all()

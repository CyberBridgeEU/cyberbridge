# user_sessions_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
import uuid
from app.models import models
from typing import Optional


def create_user_session(db: Session, user_id: uuid.UUID, email: str):
    """Create a new user session when user logs in"""
    db_session = models.UserSessions(
        user_id=user_id,
        email=email,
        login_timestamp=func.now()
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_user_session_logout(db: Session, session_id: uuid.UUID):
    """Update session with logout timestamp"""
    db_session = db.query(models.UserSessions).filter(models.UserSessions.id == session_id).first()
    if db_session:
        db_session.logout_timestamp = func.now()
        db.commit()
        db.refresh(db_session)
    return db_session


def get_latest_user_session(db: Session, user_id: uuid.UUID):
    """Get the most recent session for a user"""
    return db.query(models.UserSessions).filter(
        models.UserSessions.user_id == user_id
    ).order_by(models.UserSessions.login_timestamp.desc()).first()


def get_all_user_sessions(db: Session, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
    """Get all user sessions with optional date filtering"""
    query = db.query(models.UserSessions).order_by(models.UserSessions.login_timestamp.desc())

    if from_date:
        query = query.filter(models.UserSessions.login_timestamp >= from_date)
    if to_date:
        query = query.filter(models.UserSessions.login_timestamp <= to_date)

    return query.all()


def get_visits_per_email(db: Session, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
    """Get total visits (sessions) per email with optional date filtering"""
    query = db.query(
        models.UserSessions.email,
        func.count(models.UserSessions.id).label('visit_count')
    ).group_by(models.UserSessions.email)

    if from_date:
        query = query.filter(models.UserSessions.login_timestamp >= from_date)
    if to_date:
        query = query.filter(models.UserSessions.login_timestamp <= to_date)

    return query.all()


def get_total_visits(db: Session, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
    """Get total number of visits (sessions) with optional date filtering"""
    query = db.query(func.count(models.UserSessions.id))

    if from_date:
        query = query.filter(models.UserSessions.login_timestamp >= from_date)
    if to_date:
        query = query.filter(models.UserSessions.login_timestamp <= to_date)

    return query.scalar()


def delete_all_user_sessions(db: Session):
    """Delete all user sessions from the database"""
    try:
        deleted_count = db.query(models.UserSessions).delete()
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        raise e

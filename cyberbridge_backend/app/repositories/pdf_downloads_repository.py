# pdf_downloads_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import uuid
from app.models import models
from typing import Optional


def create_pdf_download(db: Session, user_id: uuid.UUID, email: str, pdf_type: str):
    """Create a new PDF download record"""
    db_download = models.PdfDownloads(
        user_id=user_id,
        email=email,
        pdf_type=pdf_type,
        download_timestamp=datetime.now()
    )
    db.add(db_download)
    db.commit()
    db.refresh(db_download)
    return db_download


def get_all_pdf_downloads(db: Session, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
    """Get all PDF downloads with optional date filtering"""
    query = db.query(models.PdfDownloads).order_by(models.PdfDownloads.download_timestamp.desc())

    if from_date:
        query = query.filter(models.PdfDownloads.download_timestamp >= from_date)
    if to_date:
        query = query.filter(models.PdfDownloads.download_timestamp <= to_date)

    return query.all()


def get_downloads_per_email(db: Session, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
    """Get total PDF downloads per email with optional date filtering"""
    query = db.query(
        models.PdfDownloads.email,
        func.count(models.PdfDownloads.id).label('download_count')
    ).group_by(models.PdfDownloads.email)

    if from_date:
        query = query.filter(models.PdfDownloads.download_timestamp >= from_date)
    if to_date:
        query = query.filter(models.PdfDownloads.download_timestamp <= to_date)

    return query.all()


def get_downloads_per_type(db: Session, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
    """Get total PDF downloads per type with optional date filtering"""
    query = db.query(
        models.PdfDownloads.pdf_type,
        func.count(models.PdfDownloads.id).label('download_count')
    ).group_by(models.PdfDownloads.pdf_type)

    if from_date:
        query = query.filter(models.PdfDownloads.download_timestamp >= from_date)
    if to_date:
        query = query.filter(models.PdfDownloads.download_timestamp <= to_date)

    return query.all()


def get_total_pdf_downloads(db: Session, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
    """Get total number of PDF downloads with optional date filtering"""
    query = db.query(func.count(models.PdfDownloads.id))

    if from_date:
        query = query.filter(models.PdfDownloads.download_timestamp >= from_date)
    if to_date:
        query = query.filter(models.PdfDownloads.download_timestamp <= to_date)

    return query.scalar()


def delete_all_pdf_downloads(db: Session):
    """Delete all PDF downloads from the database"""
    try:
        deleted_count = db.query(models.PdfDownloads).delete()
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        raise e

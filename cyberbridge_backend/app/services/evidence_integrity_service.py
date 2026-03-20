# services/evidence_integrity_service.py
import hashlib
import os
import uuid
from datetime import datetime
from typing import Optional, BinaryIO
from sqlalchemy.orm import Session
from io import BytesIO

from app.models import models

CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def calculate_file_hashes(file_path: str) -> dict:
    """
    Calculate SHA-256 and MD5 hashes for a file.
    Returns dict with sha256_hash, md5_hash, and file_size.
    """
    sha256_hasher = hashlib.sha256()
    md5_hasher = hashlib.md5()
    file_size = 0

    with open(file_path, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256_hasher.update(chunk)
            md5_hasher.update(chunk)
            file_size += len(chunk)

    return {
        'sha256_hash': sha256_hasher.hexdigest(),
        'md5_hash': md5_hasher.hexdigest(),
        'file_size': file_size
    }


def calculate_stream_hashes(file_stream: BinaryIO) -> dict:
    """
    Calculate SHA-256 and MD5 hashes for a file stream.
    Returns dict with sha256_hash, md5_hash, and file_size.
    """
    sha256_hasher = hashlib.sha256()
    md5_hasher = hashlib.md5()
    file_size = 0

    # Reset stream position
    file_stream.seek(0)

    while chunk := file_stream.read(CHUNK_SIZE):
        sha256_hasher.update(chunk)
        md5_hasher.update(chunk)
        file_size += len(chunk)

    # Reset stream position for subsequent use
    file_stream.seek(0)

    return {
        'sha256_hash': sha256_hasher.hexdigest(),
        'md5_hash': md5_hasher.hexdigest(),
        'file_size': file_size
    }


def create_integrity_record(
    db: Session,
    evidence_id: uuid.UUID,
    file_path: str,
    original_filename: str,
    uploaded_by_id: Optional[uuid.UUID] = None
) -> models.EvidenceIntegrity:
    """
    Create an integrity record for a new evidence file.
    Calculates hashes and creates the database record.
    """
    # Calculate hashes
    hashes = calculate_file_hashes(file_path)

    # Get current version (if any exists)
    existing = db.query(models.EvidenceIntegrity).filter(
        models.EvidenceIntegrity.evidence_id == evidence_id
    ).order_by(models.EvidenceIntegrity.version.desc()).first()

    version = 1
    previous_version_id = None

    if existing:
        version = existing.version + 1
        previous_version_id = existing.id

    # Create new integrity record
    integrity = models.EvidenceIntegrity(
        id=uuid.uuid4(),
        evidence_id=evidence_id,
        version=version,
        sha256_hash=hashes['sha256_hash'],
        md5_hash=hashes['md5_hash'],
        file_size=hashes['file_size'],
        original_filename=original_filename,
        uploaded_by_id=uploaded_by_id,
        uploaded_at=datetime.utcnow(),
        previous_version_id=previous_version_id,
        verification_status='valid'
    )

    db.add(integrity)
    db.commit()
    db.refresh(integrity)

    return integrity


def verify_file_integrity(
    db: Session,
    evidence_id: uuid.UUID,
    file_path: str
) -> dict:
    """
    Verify that a file's current hash matches the stored integrity record.
    Returns verification result with status.
    """
    # Get latest integrity record
    integrity = db.query(models.EvidenceIntegrity).filter(
        models.EvidenceIntegrity.evidence_id == evidence_id
    ).order_by(models.EvidenceIntegrity.version.desc()).first()

    if not integrity:
        return {
            'status': 'no_record',
            'message': 'No integrity record found for this evidence',
            'verified': False
        }

    # Check if file exists
    if not os.path.exists(file_path):
        integrity.verification_status = 'missing'
        integrity.last_verified_at = datetime.utcnow()
        db.commit()

        return {
            'status': 'missing',
            'message': 'Evidence file not found',
            'verified': False
        }

    # Calculate current hashes
    current_hashes = calculate_file_hashes(file_path)

    # Compare hashes
    sha256_match = current_hashes['sha256_hash'] == integrity.sha256_hash
    size_match = current_hashes['file_size'] == integrity.file_size

    if sha256_match and size_match:
        integrity.verification_status = 'valid'
        integrity.last_verified_at = datetime.utcnow()
        db.commit()

        return {
            'status': 'valid',
            'message': 'File integrity verified',
            'verified': True,
            'sha256_hash': integrity.sha256_hash,
            'file_size': integrity.file_size
        }
    else:
        integrity.verification_status = 'corrupted'
        integrity.last_verified_at = datetime.utcnow()
        db.commit()

        return {
            'status': 'corrupted',
            'message': 'File has been modified since upload',
            'verified': False,
            'expected_sha256': integrity.sha256_hash,
            'actual_sha256': current_hashes['sha256_hash'],
            'expected_size': integrity.file_size,
            'actual_size': current_hashes['file_size']
        }


def get_integrity_info(db: Session, evidence_id: uuid.UUID) -> Optional[dict]:
    """
    Get integrity information for an evidence file.
    """
    integrity = db.query(models.EvidenceIntegrity).filter(
        models.EvidenceIntegrity.evidence_id == evidence_id
    ).order_by(models.EvidenceIntegrity.version.desc()).first()

    if not integrity:
        return None

    # Get uploader name
    uploader_name = None
    if integrity.uploaded_by_id:
        user = db.query(models.User).filter(models.User.id == integrity.uploaded_by_id).first()
        uploader_name = user.name if user else None

    return {
        'id': str(integrity.id),
        'evidence_id': str(integrity.evidence_id),
        'version': integrity.version,
        'sha256_hash': integrity.sha256_hash,
        'md5_hash': integrity.md5_hash,
        'file_size': integrity.file_size,
        'original_filename': integrity.original_filename,
        'uploaded_by_id': str(integrity.uploaded_by_id) if integrity.uploaded_by_id else None,
        'uploaded_by_name': uploader_name,
        'uploaded_at': integrity.uploaded_at.isoformat() if integrity.uploaded_at else None,
        'last_verified_at': integrity.last_verified_at.isoformat() if integrity.last_verified_at else None,
        'verification_status': integrity.verification_status,
        'previous_version_id': str(integrity.previous_version_id) if integrity.previous_version_id else None
    }


def get_version_history(db: Session, evidence_id: uuid.UUID) -> list:
    """
    Get complete version history for an evidence file.
    """
    versions = db.query(models.EvidenceIntegrity).filter(
        models.EvidenceIntegrity.evidence_id == evidence_id
    ).order_by(models.EvidenceIntegrity.version.desc()).all()

    history = []
    for v in versions:
        # Get uploader name
        uploader_name = None
        if v.uploaded_by_id:
            user = db.query(models.User).filter(models.User.id == v.uploaded_by_id).first()
            uploader_name = user.name if user else None

        history.append({
            'id': str(v.id),
            'version': v.version,
            'sha256_hash': v.sha256_hash,
            'md5_hash': v.md5_hash,
            'file_size': v.file_size,
            'original_filename': v.original_filename,
            'uploaded_by_id': str(v.uploaded_by_id) if v.uploaded_by_id else None,
            'uploaded_by_name': uploader_name,
            'uploaded_at': v.uploaded_at.isoformat() if v.uploaded_at else None,
            'verification_status': v.verification_status
        })

    return history


def generate_integrity_receipt(db: Session, evidence_id: uuid.UUID) -> Optional[BytesIO]:
    """
    Generate a PDF integrity receipt for an evidence file.
    Contains file metadata, hash values, and verification timestamp.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    # Get integrity info
    integrity = db.query(models.EvidenceIntegrity).filter(
        models.EvidenceIntegrity.evidence_id == evidence_id
    ).order_by(models.EvidenceIntegrity.version.desc()).first()

    if not integrity:
        return None

    # Get evidence details
    evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not evidence:
        return None

    # Get uploader name
    uploader_name = "Unknown"
    if integrity.uploaded_by_id:
        user = db.query(models.User).filter(models.User.id == integrity.uploaded_by_id).first()
        if user:
            uploader_name = user.name

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20
    )
    normal_style = styles['Normal']

    elements = []

    # Title
    elements.append(Paragraph("Evidence Integrity Receipt", title_style))
    elements.append(Spacer(1, 10*mm))

    # Receipt metadata
    receipt_data = [
        ["Receipt Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
        ["Receipt ID:", str(uuid.uuid4())[:8].upper()]
    ]
    receipt_table = Table(receipt_data, colWidths=[50*mm, 100*mm])
    receipt_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
    ]))
    elements.append(receipt_table)
    elements.append(Spacer(1, 10*mm))

    # File information
    elements.append(Paragraph("File Information", styles['Heading2']))
    file_data = [
        ["Filename:", integrity.original_filename],
        ["File Size:", f"{integrity.file_size:,} bytes"],
        ["File Type:", evidence.file_type],
        ["Version:", str(integrity.version)],
        ["Uploaded By:", uploader_name],
        ["Upload Date:", integrity.uploaded_at.strftime("%Y-%m-%d %H:%M:%S UTC") if integrity.uploaded_at else "N/A"]
    ]
    file_table = Table(file_data, colWidths=[40*mm, 110*mm])
    file_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(file_table)
    elements.append(Spacer(1, 10*mm))

    # Hash values
    elements.append(Paragraph("Integrity Checksums", styles['Heading2']))
    hash_data = [
        ["SHA-256:", integrity.sha256_hash],
        ["MD5:", integrity.md5_hash or "N/A"]
    ]
    hash_table = Table(hash_data, colWidths=[30*mm, 120*mm])
    hash_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (1, 0), (1, -1), 'Courier'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(hash_table)
    elements.append(Spacer(1, 10*mm))

    # Verification status
    elements.append(Paragraph("Verification Status", styles['Heading2']))
    status = integrity.verification_status or "Not verified"
    status_color = colors.green if status == 'valid' else colors.red if status in ['corrupted', 'missing'] else colors.grey
    status_data = [
        ["Status:", status.upper()],
        ["Last Verified:", integrity.last_verified_at.strftime("%Y-%m-%d %H:%M:%S UTC") if integrity.last_verified_at else "Never"]
    ]
    status_table = Table(status_data, colWidths=[40*mm, 110*mm])
    status_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (1, 0), (1, 0), status_color),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 15*mm))

    # Footer note
    footer_text = """
    This receipt certifies the integrity of the referenced evidence file at the time of upload.
    The SHA-256 hash can be used to verify that the file has not been modified.
    To verify: compare the current file's SHA-256 hash against the value shown above.
    """
    elements.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=normal_style,
        fontSize=8,
        textColor=colors.grey
    )))

    doc.build(elements)
    buffer.seek(0)
    return buffer

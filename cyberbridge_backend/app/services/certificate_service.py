# certificate_service.py
import hashlib
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from sqlalchemy.orm import Session

from app.models import models
from app.repositories import gap_analysis_repository, certificate_repository
from app.services import digital_signature_service


# Framework name to abbreviation mapping
FRAMEWORK_ABBREVIATIONS = {
    "cra": "CRA",
    "cyber resilience act": "CRA",
    "nis2": "NIS2",
    "nis 2": "NIS2",
    "nist": "NIST",
    "iso 27001": "ISO27001",
    "iso27001": "ISO27001",
}


def _get_abbreviation(framework_name: str) -> str:
    lower = framework_name.lower()
    for key, abbr in FRAMEWORK_ABBREVIATIONS.items():
        if key in lower:
            return abbr
    # Fallback: first 3 uppercase chars of alphabetic characters
    alpha = "".join(c for c in framework_name if c.isalpha())
    return alpha[:3].upper() or "GEN"


def _compute_verification_hash(cert_number: str, framework_id, org_id, issued_at: datetime) -> str:
    raw = f"{cert_number}:{framework_id}:{org_id}:{issued_at.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_certificate(db: Session, current_user, framework_id: uuid.UUID) -> models.ComplianceCertificate:
    """Validate 100% score, generate certificate with PDF, and persist."""
    # 1. Get gap analysis data for this specific framework
    gap_data = gap_analysis_repository.get_gap_analysis(db, current_user, framework_id)

    overall_score = gap_data["summary"]["overall_compliance_score"]
    if overall_score < 100:
        raise ValueError(
            f"Overall compliance score is {overall_score}%. A score of 100% is required to generate a certificate."
        )

    # 2. Get framework and organisation info
    framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
    if not framework:
        raise ValueError("Framework not found.")

    organisation = db.query(models.Organisations).filter(
        models.Organisations.id == current_user.organisation_id
    ).first()
    if not organisation:
        raise ValueError("Organisation not found.")

    # 3. Extract score components
    obj_analysis = gap_data["objectives_analysis"]
    applicable = obj_analysis["total"] - obj_analysis["not_applicable"]
    objectives_pct = round((obj_analysis["compliant"] / applicable * 100), 1) if applicable > 0 else 0

    assess_analysis = gap_data["assessment_analysis"]
    assessments_pct = assess_analysis["completion_rate"]

    policy_analysis = gap_data["policy_analysis"]
    policies_pct = policy_analysis["approved_percentage"]

    # 4. Generate certificate number
    abbreviation = _get_abbreviation(framework.name)
    year = datetime.utcnow().year
    cert_number = certificate_repository.generate_next_certificate_number(db, abbreviation, year)

    # 5. Compute dates and hash
    issued_at = datetime.utcnow()
    expires_at = issued_at + timedelta(days=365)
    verification_hash = _compute_verification_hash(cert_number, framework_id, current_user.organisation_id, issued_at)

    # 6. Create DB record (without PDF first)
    cert_data = {
        "certificate_number": cert_number,
        "framework_id": framework_id,
        "organisation_id": current_user.organisation_id,
        "issued_by_user_id": current_user.id,
        "overall_score": overall_score,
        "objectives_compliant_pct": objectives_pct,
        "assessments_completed_pct": assessments_pct,
        "policies_approved_pct": policies_pct,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "verification_hash": verification_hash,
    }
    cert = certificate_repository.create_certificate(db, cert_data)

    # 7. Sign the certificate
    payload = digital_signature_service.certificate_payload(cert)
    signature_hex, signing_key_id = digital_signature_service.sign_payload(
        payload, current_user.organisation_id, db
    )
    cert.signature = signature_hex
    cert.signing_key_id = signing_key_id
    db.commit()

    # 8. Generate PDF and save (includes signature in footer)
    pdf_buffer = _generate_certificate_pdf(
        cert_number=cert_number,
        organisation_name=organisation.name,
        framework_name=framework.name,
        overall_score=overall_score,
        objectives_pct=objectives_pct,
        assessments_pct=assessments_pct,
        policies_pct=policies_pct,
        issued_at=issued_at,
        expires_at=expires_at,
        verification_hash=verification_hash,
        signature_hex=signature_hex,
    )
    cert.pdf_data = pdf_buffer.getvalue()
    db.commit()
    db.refresh(cert)

    return cert


def _generate_certificate_pdf(
    cert_number: str,
    organisation_name: str,
    framework_name: str,
    overall_score: float,
    objectives_pct: float,
    assessments_pct: float,
    policies_pct: float,
    issued_at: datetime,
    expires_at: datetime,
    verification_hash: str,
    signature_hex: str = None,
) -> BytesIO:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER

    buffer = BytesIO()
    page = landscape(A4)
    doc = SimpleDocTemplate(buffer, pagesize=page, topMargin=15 * mm, bottomMargin=15 * mm)

    styles = getSampleStyleSheet()
    center_title = ParagraphStyle(
        "CertTitle", parent=styles["Title"], fontSize=28, alignment=TA_CENTER,
        textColor=colors.HexColor("#0f386a"), spaceAfter=6
    )
    center_sub = ParagraphStyle(
        "CertSub", parent=styles["Normal"], fontSize=14, alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"), spaceAfter=20
    )
    center_org = ParagraphStyle(
        "CertOrg", parent=styles["Heading1"], fontSize=22, alignment=TA_CENTER,
        textColor=colors.HexColor("#1a365d"), spaceBefore=10, spaceAfter=6
    )
    center_fw = ParagraphStyle(
        "CertFw", parent=styles["Heading2"], fontSize=16, alignment=TA_CENTER,
        textColor=colors.HexColor("#0f386a"), spaceAfter=20
    )
    center_normal = ParagraphStyle(
        "CertNormal", parent=styles["Normal"], fontSize=11, alignment=TA_CENTER,
        textColor=colors.HexColor("#666666")
    )
    center_small = ParagraphStyle(
        "CertSmall", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER,
        textColor=colors.HexColor("#999999")
    )

    elements = []

    # Border decoration
    elements.append(Spacer(1, 10 * mm))

    # Title
    elements.append(Paragraph("COMPLIANCE CERTIFICATE", center_title))
    elements.append(Paragraph("Self-Assessment Declaration of Conformity", center_sub))

    # Divider line via a thin table
    divider = Table([[""]],colWidths=[200 * mm])
    divider.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, colors.HexColor("#0f386a")),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 8 * mm))

    # Organisation and framework
    elements.append(Paragraph("This certifies that", center_normal))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(organisation_name, center_org))
    elements.append(Paragraph(
        f"has achieved <b>100% compliance</b> under the <b>{framework_name}</b> framework",
        center_normal
    ))
    elements.append(Spacer(1, 8 * mm))

    # Score breakdown table
    score_data = [
        ["Component", "Score"],
        ["Objectives Compliance", f"{objectives_pct:.1f}%"],
        ["Assessments Completed", f"{assessments_pct:.1f}%"],
        ["Policies Approved", f"{policies_pct:.1f}%"],
        ["Overall Weighted Score", f"{overall_score:.0f}%"],
    ]
    score_table = Table(score_data, colWidths=[120 * mm, 60 * mm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f386a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f7ff")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 8 * mm))

    # Certificate details
    details = [
        ["Certificate Number:", cert_number],
        ["Date Issued:", issued_at.strftime("%B %d, %Y")],
        ["Valid Until:", expires_at.strftime("%B %d, %Y")],
    ]
    details_table = Table(details, colWidths=[80 * mm, 100 * mm])
    details_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#888888")),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 6 * mm))

    # Verification hash
    elements.append(Paragraph(f"Verification Hash: {verification_hash}", center_small))
    elements.append(Spacer(1, 3 * mm))

    # Digital signature footer
    if signature_hex:
        sig_preview = f"{signature_hex[:32]}...{signature_hex[-16:]}"
        elements.append(Paragraph(
            f"Digital Signature (RSA-2048-SHA256): {sig_preview}",
            center_small
        ))
        elements.append(Spacer(1, 2 * mm))

    elements.append(Paragraph(
        "This certificate was generated by CyberBridge Compliance Platform. "
        "Verify authenticity at /certificates/verify/&lt;hash&gt;",
        center_small
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer

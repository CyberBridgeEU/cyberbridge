# submission_service.py
import json
import os
import uuid
import zipfile
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import Session

from app.models import models
from app.repositories import submission_repository, certificate_repository, gap_analysis_repository

logger = logging.getLogger(__name__)

EVIDENCE_BASE_PATH = os.getenv("UPLOAD_PATH", "/app/uploads")


def create_and_send_submission(
    db: Session,
    current_user,
    authority_name: str,
    recipient_emails: list,
    attachment_types: list = None,
    certificate_id: uuid.UUID = None,
    framework_id: uuid.UUID = None,
    subject: str = None,
    body: str = None,
) -> models.CertificateSubmission:
    """Create a submission record, build attachments, and attempt to send via email."""
    attachment_types = attachment_types or []

    # Resolve certificate if provided
    cert = None
    if certificate_id:
        cert = certificate_repository.get_certificate_by_id(db, certificate_id)
        if not cert:
            raise ValueError("Certificate not found")
        if cert.organisation_id != current_user.organisation_id and current_user.role_name != "super_admin":
            raise ValueError("Access denied")
        if not framework_id:
            framework_id = cert.framework_id

    # Get org and framework info
    organisation = db.query(models.Organisations).filter(
        models.Organisations.id == current_user.organisation_id
    ).first()
    org_name = organisation.name if organisation else "Unknown"

    framework = None
    framework_name = "All Frameworks"
    if framework_id:
        framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
        framework_name = framework.name if framework else "Unknown"

    # Default subject/body
    if not subject:
        parts = [f"Regulatory Submission - {org_name}"]
        if framework_name != "All Frameworks":
            parts.append(f"- {framework_name}")
        if cert:
            parts.append(f"({cert.certificate_number})")
        subject = " ".join(parts)

    if not body:
        body_lines = [
            f"Dear {authority_name},\n",
            f"Please find attached the compliance documentation for:\n",
            f"Organisation: {org_name}",
            f"Framework: {framework_name}",
        ]
        if cert:
            body_lines.extend([
                f"Certificate Number: {cert.certificate_number}",
                f"Overall Compliance Score: {cert.overall_score:.0f}%",
                f"Verification Hash: {cert.verification_hash}",
            ])
        attachment_labels = {
            "certificate": "Compliance Certificate (PDF)",
            "gap_analysis": "Gap Analysis Report (PDF)",
            "evidence_bundle": "Evidence Files (ZIP)",
            "policies": "Policy Documents (PDF)",
        }
        if attachment_types:
            body_lines.append(f"\nAttachments included:")
            for at in attachment_types:
                body_lines.append(f"  - {attachment_labels.get(at, at)}")
        body_lines.extend([
            f"\nThis submission was prepared by the CyberBridge Compliance Platform.",
            f"\nBest regards,",
            f"{current_user.name}",
            org_name,
        ])
        body = "\n".join(body_lines)

    # Create submission record
    sub_data = {
        "certificate_id": certificate_id,
        "framework_id": framework_id,
        "organisation_id": current_user.organisation_id,
        "submitted_by_user_id": current_user.id,
        "authority_name": authority_name,
        "recipient_emails": json.dumps(recipient_emails),
        "attachment_types": json.dumps(attachment_types),
        "submission_method": "email",
        "status": "draft",
        "subject": subject,
        "body": body,
    }
    submission = submission_repository.create_submission(db, sub_data)

    # Build attachments
    attachments = _build_attachments(db, current_user, attachment_types, cert, framework_id)

    # Attempt to send email
    email_sent = _send_submission_email(
        recipient_emails=recipient_emails,
        subject=subject,
        body=body,
        attachments=attachments,
    )

    if email_sent:
        submission_repository.update_submission_status(db, submission.id, "sent", datetime.utcnow())
    else:
        logger.warning(f"Email sending failed for submission {submission.id}, marked as draft")

    db.refresh(submission)
    return submission


def _build_attachments(db, current_user, attachment_types, cert, framework_id):
    """Build list of (filename, content_type, data) tuples."""
    attachments = []

    for at in attachment_types:
        try:
            if at == "certificate" and cert and cert.pdf_data:
                attachments.append((f"{cert.certificate_number}.pdf", "application/pdf", cert.pdf_data))

            elif at == "gap_analysis":
                pdf_data = _generate_gap_analysis_pdf(db, current_user, framework_id)
                if pdf_data:
                    attachments.append(("gap_analysis_report.pdf", "application/pdf", pdf_data))

            elif at == "evidence_bundle":
                zip_data = _generate_evidence_bundle(db, current_user, framework_id)
                if zip_data:
                    attachments.append(("evidence_bundle.zip", "application/zip", zip_data))

            elif at == "policies":
                pdf_data = _generate_policies_pdf(db, current_user, framework_id)
                if pdf_data:
                    attachments.append(("policies_report.pdf", "application/pdf", pdf_data))
        except Exception as e:
            logger.error(f"Failed to build attachment '{at}': {e}")

    return attachments


def _generate_gap_analysis_pdf(db, current_user, framework_id):
    """Generate a gap analysis summary PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    gap_data = gap_analysis_repository.get_gap_analysis(db, current_user, framework_id)
    summary = gap_data["summary"]
    obj = gap_data["objectives_analysis"]
    assess = gap_data["assessment_analysis"]
    policy = gap_data["policy_analysis"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6)

    elements = []
    elements.append(Paragraph("Gap Analysis Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 8 * mm))

    # Summary table
    elements.append(Paragraph("Compliance Summary", h2))
    summary_data = [
        ["Metric", "Value"],
        ["Overall Compliance Score", f"{summary['overall_compliance_score']}%"],
        ["Total Objectives", str(summary["total_objectives"])],
        ["Total Assessments", str(summary["total_assessments"])],
        ["Total Policies", str(summary["total_policies"])],
    ]
    t = Table(summary_data, colWidths=[100 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f386a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))

    # Objectives breakdown
    elements.append(Paragraph("Objectives Analysis", h2))
    obj_data = [
        ["Status", "Count"],
        ["Compliant", str(obj["compliant"])],
        ["Partially Compliant", str(obj["partially_compliant"])],
        ["Not Compliant", str(obj["not_compliant"])],
        ["In Review", str(obj["in_review"])],
        ["Not Assessed", str(obj["not_assessed"])],
        ["Not Applicable", str(obj["not_applicable"])],
        ["With Evidence", str(obj["with_evidence"])],
        ["Without Evidence", str(obj["without_evidence"])],
    ]
    t2 = Table(obj_data, colWidths=[100 * mm, 60 * mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f386a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 6 * mm))

    # Assessment progress
    elements.append(Paragraph("Assessment Progress", h2))
    elements.append(Paragraph(
        f"Completed: {assess['completed']}/{assess['total']} ({assess['completion_rate']}%)",
        styles["Normal"]
    ))

    # Policy status
    elements.append(Paragraph("Policy Analysis", h2))
    elements.append(Paragraph(
        f"Approved: {policy['approved_count']}/{policy['total']} ({policy['approved_percentage']}%)",
        styles["Normal"]
    ))

    # Chapter breakdown
    if gap_data["chapter_breakdown"]:
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph("Chapter Breakdown", h2))
        ch_data = [["Chapter", "Total", "Compliant", "Rate"]]
        for ch in gap_data["chapter_breakdown"]:
            ch_data.append([ch["chapter_title"], str(ch["total_objectives"]), str(ch["compliant"]), f"{ch['compliance_rate']}%"])
        t3 = Table(ch_data, colWidths=[80 * mm, 25 * mm, 30 * mm, 25 * mm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f386a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t3)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _generate_evidence_bundle(db, current_user, framework_id):
    """Generate a ZIP of all evidence files for the org's frameworks."""
    # Get framework IDs
    fw_query = db.query(models.Framework).filter(
        models.Framework.organisation_id == current_user.organisation_id
    )
    if framework_id:
        fw_query = fw_query.filter(models.Framework.id == framework_id)
    frameworks = fw_query.all()
    framework_ids = [f.id for f in frameworks]
    if not framework_ids:
        return None

    # Get chapters → objectives → evidence
    chapters = db.query(models.Chapters).filter(models.Chapters.framework_id.in_(framework_ids)).all()
    chapter_ids = [c.id for c in chapters]
    objectives = db.query(models.Objectives).filter(
        models.Objectives.chapter_id.in_(chapter_ids),
        models.Objectives.scope_entity_id.is_(None)
    ).all() if chapter_ids else []

    # Get assessment evidence
    assessments = db.query(models.Assessment).filter(
        models.Assessment.framework_id.in_(framework_ids)
    ).all()
    answer_ids = []
    for assessment in assessments:
        answers = db.query(models.Answer.id).filter(models.Answer.assessment_id == assessment.id).all()
        answer_ids.extend([a.id for a in answers])

    evidence_files = db.query(models.Evidence).filter(
        models.Evidence.answer_id.in_(answer_ids)
    ).all() if answer_ids else []

    # Build ZIP
    buffer = BytesIO()
    file_count = 0
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add assessment evidence
        for ev in evidence_files:
            file_path = os.path.join(EVIDENCE_BASE_PATH, ev.filepath) if ev.filepath else None
            if file_path and os.path.exists(file_path):
                safe_name = f"assessment_evidence/{ev.id}_{ev.filename}"
                zf.write(file_path, safe_name)
                file_count += 1

        # Add objective evidence
        for obj in objectives:
            if obj.evidence_filepath:
                file_path = os.path.join(EVIDENCE_BASE_PATH, obj.evidence_filepath)
                if os.path.exists(file_path):
                    safe_name = f"objective_evidence/{obj.id}_{obj.evidence_filename or 'file'}"
                    zf.write(file_path, safe_name)
                    file_count += 1

        # Add manifest
        manifest = {
            "generated_at": datetime.utcnow().isoformat(),
            "organisation": current_user.organisation_name if hasattr(current_user, 'organisation_name') else "Unknown",
            "frameworks": [f.name for f in frameworks],
            "assessment_evidence_count": len(evidence_files),
            "objective_evidence_count": sum(1 for o in objectives if o.evidence_filepath),
            "total_files": file_count,
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    if file_count == 0:
        return None

    buffer.seek(0)
    return buffer.getvalue()


def _generate_policies_pdf(db, current_user, framework_id):
    """Generate a PDF summarizing all policies for the org/framework."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    # Get policies
    policy_query = db.query(models.Policies).filter(
        models.Policies.organisation_id == current_user.organisation_id
    )
    if framework_id:
        policy_query = policy_query.join(
            models.PolicyFrameworks, models.Policies.id == models.PolicyFrameworks.policy_id
        ).filter(models.PolicyFrameworks.framework_id == framework_id)

    policies = policy_query.all()
    if not policies:
        return None

    # Get status map
    statuses = db.query(models.PolicyStatuses).all()
    status_map = {s.id: s.status for s in statuses}

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6)

    elements = []
    elements.append(Paragraph("Policies Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}", styles["Normal"]))
    elements.append(Paragraph(f"Total Policies: {len(policies)}", styles["Normal"]))
    elements.append(Spacer(1, 8 * mm))

    # Summary table
    policy_data = [["Policy Name", "Status", "Version"]]
    for p in policies:
        status_name = status_map.get(p.status_id, "Unknown")
        policy_data.append([p.name or "Untitled", status_name, p.version or "-"])

    t = Table(policy_data, colWidths=[90 * mm, 40 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f386a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)

    # Individual policy details
    for p in policies:
        elements.append(PageBreak())
        elements.append(Paragraph(p.name or "Untitled Policy", h2))
        status_name = status_map.get(p.status_id, "Unknown")
        elements.append(Paragraph(f"Status: {status_name} | Version: {p.version or '-'}", styles["Normal"]))
        if p.body:
            # Truncate very long bodies for PDF
            body_text = p.body[:3000] + ("..." if len(p.body) > 3000 else "")
            elements.append(Spacer(1, 4 * mm))
            elements.append(Paragraph(body_text, styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _send_submission_email(
    recipient_emails: list,
    subject: str,
    body: str,
    attachments: list,
) -> bool:
    """Send submission via SMTP with multiple attachments. Returns True if sent."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        logger.info("SMTP not configured — skipping email send")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = ", ".join(recipient_emails)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Attach all files
        for filename, content_type, data in attachments:
            subtype = content_type.split("/")[-1] if "/" in content_type else "octet-stream"
            attachment = MIMEApplication(data, _subtype=subtype)
            attachment.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(attachment)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info(f"Submission email sent to {recipient_emails} with {len(attachments)} attachments")
        return True
    except Exception as e:
        logger.error(f"Failed to send submission email: {e}")
        return False

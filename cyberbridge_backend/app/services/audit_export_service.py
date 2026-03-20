# services/audit_export_service.py
import uuid
import os
import zipfile
import json
from datetime import datetime
from typing import Optional, List
from io import BytesIO
from sqlalchemy.orm import Session

from app.models import models
from app.repositories import audit_engagement_repository, audit_finding_repository, audit_comment_repository


def generate_review_pack(db: Session, engagement_id: uuid.UUID) -> Optional[BytesIO]:
    """
    Generate a comprehensive PDF review pack for an audit engagement.
    Includes engagement summary, controls review, findings, and comments.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    # Get engagement
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        return None

    # Get related data
    findings = audit_finding_repository.get_findings_for_engagement(db, engagement_id)
    comments = audit_comment_repository.get_comments_for_engagement(db, engagement_id)
    sign_offs = audit_finding_repository.get_sign_offs_for_engagement(db, engagement_id)
    activity_logs = audit_finding_repository.get_activity_logs_for_engagement(db, engagement_id, limit=50)

    # Get assessment details if available
    assessment = None
    framework = None
    if engagement.assessment_id:
        assessment = db.query(models.Assessment).filter(models.Assessment.id == engagement.assessment_id).first()
        if assessment and assessment.framework_id:
            framework = db.query(models.Framework).filter(models.Framework.id == assessment.framework_id).first()

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, spaceAfter=20)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=10)
    h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=12, spaceBefore=10, spaceAfter=5)
    normal_style = styles['Normal']

    elements = []

    # Cover page
    elements.append(Spacer(1, 50*mm))
    elements.append(Paragraph("Audit Review Pack", title_style))
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(engagement.name, styles['Heading2']))
    elements.append(Spacer(1, 20*mm))

    cover_data = [
        ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Engagement Status:", engagement.status or "N/A"],
        ["Audit Period:", f"{engagement.audit_period_start.strftime('%Y-%m-%d') if engagement.audit_period_start else 'N/A'} to {engagement.audit_period_end.strftime('%Y-%m-%d') if engagement.audit_period_end else 'N/A'}"],
        ["Framework:", framework.name if framework else "N/A"]
    ]
    cover_table = Table(cover_data, colWidths=[50*mm, 100*mm])
    cover_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(cover_table)
    elements.append(PageBreak())

    # Executive Summary
    elements.append(Paragraph("Executive Summary", title_style))

    # Statistics
    open_comments = len([c for c in comments if c.status in ['open', 'in_progress']])
    resolved_comments = len([c for c in comments if c.status in ['resolved', 'closed']])
    critical_findings = len([f for f in findings if f.severity == 'critical'])
    high_findings = len([f for f in findings if f.severity == 'high'])
    medium_findings = len([f for f in findings if f.severity == 'medium'])
    low_findings = len([f for f in findings if f.severity == 'low'])

    stats_data = [
        ["Metric", "Count"],
        ["Total Findings", str(len(findings))],
        ["Critical Severity", str(critical_findings)],
        ["High Severity", str(high_findings)],
        ["Medium Severity", str(medium_findings)],
        ["Low Severity", str(low_findings)],
        ["Open Comments", str(open_comments)],
        ["Resolved Comments", str(resolved_comments)],
        ["Sign-offs Completed", str(len(sign_offs))]
    ]
    stats_table = Table(stats_data, colWidths=[80*mm, 40*mm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 10*mm))

    if engagement.description:
        elements.append(Paragraph("Description", h2_style))
        elements.append(Paragraph(engagement.description, normal_style))

    elements.append(PageBreak())

    # Findings Section
    elements.append(Paragraph("Audit Findings", title_style))

    if findings:
        for i, finding in enumerate(findings, 1):
            severity_color = {
                'critical': colors.red,
                'high': colors.orange,
                'medium': colors.yellow,
                'low': colors.green
            }.get(finding.severity, colors.grey)

            elements.append(Paragraph(f"{i}. {finding.title}", h2_style))

            finding_data = [
                ["Severity:", finding.severity.upper() if finding.severity else "N/A"],
                ["Category:", finding.category or "N/A"],
                ["Status:", finding.status or "N/A"],
            ]
            finding_table = Table(finding_data, colWidths=[40*mm, 110*mm])
            finding_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (1, 0), (1, 0), severity_color),
            ]))
            elements.append(finding_table)

            if finding.description:
                elements.append(Paragraph("Description:", h3_style))
                elements.append(Paragraph(finding.description, normal_style))

            if finding.remediation_plan:
                elements.append(Paragraph("Remediation Plan:", h3_style))
                elements.append(Paragraph(finding.remediation_plan, normal_style))

            elements.append(Spacer(1, 5*mm))
    else:
        elements.append(Paragraph("No findings recorded.", normal_style))

    elements.append(PageBreak())

    # Comments Summary
    elements.append(Paragraph("Comments & Evidence Requests", title_style))

    if comments:
        for i, comment in enumerate(comments[:20], 1):  # Limit to first 20
            elements.append(Paragraph(f"{i}. {comment.comment_type.replace('_', ' ').title()}", h3_style))

            comment_data = [
                ["Target:", f"{comment.target_type}"],
                ["Status:", comment.status or "N/A"],
                ["Author:", getattr(comment, 'author_name', 'Unknown')],
            ]
            comment_table = Table(comment_data, colWidths=[30*mm, 120*mm])
            comment_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ]))
            elements.append(comment_table)

            if comment.content:
                # Truncate long content
                content = comment.content[:500] + "..." if len(comment.content) > 500 else comment.content
                elements.append(Paragraph(content, normal_style))

            elements.append(Spacer(1, 3*mm))

        if len(comments) > 20:
            elements.append(Paragraph(f"... and {len(comments) - 20} more comments",
                ParagraphStyle('More', parent=normal_style, textColor=colors.grey)))
    else:
        elements.append(Paragraph("No comments recorded.", normal_style))

    elements.append(PageBreak())

    # Sign-offs
    elements.append(Paragraph("Sign-offs", title_style))

    if sign_offs:
        signoff_data = [["Type", "Status", "Signer", "Date"]]
        for so in sign_offs:
            signoff_data.append([
                so.sign_off_type or "N/A",
                so.status or "N/A",
                getattr(so, 'signer_name', 'Unknown'),
                so.signed_at.strftime("%Y-%m-%d") if so.signed_at else "N/A"
            ])

        signoff_table = Table(signoff_data, colWidths=[40*mm, 40*mm, 50*mm, 30*mm])
        signoff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(signoff_table)
    else:
        elements.append(Paragraph("No sign-offs recorded.", normal_style))

    elements.append(PageBreak())

    # Activity Log
    elements.append(Paragraph("Recent Activity", title_style))

    if activity_logs:
        activity_data = [["Date", "Actor", "Action", "Target"]]
        for log in activity_logs[:30]:  # Limit to 30 entries
            activity_data.append([
                log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "N/A",
                getattr(log, 'actor_name', 'Unknown'),
                log.action or "N/A",
                log.target_type or "N/A"
            ])

        activity_table = Table(activity_data, colWidths=[35*mm, 45*mm, 40*mm, 40*mm])
        activity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(activity_table)
    else:
        elements.append(Paragraph("No activity recorded.", normal_style))

    # Footer
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph(
        f"Generated by CyberBridge Audit System on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_evidence_package(
    db: Session,
    engagement_id: uuid.UUID,
    evidence_base_path: str = "/app/uploads"
) -> Optional[BytesIO]:
    """
    Generate a ZIP package containing all evidence files for an engagement,
    along with an index and integrity manifest.
    """
    # Get engagement
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        return None

    # Get assessment to find related evidence
    if not engagement.assessment_id:
        return None

    # Get all answers for the assessment
    answers = db.query(models.Answer).filter(
        models.Answer.assessment_id == engagement.assessment_id
    ).all()

    # Get all evidence for these answers
    answer_ids = [a.id for a in answers]
    evidence_files = db.query(models.Evidence).filter(
        models.Evidence.answer_id.in_(answer_ids)
    ).all() if answer_ids else []

    # Create ZIP in memory
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Create manifest
        manifest = {
            'engagement_id': str(engagement_id),
            'engagement_name': engagement.name,
            'generated_at': datetime.utcnow().isoformat(),
            'total_files': len(evidence_files),
            'files': []
        }

        # Add each evidence file
        for evidence in evidence_files:
            file_path = os.path.join(evidence_base_path, evidence.filepath)

            # Get integrity info if available
            integrity = db.query(models.EvidenceIntegrity).filter(
                models.EvidenceIntegrity.evidence_id == evidence.id
            ).order_by(models.EvidenceIntegrity.version.desc()).first()

            file_info = {
                'id': str(evidence.id),
                'filename': evidence.filename,
                'file_type': evidence.file_type,
                'file_size': evidence.file_size,
                'uploaded_at': evidence.uploaded_at.isoformat() if evidence.uploaded_at else None,
                'sha256_hash': integrity.sha256_hash if integrity else None,
                'md5_hash': integrity.md5_hash if integrity else None
            }
            manifest['files'].append(file_info)

            # Add file to ZIP if it exists
            if os.path.exists(file_path):
                # Create clean filename for ZIP
                safe_filename = f"evidence/{evidence.id}_{evidence.filename}"
                zf.write(file_path, safe_filename)

        # Add manifest
        zf.writestr('manifest.json', json.dumps(manifest, indent=2))

        # Add index HTML
        index_html = generate_evidence_index_html(engagement, manifest)
        zf.writestr('index.html', index_html)

    buffer.seek(0)
    return buffer


def generate_evidence_index_html(engagement, manifest: dict) -> str:
    """Generate an HTML index file for the evidence package."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Evidence Package - {engagement.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .meta {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #007bff; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .hash {{ font-family: monospace; font-size: 11px; color: #666; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Evidence Package</h1>
    <div class="meta">
        <strong>Engagement:</strong> {engagement.name}<br>
        <strong>Generated:</strong> {manifest['generated_at']}<br>
        <strong>Total Files:</strong> {manifest['total_files']}
    </div>
    <table>
        <tr>
            <th>Filename</th>
            <th>Type</th>
            <th>Size</th>
            <th>SHA-256</th>
        </tr>
"""

    for f in manifest['files']:
        size_kb = f['file_size'] / 1024 if f['file_size'] else 0
        hash_display = f['sha256_hash'][:16] + '...' if f['sha256_hash'] else 'N/A'
        html += f"""        <tr>
            <td><a href="evidence/{f['id']}_{f['filename']}">{f['filename']}</a></td>
            <td>{f['file_type']}</td>
            <td>{size_kb:.1f} KB</td>
            <td class="hash" title="{f['sha256_hash'] or ''}">{hash_display}</td>
        </tr>
"""

    html += """    </table>
</body>
</html>"""
    return html


def generate_pbc_list(db: Session, engagement_id: uuid.UUID) -> Optional[BytesIO]:
    """
    Generate a PBC (Prepared by Client) list as CSV.
    Lists all requested evidence and their status.
    """
    import csv

    # Get engagement
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        return None

    # Get evidence request comments
    evidence_requests = db.query(models.AuditComment).filter(
        models.AuditComment.engagement_id == engagement_id,
        models.AuditComment.comment_type == 'evidence_request'
    ).all()

    buffer = BytesIO()
    # Write UTF-8 BOM for Excel compatibility
    buffer.write(b'\xef\xbb\xbf')

    wrapper = BytesIO()
    writer = csv.writer(wrapper.__class__(buffer, 'w', newline='', encoding='utf-8'))

    # Write header
    writer.writerow([
        'Request ID',
        'Request Date',
        'Description',
        'Target Type',
        'Status',
        'Assigned To',
        'Due Date',
        'Resolved Date',
        'Resolution Note'
    ])

    # Write data
    for req in evidence_requests:
        # Get assigned user name
        assigned_to = "Unassigned"
        if req.assigned_to_id:
            user = db.query(models.User).filter(models.User.id == req.assigned_to_id).first()
            assigned_to = user.name if user else "Unknown"

        writer.writerow([
            str(req.id)[:8],
            req.created_at.strftime("%Y-%m-%d") if req.created_at else "",
            req.content[:200] if req.content else "",
            req.target_type or "",
            req.status or "",
            assigned_to,
            req.due_date.strftime("%Y-%m-%d") if req.due_date else "",
            req.resolved_at.strftime("%Y-%m-%d") if req.resolved_at else "",
            req.resolution_note[:100] if req.resolution_note else ""
        ])

    buffer.seek(0)
    return buffer


def export_activity_log(
    db: Session,
    engagement_id: uuid.UUID,
    format: str = 'csv'
) -> Optional[BytesIO]:
    """
    Export the activity log for an engagement.
    Supports CSV and JSON formats.
    """
    # Get all activity logs
    logs = audit_finding_repository.get_activity_logs_for_engagement(
        db, engagement_id, limit=10000
    )

    if format == 'json':
        data = []
        for log in logs:
            data.append({
                'id': str(log.id),
                'timestamp': log.created_at.isoformat() if log.created_at else None,
                'actor_type': getattr(log, 'actor_type', None),
                'actor_name': getattr(log, 'actor_name', None),
                'action': log.action,
                'target_type': log.target_type,
                'target_id': str(log.target_id) if log.target_id else None,
                'details': log.details,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent
            })

        buffer = BytesIO()
        buffer.write(json.dumps(data, indent=2).encode('utf-8'))
        buffer.seek(0)
        return buffer

    else:  # CSV format
        import csv

        buffer = BytesIO()
        buffer.write(b'\xef\xbb\xbf')  # UTF-8 BOM

        wrapper = BytesIO()
        writer = csv.writer(wrapper.__class__(buffer, 'w', newline='', encoding='utf-8'))

        writer.writerow([
            'Timestamp',
            'Actor Type',
            'Actor Name',
            'Action',
            'Target Type',
            'Target ID',
            'IP Address',
            'User Agent'
        ])

        for log in logs:
            writer.writerow([
                log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
                getattr(log, 'actor_type', "") or "",
                getattr(log, 'actor_name', "") or "",
                log.action or "",
                log.target_type or "",
                str(log.target_id)[:8] if log.target_id else "",
                log.ip_address or "",
                (log.user_agent[:50] + "...") if log.user_agent and len(log.user_agent) > 50 else (log.user_agent or "")
            ])

        buffer.seek(0)
        return buffer

# services/notification_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from ..repositories import smtp_repository, user_repository
from ..config.environment import get_api_base_url, get_environment_name

logger = logging.getLogger(__name__)


def get_user_notification_preferences(db: Session, user_id: str) -> Dict[str, bool]:
    """Get user's notification preferences"""
    user = user_repository.get_user(db, user_id)
    if not user or not user.notification_preferences:
        # Default preferences if not set
        return {
            "email_notifications": True,
            "assessment_reminders": True,
            "security_alerts": True,
            "scan_completed": True,
            "assessment_incomplete_reminder": True,
            "risk_status_critical": True,
            "account_status_change": True,
        }

    try:
        if isinstance(user.notification_preferences, str):
            return json.loads(user.notification_preferences)
        return user.notification_preferences
    except (json.JSONDecodeError, TypeError):
        return {
            "email_notifications": True,
            "assessment_reminders": True,
            "security_alerts": True,
            "scan_completed": True,
            "assessment_incomplete_reminder": True,
            "risk_status_critical": True,
            "account_status_change": True,
        }


def should_send_notification(db: Session, user_id: str, notification_type: str) -> bool:
    """Check if user has enabled a specific notification type"""
    prefs = get_user_notification_preferences(db, user_id)

    # Master toggle check
    if not prefs.get("email_notifications", True):
        return False

    # Specific notification check
    return prefs.get(notification_type, True)


def send_email(db: Session, to_email: str, subject: str, html_content: str) -> bool:
    """Send an email using SMTP configuration"""
    smtp_config = smtp_repository.get_active_smtp_config(db)
    if not smtp_config:
        logger.warning("No active SMTP configuration found. Cannot send email.")
        return False

    try:
        from_address = smtp_config.sender_email or smtp_config.username
        if not from_address:
            logger.error("No sender email or username configured in active SMTP config.")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = from_address
        message["To"] = to_email

        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        text = message.as_string()

        server = smtplib.SMTP(smtp_config.smtp_server, smtp_config.smtp_port)
        if smtp_config.use_tls:
            server.starttls()
        # Only login if credentials are provided
        if smtp_config.username and smtp_config.password:
            server.login(smtp_config.username, smtp_config.password)
        server.sendmail(from_address, to_email, text)
        server.quit()

        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False


def send_scan_completed_notification(
    db: Session,
    user_id: str,
    user_email: str,
    scanner_type: str,
    scan_target: str,
    results_summary: Dict[str, Any]
) -> bool:
    """Send notification when a security scan completes"""

    if not should_send_notification(db, user_id, "scan_completed"):
        logger.info(f"User {user_email} has disabled scan_completed notifications")
        return False

    # Format scanner type for display
    scanner_display_names = {
        "zap": "Web App Scanner",
        "nmap": "Network Scanner",
        "semgrep": "Code Analysis",
        "osv": "Dependency Analysis",
        "syft": "SBOM Generator"
    }
    scanner_name = scanner_display_names.get(scanner_type.lower(), scanner_type.upper())

    # Build results summary HTML
    summary_html = build_scan_summary_html(scanner_type, results_summary)

    environment = get_environment_name()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #1a365d; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #e0e0e0; }}
            .summary-box {{ background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 15px 0; }}
            .severity-critical {{ color: #dc2626; font-weight: bold; }}
            .severity-high {{ color: #ea580c; font-weight: bold; }}
            .severity-medium {{ color: #ca8a04; font-weight: bold; }}
            .severity-low {{ color: #16a34a; font-weight: bold; }}
            .severity-info {{ color: #2563eb; font-weight: bold; }}
            .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
            .btn {{ display: inline-block; background-color: #5b9bd5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Security Scan Completed</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>Your <strong>{scanner_name}</strong> security scan has completed.</p>

                <div class="summary-box">
                    <h3>Scan Details</h3>
                    <p><strong>Scanner:</strong> {scanner_name}</p>
                    <p><strong>Target:</strong> {scan_target}</p>
                </div>

                {summary_html}

                <p>Log in to CyberBridge to view the full scan results and take action on any findings.</p>

                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    You received this email because you have scan completion notifications enabled in your profile settings.
                </p>
            </div>
            <div class="footer">
                <p>CyberBridge - Cybersecurity Compliance Platform</p>
                <p>Environment: {environment}</p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"[CyberBridge] {scanner_name} Scan Completed - {scan_target}"
    return send_email(db, user_email, subject, html_content)


def build_scan_summary_html(scanner_type: str, results_summary: Dict[str, Any]) -> str:
    """Build HTML summary based on scanner type"""

    scanner_type_lower = scanner_type.lower()

    if scanner_type_lower == "zap":
        return build_zap_summary_html(results_summary)
    elif scanner_type_lower == "nmap":
        return build_nmap_summary_html(results_summary)
    elif scanner_type_lower == "semgrep":
        return build_semgrep_summary_html(results_summary)
    elif scanner_type_lower == "osv":
        return build_osv_summary_html(results_summary)
    else:
        return "<div class='summary-box'><p>Scan completed. Check CyberBridge for details.</p></div>"


def build_zap_summary_html(results_summary: Dict[str, Any]) -> str:
    """Build HTML summary for ZAP scan results"""
    total_alerts = results_summary.get("total_alerts", 0)
    high = results_summary.get("high", 0)
    medium = results_summary.get("medium", 0)
    low = results_summary.get("low", 0)
    informational = results_summary.get("informational", 0)

    return f"""
    <div class="summary-box">
        <h3>Results Summary</h3>
        <p><strong>Total Alerts Found:</strong> {total_alerts}</p>
        <ul style="list-style: none; padding-left: 0;">
            <li><span class="severity-high">High:</span> {high}</li>
            <li><span class="severity-medium">Medium:</span> {medium}</li>
            <li><span class="severity-low">Low:</span> {low}</li>
            <li><span class="severity-info">Informational:</span> {informational}</li>
        </ul>
    </div>
    """


def build_nmap_summary_html(results_summary: Dict[str, Any]) -> str:
    """Build HTML summary for Nmap scan results"""
    total_hosts = results_summary.get("total_hosts", 0)
    hosts_up = results_summary.get("hosts_up", 0)
    open_ports = results_summary.get("open_ports", 0)
    services_found = results_summary.get("services_found", [])

    services_html = ""
    if services_found:
        services_list = ", ".join(services_found[:10])  # Limit to first 10
        if len(services_found) > 10:
            services_list += f" (+{len(services_found) - 10} more)"
        services_html = f"<p><strong>Services Detected:</strong> {services_list}</p>"

    return f"""
    <div class="summary-box">
        <h3>Results Summary</h3>
        <p><strong>Total Hosts Scanned:</strong> {total_hosts}</p>
        <p><strong>Hosts Up:</strong> {hosts_up}</p>
        <p><strong>Open Ports Found:</strong> {open_ports}</p>
        {services_html}
    </div>
    """


def build_semgrep_summary_html(results_summary: Dict[str, Any]) -> str:
    """Build HTML summary for Semgrep scan results"""
    total_findings = results_summary.get("total_findings", 0)
    error = results_summary.get("error", 0)
    warning = results_summary.get("warning", 0)
    info = results_summary.get("info", 0)
    files_scanned = results_summary.get("files_scanned", 0)

    return f"""
    <div class="summary-box">
        <h3>Results Summary</h3>
        <p><strong>Total Findings:</strong> {total_findings}</p>
        <p><strong>Files Scanned:</strong> {files_scanned}</p>
        <ul style="list-style: none; padding-left: 0;">
            <li><span class="severity-high">Errors:</span> {error}</li>
            <li><span class="severity-medium">Warnings:</span> {warning}</li>
            <li><span class="severity-info">Info:</span> {info}</li>
        </ul>
    </div>
    """


def build_osv_summary_html(results_summary: Dict[str, Any]) -> str:
    """Build HTML summary for OSV Scanner results"""
    total_vulnerabilities = results_summary.get("total_vulnerabilities", 0)
    critical = results_summary.get("critical", 0)
    high = results_summary.get("high", 0)
    medium = results_summary.get("medium", 0)
    low = results_summary.get("low", 0)
    packages_scanned = results_summary.get("packages_scanned", 0)

    return f"""
    <div class="summary-box">
        <h3>Results Summary</h3>
        <p><strong>Total Vulnerabilities Found:</strong> {total_vulnerabilities}</p>
        <p><strong>Packages Scanned:</strong> {packages_scanned}</p>
        <ul style="list-style: none; padding-left: 0;">
            <li><span class="severity-critical">Critical:</span> {critical}</li>
            <li><span class="severity-high">High:</span> {high}</li>
            <li><span class="severity-medium">Medium:</span> {medium}</li>
            <li><span class="severity-low">Low:</span> {low}</li>
        </ul>
    </div>
    """


def send_assessment_incomplete_reminder(
    db: Session,
    user_id: str,
    user_email: str,
    assessment_name: str,
    framework_name: str,
    days_incomplete: int,
    progress_percentage: int
) -> bool:
    """Send reminder notification for incomplete assessments"""

    if not should_send_notification(db, user_id, "assessment_incomplete_reminder"):
        logger.info(f"User {user_email} has disabled assessment_incomplete_reminder notifications")
        return False

    environment = get_environment_name()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #ea580c; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #e0e0e0; }}
            .info-box {{ background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 15px 0; }}
            .progress-bar {{ background-color: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden; }}
            .progress-fill {{ background-color: #5b9bd5; height: 100%; text-align: center; color: white; font-size: 12px; line-height: 20px; }}
            .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
            .btn {{ display: inline-block; background-color: #5b9bd5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Assessment Reminder</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>This is a reminder that you have an incomplete assessment that has been pending for <strong>{days_incomplete} days</strong>.</p>

                <div class="info-box">
                    <h3>Assessment Details</h3>
                    <p><strong>Assessment Name:</strong> {assessment_name}</p>
                    <p><strong>Framework:</strong> {framework_name}</p>
                    <p><strong>Days Since Started:</strong> {days_incomplete}</p>
                    <p><strong>Current Progress:</strong></p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress_percentage}%;">{progress_percentage}%</div>
                    </div>
                </div>

                <p>Please log in to CyberBridge to continue your assessment and ensure compliance requirements are met in a timely manner.</p>

                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    You received this email because you have assessment reminder notifications enabled in your profile settings.
                </p>
            </div>
            <div class="footer">
                <p>CyberBridge - Cybersecurity Compliance Platform</p>
                <p>Environment: {environment}</p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"[CyberBridge] Reminder: Incomplete Assessment - {assessment_name}"
    return send_email(db, user_email, subject, html_content)


def send_risk_status_critical_notification(
    db: Session,
    user_id: str,
    user_email: str,
    risk_name: str,
    old_severity: str,
    new_severity: str,
    risk_description: Optional[str] = None,
    changed_by_email: Optional[str] = None
) -> bool:
    """Send notification when risk status changes to High or Critical"""

    if not should_send_notification(db, user_id, "risk_status_critical"):
        logger.info(f"User {user_email} has disabled risk_status_critical notifications")
        return False

    # Determine severity color
    severity_color = "#dc2626" if new_severity.lower() == "critical" else "#ea580c"
    severity_class = "severity-critical" if new_severity.lower() == "critical" else "severity-high"

    environment = get_environment_name()

    description_html = ""
    if risk_description:
        description_html = f"<p><strong>Description:</strong> {risk_description}</p>"

    changed_by_html = ""
    if changed_by_email:
        changed_by_html = f"<p><strong>Changed By:</strong> {changed_by_email}</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: {severity_color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #e0e0e0; }}
            .alert-box {{ background-color: white; border: 2px solid {severity_color}; border-radius: 8px; padding: 15px; margin: 15px 0; }}
            .severity-critical {{ color: #dc2626; font-weight: bold; font-size: 18px; }}
            .severity-high {{ color: #ea580c; font-weight: bold; font-size: 18px; }}
            .change-arrow {{ color: #666; margin: 0 10px; }}
            .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
            .btn {{ display: inline-block; background-color: #5b9bd5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Risk Alert: {new_severity.upper()} Severity</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>A risk in your organization has been escalated to <strong class="{severity_class}">{new_severity.upper()}</strong> severity and requires your attention.</p>

                <div class="alert-box">
                    <h3>Risk Details</h3>
                    <p><strong>Risk Name:</strong> {risk_name}</p>
                    {description_html}
                    <p><strong>Severity Change:</strong>
                        <span>{old_severity}</span>
                        <span class="change-arrow">&#8594;</span>
                        <span class="{severity_class}">{new_severity.upper()}</span>
                    </p>
                    {changed_by_html}
                </div>

                <p>Please log in to CyberBridge to review this risk and take appropriate action to mitigate the threat.</p>

                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    You received this email because you have risk status critical notifications enabled in your profile settings.
                </p>
            </div>
            <div class="footer">
                <p>CyberBridge - Cybersecurity Compliance Platform</p>
                <p>Environment: {environment}</p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"[CyberBridge] ALERT: Risk Escalated to {new_severity.upper()} - {risk_name}"
    return send_email(db, user_email, subject, html_content)


def send_risk_status_critical_notification_to_org(
    db: Session,
    organisation_id: str,
    risk_name: str,
    old_severity: str,
    new_severity: str,
    risk_description: Optional[str] = None,
    changed_by_email: Optional[str] = None,
    exclude_user_id: Optional[str] = None
) -> int:
    """Send risk critical notification to all org admins in the organization"""

    # Get all org admins for the organization
    org_admins = user_repository.get_organisation_admins(db, organisation_id)

    sent_count = 0
    for admin in org_admins:
        # Skip the user who made the change
        if exclude_user_id and str(admin.id) == str(exclude_user_id):
            continue

        success = send_risk_status_critical_notification(
            db=db,
            user_id=str(admin.id),
            user_email=admin.email,
            risk_name=risk_name,
            old_severity=old_severity,
            new_severity=new_severity,
            risk_description=risk_description,
            changed_by_email=changed_by_email
        )
        if success:
            sent_count += 1

    return sent_count


def send_account_status_change_notification(
    db: Session,
    user_id: str,
    user_email: str,
    new_status: str,
    changed_by_email: Optional[str] = None
) -> bool:
    """Send notification when a user's account status changes"""

    if not should_send_notification(db, user_id, "account_status_change"):
        logger.info(f"User {user_email} has disabled account_status_change notifications")
        return False

    # Status-specific content
    status_config = {
        "active": {
            "header_color": "#16a34a",
            "title": "Account Approved",
            "message": "Your account has been approved. You now have full access to CyberBridge.",
        },
        "inactive": {
            "header_color": "#dc2626",
            "title": "Account Deactivated",
            "message": "Your account has been deactivated. You will no longer be able to log in to CyberBridge.",
        },
        "pending_approval": {
            "header_color": "#ea580c",
            "title": "Account Set to Pending Approval",
            "message": "Your account has been set to pending approval. You will be notified once your account is reviewed.",
        },
    }

    config = status_config.get(new_status, {
        "header_color": "#1a365d",
        "title": "Account Status Changed",
        "message": f"Your account status has been changed to: {new_status}.",
    })

    changed_by_html = ""
    if changed_by_email:
        changed_by_html = f"<p><strong>Changed By:</strong> {changed_by_email}</p>"

    environment = get_environment_name()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: {config["header_color"]}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #e0e0e0; }}
            .info-box {{ background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 15px 0; }}
            .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{config["title"]}</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>{config["message"]}</p>

                <div class="info-box">
                    <h3>Details</h3>
                    <p><strong>Account:</strong> {user_email}</p>
                    <p><strong>New Status:</strong> {new_status.replace("_", " ").title()}</p>
                    {changed_by_html}
                </div>

                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    You received this email because you have account status change notifications enabled in your profile settings.
                </p>
            </div>
            <div class="footer">
                <p>CyberBridge - Cybersecurity Compliance Platform</p>
                <p>Environment: {environment}</p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"[CyberBridge] {config['title']}"
    return send_email(db, user_email, subject, html_content)

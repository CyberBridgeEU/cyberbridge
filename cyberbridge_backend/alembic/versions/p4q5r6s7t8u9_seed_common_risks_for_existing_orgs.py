"""Seed Common Risks for existing organizations

Revision ID: p4q5r6s7t8u9
Revises: o3p4q5r6s7t8
Create Date: 2026-01-26 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect
import uuid


# revision identifiers, used by Alembic.
revision: str = 'p4q5r6s7t8u9'
down_revision: Union[str, None] = 'o3p4q5r6s7t8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Common Risks to seed (29 risks)
COMMON_RISKS = [
    {
        "risk_category_name": "Phishing Attacks",
        "risk_category_description": "Social engineering attacks that trick users into revealing sensitive information, credentials, or installing malware through deceptive emails, messages, or websites.",
        "risk_potential_impact": "Credential theft, malware infection, data breach, financial loss, reputation damage",
        "risk_control": "Security awareness training, email filtering, multi-factor authentication, anti-phishing tools, incident response procedures"
    },
    {
        "risk_category_name": "Ransomware",
        "risk_category_description": "Malicious software that encrypts organizational data and demands payment for decryption keys, potentially causing extended operational disruption.",
        "risk_potential_impact": "Complete operational shutdown, data loss, ransom payment costs, recovery expenses, reputation damage",
        "risk_control": "Regular backups, endpoint protection, network segmentation, patch management, user awareness training, incident response plan"
    },
    {
        "risk_category_name": "Malware Infection",
        "risk_category_description": "Introduction of malicious software (viruses, trojans, worms, spyware) into organizational systems, compromising data integrity and system functionality.",
        "risk_potential_impact": "Data theft, system corruption, operational disruption, compliance violations, lateral movement within network",
        "risk_control": "Antivirus/anti-malware solutions, endpoint detection and response (EDR), application whitelisting, regular updates, network monitoring"
    },
    {
        "risk_category_name": "Insider Threats",
        "risk_category_description": "Security risks posed by current or former employees, contractors, or business partners who have legitimate access to organizational resources.",
        "risk_potential_impact": "Data exfiltration, sabotage, intellectual property theft, fraud, compliance violations",
        "risk_control": "Access controls, user activity monitoring, background checks, separation of duties, data loss prevention (DLP), offboarding procedures"
    },
    {
        "risk_category_name": "Data Breach",
        "risk_category_description": "Unauthorized access to or disclosure of sensitive, protected, or confidential data that could be used for malicious purposes.",
        "risk_potential_impact": "Regulatory fines, legal liability, customer trust loss, competitive disadvantage, identity theft for affected individuals",
        "risk_control": "Data encryption, access controls, DLP solutions, security monitoring, incident response, data classification"
    },
    {
        "risk_category_name": "Weak Authentication",
        "risk_category_description": "Insufficient authentication mechanisms that allow unauthorized users to gain access to systems, applications, or data.",
        "risk_potential_impact": "Unauthorized access, account takeover, data breach, privilege escalation, compliance violations",
        "risk_control": "Multi-factor authentication (MFA), strong password policies, password managers, biometric authentication, SSO with secure protocols"
    },
    {
        "risk_category_name": "Unpatched Vulnerabilities",
        "risk_category_description": "Known security vulnerabilities in software, operating systems, or firmware that remain unaddressed and can be exploited by attackers.",
        "risk_potential_impact": "System compromise, data breach, ransomware infection, service disruption, compliance violations",
        "risk_control": "Patch management program, vulnerability scanning, risk-based prioritization, automated patching, virtual patching"
    },
    {
        "risk_category_name": "DDoS Attacks",
        "risk_category_description": "Distributed Denial of Service attacks that overwhelm systems, networks, or applications with traffic, making them unavailable to legitimate users.",
        "risk_potential_impact": "Service unavailability, revenue loss, customer dissatisfaction, reputation damage, resource exhaustion",
        "risk_control": "DDoS protection services, traffic analysis, rate limiting, redundant infrastructure, incident response procedures"
    },
    {
        "risk_category_name": "Man-in-the-Middle Attacks",
        "risk_category_description": "Attackers intercepting and potentially altering communications between two parties who believe they are communicating directly.",
        "risk_potential_impact": "Data interception, credential theft, session hijacking, unauthorized transactions, privacy violation",
        "risk_control": "TLS/SSL encryption, certificate pinning, secure protocols, network monitoring, VPN for remote access"
    },
    {
        "risk_category_name": "Social Engineering",
        "risk_category_description": "Psychological manipulation techniques used to deceive individuals into divulging confidential information or taking harmful actions.",
        "risk_potential_impact": "Credential disclosure, unauthorized access, financial fraud, malware installation, data breach",
        "risk_control": "Security awareness training, verification procedures, anti-social engineering policies, simulated attack exercises"
    },
    {
        "risk_category_name": "Third-Party Risk",
        "risk_category_description": "Security risks introduced through vendors, suppliers, partners, or service providers who have access to organizational systems or data.",
        "risk_potential_impact": "Supply chain compromise, data breach through vendor, service disruption, compliance violations, reputation damage",
        "risk_control": "Vendor risk assessments, contractual security requirements, continuous monitoring, access limitations, regular audits"
    },
    {
        "risk_category_name": "Business Email Compromise",
        "risk_category_description": "Sophisticated scam targeting businesses that perform wire transfers, using compromised or spoofed executive email accounts.",
        "risk_potential_impact": "Financial loss, wire fraud, data disclosure, reputation damage, operational disruption",
        "risk_control": "Email authentication (DMARC, SPF, DKIM), verification procedures, awareness training, approval workflows"
    },
    {
        "risk_category_name": "Credential Stuffing",
        "risk_category_description": "Automated attacks using stolen username/password pairs from data breaches to attempt access to multiple accounts.",
        "risk_potential_impact": "Account takeover, unauthorized access, data breach, fraud, customer trust loss",
        "risk_control": "Multi-factor authentication, rate limiting, account lockout policies, credential monitoring, CAPTCHA"
    },
    {
        "risk_category_name": "Physical Security Breach",
        "risk_category_description": "Unauthorized physical access to facilities, data centers, or devices that could lead to data theft or system compromise.",
        "risk_potential_impact": "Equipment theft, data theft, hardware tampering, service disruption, unauthorized access",
        "risk_control": "Access controls, surveillance systems, visitor management, secure disposal, device encryption"
    },
    {
        "risk_category_name": "Data Loss",
        "risk_category_description": "Accidental or intentional destruction, corruption, or loss of organizational data through various means.",
        "risk_potential_impact": "Business disruption, compliance violations, recovery costs, reputation damage, competitive disadvantage",
        "risk_control": "Regular backups, disaster recovery planning, DLP solutions, data classification, redundant storage"
    },
    {
        "risk_category_name": "Privilege Escalation",
        "risk_category_description": "Exploitation of vulnerabilities or misconfigurations to gain elevated access rights beyond intended authorization levels.",
        "risk_potential_impact": "Unauthorized system access, data breach, system compromise, compliance violations, lateral movement",
        "risk_control": "Least privilege principle, privileged access management (PAM), regular access reviews, vulnerability management"
    },
    {
        "risk_category_name": "Shadow IT",
        "risk_category_description": "Use of unauthorized IT systems, software, or services by employees without IT department knowledge or approval.",
        "risk_potential_impact": "Security gaps, data leakage, compliance violations, lack of support, integration issues",
        "risk_control": "IT governance policies, cloud access security broker (CASB), user awareness, approved alternatives catalog"
    },
    {
        "risk_category_name": "Cryptojacking",
        "risk_category_description": "Unauthorized use of computing resources to mine cryptocurrency, degrading system performance and increasing costs.",
        "risk_potential_impact": "Increased costs, degraded performance, resource exhaustion, potential for other malware",
        "risk_control": "Endpoint protection, network monitoring, ad blockers, browser extensions, resource monitoring"
    },
    {
        "risk_category_name": "DNS Attacks",
        "risk_category_description": "Attacks targeting Domain Name System infrastructure including DNS spoofing, cache poisoning, and DNS amplification.",
        "risk_potential_impact": "Traffic redirection, phishing facilitation, service disruption, data interception",
        "risk_control": "DNSSEC implementation, DNS monitoring, redundant DNS providers, secure DNS configurations"
    },
    {
        "risk_category_name": "Zero-Day Exploits",
        "risk_category_description": "Attacks exploiting previously unknown vulnerabilities before patches or fixes are available from vendors.",
        "risk_potential_impact": "System compromise, data breach, no immediate remediation available, potential widespread impact",
        "risk_control": "Defense in depth, behavioral analysis, threat intelligence, network segmentation, rapid response capabilities"
    },
    {
        "risk_category_name": "Configuration Errors",
        "risk_category_description": "Security vulnerabilities introduced through misconfigured systems, applications, or network devices.",
        "risk_potential_impact": "Unauthorized access, data exposure, compliance violations, service disruption",
        "risk_control": "Configuration management, security baselines, automated compliance checking, change management"
    },
    {
        "risk_category_name": "Inadequate Logging",
        "risk_category_description": "Insufficient logging and monitoring capabilities that prevent detection of security incidents and forensic investigation.",
        "risk_potential_impact": "Delayed incident detection, incomplete investigations, compliance violations, extended breach duration",
        "risk_control": "Comprehensive logging strategy, SIEM implementation, log retention policies, regular review"
    },
    {
        "risk_category_name": "Supply Chain Attack",
        "risk_category_description": "Compromise of trusted third-party software, hardware, or services to gain access to target organizations.",
        "risk_potential_impact": "Widespread compromise, difficult detection, trust erosion, significant remediation effort",
        "risk_control": "Supply chain security assessment, software composition analysis, integrity verification, vendor monitoring"
    },
    {
        "risk_category_name": "Mobile Device Risks",
        "risk_category_description": "Security threats associated with mobile devices including loss, theft, malware, and unauthorized access.",
        "risk_potential_impact": "Data breach, unauthorized access, malware spread, compliance violations",
        "risk_control": "Mobile device management (MDM), device encryption, remote wipe capability, app whitelisting"
    },
    {
        "risk_category_name": "Wireless Network Attacks",
        "risk_category_description": "Attacks targeting wireless networks including rogue access points, evil twin attacks, and protocol vulnerabilities.",
        "risk_potential_impact": "Data interception, unauthorized access, man-in-the-middle attacks, network compromise",
        "risk_control": "WPA3 encryption, wireless intrusion detection, network segmentation, regular audits, secure configurations"
    },
    {
        "risk_category_name": "Inadequate Incident Response",
        "risk_category_description": "Lack of proper incident response capabilities leading to prolonged breaches and ineffective remediation.",
        "risk_potential_impact": "Extended breach duration, increased damage, regulatory penalties, reputation damage",
        "risk_control": "Incident response plan, regular testing, trained response team, playbooks, communication procedures"
    },
    {
        "risk_category_name": "Legacy System Vulnerabilities",
        "risk_category_description": "Security risks from outdated systems that no longer receive security updates or have known vulnerabilities.",
        "risk_potential_impact": "Exploitation of known vulnerabilities, compliance violations, integration issues, support challenges",
        "risk_control": "Legacy system inventory, compensating controls, migration planning, network isolation, enhanced monitoring"
    },
    {
        "risk_category_name": "Insufficient Encryption",
        "risk_category_description": "Inadequate encryption of data at rest, in transit, or in use, leaving sensitive information vulnerable.",
        "risk_potential_impact": "Data exposure, compliance violations, privacy breaches, competitive disadvantage",
        "risk_control": "Encryption standards enforcement, key management, TLS implementation, encrypted storage, data classification"
    },
    {
        "risk_category_name": "Account Takeover",
        "risk_category_description": "Unauthorized access to user accounts through various methods including credential theft, session hijacking, or brute force.",
        "risk_potential_impact": "Data breach, fraud, unauthorized transactions, reputation damage, customer trust loss",
        "risk_control": "Multi-factor authentication, anomaly detection, session management, account monitoring, user awareness"
    }
]


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Seed Common Risks for all existing organizations that don't have any risks"""
    conn = op.get_bind()

    # Check if required tables exist
    if not table_exists('organisations') or not table_exists('risks'):
        print("Required tables don't exist, skipping migration")
        return

    # Get default severity ID (Medium)
    severity_result = conn.execute(text(
        "SELECT id FROM risk_severity WHERE LOWER(risk_severity_name) = 'medium' LIMIT 1"
    )).fetchone()

    if not severity_result:
        print("Could not find 'Medium' severity level, skipping migration")
        return

    medium_severity_id = severity_result[0]

    # Get default status ID (Accept)
    status_result = conn.execute(text(
        "SELECT id FROM risk_status WHERE LOWER(risk_status_name) = 'accept' LIMIT 1"
    )).fetchone()

    if not status_result:
        print("Could not find 'Accept' status, skipping migration")
        return

    accept_status_id = status_result[0]

    # Get default product type ID (Software)
    product_type_result = conn.execute(text(
        "SELECT id FROM product_types WHERE LOWER(name) = 'software' LIMIT 1"
    )).fetchone()

    if not product_type_result:
        print("Could not find 'Software' product type, skipping migration")
        return

    software_product_type_id = product_type_result[0]

    # Get all organizations that don't have any risks
    orgs_without_risks = conn.execute(text("""
        SELECT o.id, o.name
        FROM organisations o
        WHERE NOT EXISTS (
            SELECT 1 FROM risks r WHERE r.organisation_id = o.id
        )
    """)).fetchall()

    print(f"Found {len(orgs_without_risks)} organizations without risks")

    total_risks_created = 0

    for org in orgs_without_risks:
        org_id = org[0]
        org_name = org[1]
        risks_created = 0

        for risk in COMMON_RISKS:
            try:
                risk_id = str(uuid.uuid4())
                conn.execute(text("""
                    INSERT INTO risks (
                        id,
                        product_type_id,
                        risk_category_name,
                        risk_category_description,
                        risk_potential_impact,
                        risk_control,
                        likelihood,
                        residual_risk,
                        risk_severity_id,
                        risk_status_id,
                        organisation_id,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :product_type_id,
                        :risk_category_name,
                        :risk_category_description,
                        :risk_potential_impact,
                        :risk_control,
                        :likelihood,
                        :residual_risk,
                        :risk_severity_id,
                        :risk_status_id,
                        :organisation_id,
                        NOW(),
                        NOW()
                    )
                """), {
                    "id": risk_id,
                    "product_type_id": str(software_product_type_id),
                    "risk_category_name": risk["risk_category_name"],
                    "risk_category_description": risk["risk_category_description"],
                    "risk_potential_impact": risk["risk_potential_impact"],
                    "risk_control": risk["risk_control"],
                    "likelihood": str(medium_severity_id),
                    "residual_risk": str(medium_severity_id),
                    "risk_severity_id": str(medium_severity_id),
                    "risk_status_id": str(accept_status_id),
                    "organisation_id": str(org_id)
                })
                risks_created += 1
            except Exception as e:
                print(f"Error creating risk '{risk['risk_category_name']}' for org '{org_name}': {str(e)}")

        print(f"Created {risks_created} risks for organization '{org_name}'")
        total_risks_created += risks_created

    print(f"Total risks created: {total_risks_created}")


def downgrade() -> None:
    """Remove seeded Common Risks (risks that match the Common Risks template names)"""
    conn = op.get_bind()

    if not table_exists('risks'):
        return

    # Get the list of risk names to delete
    risk_names = [risk["risk_category_name"] for risk in COMMON_RISKS]

    # Delete risks that match the Common Risks template names
    # Only delete risks that have no modifications (same description as template)
    for risk in COMMON_RISKS:
        try:
            conn.execute(text("""
                DELETE FROM risks
                WHERE risk_category_name = :name
                AND risk_category_description = :description
            """), {
                "name": risk["risk_category_name"],
                "description": risk["risk_category_description"]
            })
        except Exception as e:
            print(f"Error deleting risk '{risk['risk_category_name']}': {str(e)}")

    print(f"Removed seeded Common Risks")

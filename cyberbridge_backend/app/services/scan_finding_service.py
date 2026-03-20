# scan_finding_service.py
import hashlib
import json
import logging
import uuid
from sqlalchemy.orm import Session

from app.models import models
from app.constants.scan_finding_mapping_rules import MAPPING_RULES

logger = logging.getLogger(__name__)


def _compute_finding_hash(title: str, severity: str, identifier: str) -> str:
    """Compute SHA256 hash for finding deduplication."""
    raw = f"{title or ''}|{severity or ''}|{identifier or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalize_severity(severity: str, scanner_type: str) -> str:
    """Map scanner-specific severity strings to high/medium/low/info."""
    if not severity:
        return "info"
    s = severity.strip().lower()
    # ZAP uses: High, Medium, Low, Informational
    # Semgrep uses: ERROR, WARNING, INFO
    # OSV uses: CRITICAL, HIGH, MODERATE, LOW
    # Nmap: varies
    high_values = {"high", "error", "critical", "3"}
    medium_values = {"medium", "moderate", "warning", "2"}
    low_values = {"low", "1"}
    if s in high_values:
        return "high"
    if s in medium_values:
        return "medium"
    if s in low_values:
        return "low"
    return "info"


# ===========================
# Finding Extractors (one per scanner type)
# ===========================

def extract_findings_from_zap(results_json: dict) -> list[dict]:
    """Extract individual findings from ZAP scan results."""
    findings = []
    try:
        # ZAP results are stored as an array of alerts
        alerts = []
        if isinstance(results_json, list):
            alerts = results_json
        elif isinstance(results_json, dict):
            alerts = results_json.get("alerts", results_json.get("site", []))
            if isinstance(alerts, dict):
                alerts = alerts.get("alerts", [])

        for alert in alerts:
            if not isinstance(alert, dict):
                continue
            title = alert.get("name") or alert.get("alert") or ""
            severity = alert.get("risk") or alert.get("riskdesc", "").split(" ")[0] if alert.get("riskdesc") else ""
            cweid = alert.get("cweid") or alert.get("cweId") or ""
            identifier = f"CWE-{cweid}" if cweid and str(cweid) != "-1" and str(cweid) != "0" else ""
            description = alert.get("description") or alert.get("desc") or ""
            solution = alert.get("solution") or ""
            url = alert.get("url") or ""
            # Build extra data with additional ZAP fields
            extra = {}
            for key in ["wascid", "sourceid", "reference", "evidence", "param", "attack", "otherinfo"]:
                if alert.get(key):
                    extra[key] = alert[key]

            findings.append({
                "title": title[:500],
                "severity": severity,
                "identifier": identifier[:255],
                "description": description,
                "solution": solution,
                "url_or_target": url[:500],
                "extra_data": json.dumps(extra) if extra else None,
            })
    except Exception as e:
        logger.error(f"Error extracting ZAP findings: {e}")
    return findings


def extract_findings_from_nmap(results_json: dict) -> list[dict]:
    """Extract individual findings from Nmap scan results."""
    findings = []
    try:
        if not isinstance(results_json, dict):
            return findings

        # Nmap results have hosts with ports/services
        hosts = results_json.get("hosts", [])
        if isinstance(results_json.get("scan"), dict):
            # python-nmap format
            for host_ip, host_data in results_json["scan"].items():
                if not isinstance(host_data, dict):
                    continue
                protocols = ["tcp", "udp"]
                for proto in protocols:
                    ports = host_data.get(proto, {})
                    if not isinstance(ports, dict):
                        continue
                    for port_num, port_data in ports.items():
                        if not isinstance(port_data, dict):
                            continue
                        state = port_data.get("state", "")
                        if state != "open":
                            continue
                        service = port_data.get("name", "unknown")
                        product = port_data.get("product", "")
                        version = port_data.get("version", "")
                        title = f"Open port {port_num}/{proto}: {service}"
                        if product:
                            title += f" ({product} {version})".strip()

                        findings.append({
                            "title": title[:500],
                            "severity": "info",
                            "identifier": "",
                            "description": f"Service {service} detected on {host_ip}:{port_num}",
                            "solution": "",
                            "url_or_target": f"{host_ip}:{port_num}",
                            "extra_data": json.dumps({
                                "host": host_ip,
                                "port": int(port_num),
                                "protocol": proto,
                                "service": service,
                                "product": product,
                                "version": version,
                            }),
                        })

        # Also handle vulnerabilities array if present
        vulnerabilities = results_json.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            if not isinstance(vuln, dict):
                continue
            title = vuln.get("title") or vuln.get("name") or ""
            severity = vuln.get("severity") or "medium"
            cve_id = vuln.get("cve_id") or vuln.get("id") or ""
            host = vuln.get("host") or ""
            port = vuln.get("port") or ""

            findings.append({
                "title": title[:500],
                "severity": severity,
                "identifier": cve_id[:255],
                "description": vuln.get("description") or "",
                "solution": vuln.get("solution") or "",
                "url_or_target": f"{host}:{port}" if host else "",
                "extra_data": None,
            })
    except Exception as e:
        logger.error(f"Error extracting Nmap findings: {e}")
    return findings


def extract_findings_from_semgrep(results_json: dict) -> list[dict]:
    """Extract individual findings from Semgrep scan results."""
    findings = []
    try:
        if not isinstance(results_json, dict):
            return findings

        results = []
        # Semgrep stores results in raw_data.results
        raw_data = results_json.get("raw_data", results_json)
        if isinstance(raw_data, dict):
            results = raw_data.get("results", [])
        elif isinstance(raw_data, list):
            results = raw_data

        for result in results:
            if not isinstance(result, dict):
                continue
            check_id = result.get("check_id") or ""
            severity = result.get("extra", {}).get("severity") or result.get("severity") or "info"
            message = result.get("extra", {}).get("message") or result.get("message") or ""
            path = result.get("path") or ""
            start_line = result.get("start", {}).get("line") or ""
            # Extract CWE from metadata if available
            metadata = result.get("extra", {}).get("metadata", {})
            cwe_list = metadata.get("cwe", [])
            identifier = ""
            if cwe_list:
                if isinstance(cwe_list, list):
                    identifier = cwe_list[0] if cwe_list else ""
                else:
                    identifier = str(cwe_list)

            title = check_id.split(".")[-1] if "." in check_id else check_id
            if not title:
                title = message[:100] if message else "Semgrep finding"

            findings.append({
                "title": title[:500],
                "severity": severity,
                "identifier": identifier[:255],
                "description": message,
                "solution": "",
                "url_or_target": f"{path}:{start_line}" if path else "",
                "extra_data": json.dumps({"check_id": check_id}) if check_id else None,
            })
    except Exception as e:
        logger.error(f"Error extracting Semgrep findings: {e}")
    return findings


def extract_findings_from_osv(results_json: dict) -> list[dict]:
    """Extract individual findings from OSV scan results."""
    findings = []
    try:
        if not isinstance(results_json, dict):
            return findings

        # OSV results may be wrapped in {success, analysis, raw_data} format
        raw_data = results_json.get("raw_data", results_json)
        if not isinstance(raw_data, dict):
            raw_data = results_json

        # OSV results have nested package → vulnerabilities
        results = raw_data.get("results", [])
        if not isinstance(results, list):
            results = []

        for result in results:
            if not isinstance(result, dict):
                continue
            # result can have "packages" or be the package itself
            packages = result.get("packages", [result])
            for pkg in packages:
                if not isinstance(pkg, dict):
                    continue
                package_info = pkg.get("package", {})
                package_name = package_info.get("name", "") if isinstance(package_info, dict) else ""
                vulnerabilities = pkg.get("vulnerabilities", [])

                for vuln in vulnerabilities:
                    if not isinstance(vuln, dict):
                        continue
                    vuln_id = vuln.get("id") or ""
                    summary = vuln.get("summary") or vuln.get("details") or ""
                    severity_list = vuln.get("severity", [])
                    severity = "medium"
                    if severity_list and isinstance(severity_list, list):
                        for sev in severity_list:
                            if isinstance(sev, dict) and sev.get("type") == "CVSS_V3":
                                score = sev.get("score")
                                if score:
                                    # Parse CVSS score from vector
                                    try:
                                        score_val = float(str(score).split("/")[-1]) if "/" in str(score) else float(score)
                                        if score_val >= 9.0:
                                            severity = "critical"
                                        elif score_val >= 7.0:
                                            severity = "high"
                                        elif score_val >= 4.0:
                                            severity = "medium"
                                        else:
                                            severity = "low"
                                    except (ValueError, TypeError):
                                        pass

                    title = f"{vuln_id}: {summary[:100]}" if summary else vuln_id
                    if not title:
                        title = f"OSV vulnerability in {package_name}"

                    findings.append({
                        "title": title[:500],
                        "severity": severity,
                        "identifier": vuln_id[:255],
                        "description": summary,
                        "solution": "",
                        "url_or_target": package_name[:500],
                        "extra_data": json.dumps({"package": package_name}) if package_name else None,
                    })
    except Exception as e:
        logger.error(f"Error extracting OSV findings: {e}")
    return findings


# ===========================
# Core Functions
# ===========================

_EXTRACTORS = {
    "zap": extract_findings_from_zap,
    "nmap": extract_findings_from_nmap,
    "semgrep": extract_findings_from_semgrep,
    "osv": extract_findings_from_osv,
}


def extract_and_store_findings(
    db: Session,
    scan_history_id: uuid.UUID,
    scanner_type: str,
    results_json,
    organisation_id: uuid.UUID,
) -> list:
    """Extract findings from scan results and store as ScanFinding rows.
    Returns list of created ScanFinding objects."""
    extractor = _EXTRACTORS.get(scanner_type)
    if not extractor:
        return []

    # Parse results if string
    if isinstance(results_json, str):
        try:
            results_json = json.loads(results_json)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Could not parse results JSON for scan {scan_history_id}")
            return []

    raw_findings = extractor(results_json)
    if not raw_findings:
        return []

    created = []
    seen_hashes = set()
    for f in raw_findings:
        finding_hash = _compute_finding_hash(f["title"], f["severity"], f["identifier"])
        normalized = _normalize_severity(f["severity"], scanner_type)

        # Skip duplicates within current batch
        if finding_hash in seen_hashes:
            continue
        seen_hashes.add(finding_hash)

        # Skip duplicates already in DB for same scan
        existing = db.query(models.ScanFinding).filter(
            models.ScanFinding.scan_history_id == scan_history_id,
            models.ScanFinding.finding_hash == finding_hash,
        ).first()
        if existing:
            continue

        scan_finding = models.ScanFinding(
            scan_history_id=scan_history_id,
            scanner_type=scanner_type,
            organisation_id=organisation_id,
            finding_hash=finding_hash,
            title=f["title"],
            severity=f["severity"],
            normalized_severity=normalized,
            identifier=f["identifier"],
            description=f["description"],
            solution=f["solution"],
            url_or_target=f["url_or_target"],
            extra_data=f.get("extra_data"),
        )
        db.add(scan_finding)
        created.append(scan_finding)

    if created:
        try:
            db.flush()
        except Exception as e:
            logger.error(f"Error flushing scan findings: {e}")
            db.rollback()
            return []

    return created


def auto_map_findings_to_risks(
    db: Session,
    findings: list,
    organisation_id: uuid.UUID,
) -> int:
    """Auto-map findings to risks in the organisation based on mapping rules.
    Returns count of new mappings created."""
    if not findings:
        return 0

    # Load all risks for the organisation
    risks = db.query(models.Risks).filter(
        models.Risks.organisation_id == organisation_id
    ).all()

    if not risks:
        return 0

    mapped_count = 0
    for finding in findings:
        for rule in MAPPING_RULES:
            # Check if scanner type matches
            if finding.scanner_type not in rule["scanner_types"]:
                continue

            # Check if finding title matches any keyword
            title_lower = (finding.title or "").lower()
            identifier_upper = (finding.identifier or "").upper()

            title_match = any(kw in title_lower for kw in rule["finding_title_keywords"])
            id_match = any(pat.upper() in identifier_upper for pat in rule["finding_identifier_patterns"]) if rule["finding_identifier_patterns"] else False

            if not title_match and not id_match:
                continue

            # Find matching risks
            for risk in risks:
                risk_name_lower = (risk.risk_category_name or "").lower()
                if any(pat in risk_name_lower for pat in rule["risk_patterns"]):
                    # Create junction entry (idempotent)
                    existing = db.query(models.RiskScanFinding).filter(
                        models.RiskScanFinding.risk_id == risk.id,
                        models.RiskScanFinding.finding_id == finding.id,
                    ).first()
                    if not existing:
                        junction = models.RiskScanFinding(
                            risk_id=risk.id,
                            finding_id=finding.id,
                            is_auto_mapped=True,
                        )
                        db.add(junction)
                        mapped_count += 1

    if mapped_count > 0:
        try:
            db.flush()
        except Exception as e:
            logger.error(f"Error flushing risk-finding mappings: {e}")
            db.rollback()
            return 0

    return mapped_count

"""
Aggregation logic for scanner-specific endpoints.
Reproduces the exact response shapes from the old cti-dashboard-api.
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from ..repositories.indicator_repository import IndicatorRepository
from ..utils import parse_labels as _parse_labels


# ---------------------------------------------------------------------------
# Nmap helpers
# ---------------------------------------------------------------------------

def _parse_nmap_labels(labels: list[str]) -> tuple[str, str, str]:
    port = ""
    service = ""
    protocol = ""
    for lbl in labels:
        if lbl.startswith("nmap-port-"):
            port = lbl.replace("nmap-port-", "")
        elif lbl.startswith("nmap-service-"):
            service = lbl.replace("nmap-service-", "")
        elif lbl.startswith("nmap-protocol-"):
            protocol = lbl.replace("nmap-protocol-", "")
    return port, service, protocol


def _extract_nmap_ip(name: str) -> str:
    try:
        if " on " in name:
            after_on = name.split(" on ", 1)[1]
            return after_on.split(" ")[0].strip().rstrip("()")
    except Exception:
        pass
    return ""


def get_nmap_results(db: Session) -> dict:
    indicators = IndicatorRepository.get_indicators_by_source(db, "nmap")

    port_counts: dict[str, int] = defaultdict(int)
    service_counts: dict[str, int] = defaultdict(int)
    protocol_counts: dict[str, int] = defaultdict(int)
    host_ports: dict[str, set] = defaultdict(set)
    recent = []

    for ind in indicators:
        labels = _parse_labels(ind.labels)
        port, service, protocol = _parse_nmap_labels(labels)
        name = ind.name or ""
        ip = _extract_nmap_ip(name)

        if port:
            port_counts[port] += 1
        if service:
            service_counts[service] += 1
        if protocol:
            protocol_counts[protocol] += 1
        if ip and port:
            host_ports[ip].add(port)

        if len(recent) < 50:
            recent.append({
                "id": str(ind.id),
                "name": name,
                "port": port,
                "service": service,
                "protocol": protocol,
                "ip": ip,
                "created": ind.created_at.isoformat() if ind.created_at else "",
            })

    open_ports = sorted(
        [{"port": p, "count": c} for p, c in port_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]
    by_service = sorted(
        [{"service": s, "count": c} for s, c in service_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]
    by_protocol = sorted(
        [{"protocol": p, "count": c} for p, c in protocol_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )
    hosts = [
        {"ip": ip, "ports": sorted(list(ports))}
        for ip, ports in host_ports.items()
    ][:50]

    return {
        "total": len(indicators),
        "open_ports": open_ports,
        "by_service": by_service,
        "by_protocol": by_protocol,
        "hosts": hosts,
        "recent": recent,
    }


# ---------------------------------------------------------------------------
# ZAP helpers
# ---------------------------------------------------------------------------

def _parse_zap_labels(labels: list[str]) -> tuple[str, str]:
    risk = ""
    cwe = ""
    for lbl in labels:
        if lbl.startswith("zap-risk-"):
            risk = lbl.replace("zap-risk-", "").capitalize()
        elif lbl.startswith("zap-cwe-"):
            cwe = lbl.replace("zap-cwe-", "")
    return risk, cwe


def get_zap_results(db: Session) -> dict:
    indicators = IndicatorRepository.get_indicators_by_source(db, "zap")

    by_risk: dict[str, int] = defaultdict(int)
    cwe_counts: dict[str, int] = defaultdict(int)
    vuln_counts: dict[str, dict] = {}
    recent = []

    for ind in indicators:
        labels = _parse_labels(ind.labels)
        risk, cwe = _parse_zap_labels(labels)
        name = ind.name or ""
        vuln_name = name.replace("ZAP: ", "") if name.startswith("ZAP: ") else name

        pattern = ind.pattern or ""
        url_val = ""
        if "url:value" in pattern:
            parts = pattern.split("'")
            if len(parts) >= 2:
                url_val = parts[1]

        if risk:
            by_risk[risk] += 1
        if cwe:
            cwe_counts[f"CWE-{cwe}"] += 1

        vkey = vuln_name
        if vkey not in vuln_counts:
            vuln_counts[vkey] = {"name": vuln_name, "count": 0, "risk": risk}
        vuln_counts[vkey]["count"] += 1

        if len(recent) < 50:
            recent.append({
                "id": str(ind.id),
                "name": vuln_name,
                "risk": risk,
                "cwe": cwe,
                "url": url_val,
                "created": ind.created_at.isoformat() if ind.created_at else "",
            })

    risk_order = {"High": 0, "Medium": 1, "Low": 2, "Info": 3, "": 4}
    recent.sort(key=lambda x: risk_order.get(x.get("risk", ""), 4))

    by_cwe = sorted(
        [{"cwe": c, "count": cnt} for c, cnt in cwe_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]
    top_vulnerabilities = sorted(
        list(vuln_counts.values()),
        key=lambda x: x["count"], reverse=True,
    )[:10]

    full_by_risk = {"High": 0, "Medium": 0, "Low": 0, "Info": 0}
    full_by_risk.update(dict(by_risk))

    return {
        "total": len(indicators),
        "by_risk": full_by_risk,
        "by_cwe": by_cwe,
        "top_vulnerabilities": top_vulnerabilities,
        "recent": recent,
    }


# ---------------------------------------------------------------------------
# Semgrep helpers
# ---------------------------------------------------------------------------

def _parse_semgrep_labels(labels: list[str]) -> tuple[str, str, str]:
    severity = ""
    cwe = ""
    check = ""
    for lbl in labels:
        if lbl.startswith("semgrep-severity-"):
            severity = lbl.replace("semgrep-severity-", "").upper()
        elif lbl.startswith("semgrep-cwe-"):
            cwe = lbl.replace("semgrep-cwe-", "").upper()
        elif lbl.startswith("semgrep-check-"):
            check = lbl.replace("semgrep-check-", "")
    return severity, cwe, check


def get_semgrep_results(db: Session) -> dict:
    indicators = IndicatorRepository.get_indicators_by_source(db, "semgrep")

    by_severity: dict[str, int] = defaultdict(int)
    check_counts: dict[str, int] = defaultdict(int)
    owasp_counts: dict[str, int] = defaultdict(int)
    recent = []

    for ind in indicators:
        labels = _parse_labels(ind.labels)
        severity, cwe, check = _parse_semgrep_labels(labels)
        name = ind.name or ""

        pattern = ind.pattern or ""
        file_val = ""
        if "file:name" in pattern:
            parts = pattern.split("'")
            if len(parts) >= 2:
                file_val = parts[1]

        description = ind.description or ""
        if "OWASP:" in description:
            for line in description.split("\n"):
                if "OWASP:" in line:
                    owasp_val = line.replace("OWASP:", "").strip()
                    owasp_prefix = owasp_val.split(":")[0].strip()
                    if owasp_prefix:
                        owasp_counts[owasp_prefix] += 1
                    break

        if severity:
            by_severity[severity] += 1
        if check:
            check_counts[check] += 1

        if len(recent) < 50:
            recent.append({
                "id": str(ind.id),
                "name": name,
                "severity": severity,
                "cwe": cwe,
                "file": file_val,
                "created": ind.created_at.isoformat() if ind.created_at else "",
            })

    by_owasp = sorted(
        [{"category": c, "count": cnt} for c, cnt in owasp_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]
    by_check = sorted(
        [{"check": c, "count": cnt} for c, cnt in check_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]

    full_by_severity = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    full_by_severity.update(dict(by_severity))

    return {
        "total": len(indicators),
        "by_severity": full_by_severity,
        "by_owasp": by_owasp,
        "by_check": by_check,
        "recent": recent,
    }


# ---------------------------------------------------------------------------
# OSV helpers
# ---------------------------------------------------------------------------

def _parse_osv_labels(labels: list[str]) -> tuple[str, str, str]:
    ecosystem = ""
    severity = ""
    vuln_id = ""
    for lbl in labels:
        if lbl.startswith("osv-ecosystem-"):
            ecosystem = lbl.replace("osv-ecosystem-", "")
        elif lbl.startswith("osv-severity-"):
            severity = lbl.replace("osv-severity-", "").capitalize()
        elif lbl.startswith("osv-id-"):
            vuln_id = lbl.replace("osv-id-", "").upper()
    return ecosystem, severity, vuln_id


def get_osv_results(db: Session) -> dict:
    indicators = IndicatorRepository.get_indicators_by_source(db, "osv")

    by_severity: dict[str, int] = defaultdict(int)
    ecosystem_counts: dict[str, int] = defaultdict(int)
    package_counts: dict[str, int] = defaultdict(int)
    recent = []

    for ind in indicators:
        labels = _parse_labels(ind.labels)
        ecosystem, severity, vuln_id = _parse_osv_labels(labels)
        name = ind.name or ""

        pkg_display = ""
        cve_id = ""
        if name.startswith("Vulnerable dependency: "):
            rest = name.replace("Vulnerable dependency: ", "")
            parts = rest.split(" (")
            if parts:
                pkg_display = parts[0].strip()
            if len(parts) > 1:
                cve_id = parts[1].rstrip(")").strip()

        if severity:
            by_severity[severity] += 1
        if ecosystem:
            ecosystem_counts[ecosystem] += 1
        if pkg_display:
            package_counts[pkg_display] += 1

        if len(recent) < 50:
            recent.append({
                "id": str(ind.id),
                "name": name,
                "severity": severity,
                "ecosystem": ecosystem,
                "cve_id": cve_id or vuln_id,
                "created": ind.created_at.isoformat() if ind.created_at else "",
            })

    sev_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "": 4}
    recent.sort(key=lambda x: sev_order.get(x.get("severity", ""), 4))

    by_ecosystem = sorted(
        [{"ecosystem": e, "count": c} for e, c in ecosystem_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]
    top_packages = sorted(
        [{"package": p, "count": c} for p, c in package_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]

    full_by_severity = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    full_by_severity.update(dict(by_severity))

    return {
        "total": len(indicators),
        "by_severity": full_by_severity,
        "by_ecosystem": by_ecosystem,
        "top_packages": top_packages,
        "recent": recent,
    }

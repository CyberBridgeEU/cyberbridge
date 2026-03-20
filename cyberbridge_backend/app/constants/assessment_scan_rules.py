# assessment_scan_rules.py
# Keyword-to-scanner mapping for rule-based assessment answer suggestions.
# Maps question keywords to relevant scanner types and provides severity weights.

# Scanner types as stored in scan_findings.scanner_type
SCANNER_TYPES = {"zap", "nmap", "semgrep", "osv", "syft"}

# Maps question keywords/phrases to relevant scanner types.
# When a question's text matches a keyword, findings from those scanners are relevant.
QUESTION_KEYWORD_TO_SCANNERS = {
    # Vulnerability scanning
    "vulnerability": ["zap", "nmap", "osv", "semgrep"],
    "vulnerabilities": ["zap", "nmap", "osv", "semgrep"],
    "vulnerability scanning": ["zap", "nmap", "osv", "semgrep"],
    "security testing": ["zap", "nmap", "semgrep"],
    "penetration test": ["zap", "nmap"],
    "pen test": ["zap", "nmap"],
    # Web application security
    "web application": ["zap", "semgrep"],
    "injection": ["zap", "semgrep"],
    "cross-site": ["zap", "semgrep"],
    "xss": ["zap", "semgrep"],
    "sql injection": ["zap", "semgrep"],
    "owasp": ["zap", "semgrep"],
    # Network security
    "network": ["nmap"],
    "port": ["nmap"],
    "firewall": ["nmap"],
    "open port": ["nmap"],
    "network security": ["nmap"],
    "encryption": ["nmap"],
    "tls": ["nmap"],
    "ssl": ["nmap"],
    "cryptograph": ["nmap"],
    # Code security
    "source code": ["semgrep"],
    "code review": ["semgrep"],
    "code analysis": ["semgrep"],
    "static analysis": ["semgrep"],
    "secure coding": ["semgrep"],
    "coding practices": ["semgrep"],
    "code quality": ["semgrep"],
    # Dependency / supply chain
    "dependency": ["osv"],
    "dependencies": ["osv"],
    "third-party": ["osv", "syft"],
    "third party": ["osv", "syft"],
    "supply chain": ["osv", "syft"],
    "software composition": ["osv", "syft"],
    "open source": ["osv", "syft"],
    "component": ["osv", "syft"],
    "library": ["osv"],
    "package": ["osv"],
    # SBOM
    "software bill of materials": ["syft"],
    "sbom": ["syft"],
    "bill of materials": ["syft"],
    "inventory": ["syft"],
    "asset inventory": ["syft"],
    # General security
    "exploitable": ["zap", "nmap", "osv", "semgrep"],
    "exploit": ["zap", "nmap", "osv", "semgrep"],
    "patch": ["osv"],
    "patching": ["osv"],
    "update": ["osv"],
    "remediat": ["zap", "nmap", "osv", "semgrep"],
    "security flaw": ["zap", "nmap", "osv", "semgrep"],
    "known vulnerabilit": ["osv"],
    "cve": ["osv"],
}

# Severity ordering for prioritizing findings (lower = more severe)
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
    "informational": 4,
    "unknown": 5,
}

# Keywords that indicate the question is about HAVING a capability (positive framing)
CAPABILITY_KEYWORDS = [
    "do you perform", "do you conduct", "is there", "are there",
    "do you have", "have you implemented", "is.*implemented",
    "do you use", "do you maintain", "are.*in place",
    "does.*include", "do you ensure",
]

# Keywords that indicate the question is about ABSENCE of issues (negative framing)
ABSENCE_KEYWORDS = [
    "without.*vulnerabilit", "no known.*vulnerabilit", "free.*from",
    "absence.*of", "without.*exploit", "no.*exploitable",
    "delivered.*without", "free.*of.*defect",
]

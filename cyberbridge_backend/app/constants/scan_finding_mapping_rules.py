# scan_finding_mapping_rules.py
# Auto-mapping rules linking scanner findings to risk categories.
# Each rule specifies patterns to match findings and the risk category names they map to.

MAPPING_RULES = [
    {
        "risk_patterns": ["sql injection"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["sql injection", "sqli"],
        "finding_identifier_patterns": ["CWE-89"],
    },
    {
        "risk_patterns": ["cross-site scripting", "xss"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["xss", "cross-site scripting", "cross site scripting"],
        "finding_identifier_patterns": ["CWE-79"],
    },
    {
        "risk_patterns": ["cross site request forgery", "csrf"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["csrf", "cross-site request forgery", "cross site request forgery"],
        "finding_identifier_patterns": ["CWE-352"],
    },
    {
        "risk_patterns": ["server side request forgery", "ssrf"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["ssrf", "server-side request forgery", "server side request forgery"],
        "finding_identifier_patterns": ["CWE-918"],
    },
    {
        "risk_patterns": ["broken or weak authentication", "authentication"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["authentication", "auth bypass", "broken auth", "weak password", "session fixation"],
        "finding_identifier_patterns": ["CWE-287", "CWE-306", "CWE-384"],
    },
    {
        "risk_patterns": ["security misconfiguration"],
        "scanner_types": ["zap", "semgrep", "nmap"],
        "finding_title_keywords": ["misconfiguration", "misconfigured", "default credentials", "directory listing", "server leaks"],
        "finding_identifier_patterns": ["CWE-16", "CWE-756"],
    },
    {
        "risk_patterns": ["unpatched vulnerability exploitation", "known vulnerabilit"],
        "scanner_types": ["osv", "nmap"],
        "finding_title_keywords": ["cve-", "vulnerability", "vulnerable version"],
        "finding_identifier_patterns": ["CVE-"],
    },
    {
        "risk_patterns": ["man in the middle", "man-in-the-middle"],
        "scanner_types": ["nmap", "zap"],
        "finding_title_keywords": ["ssl", "tls", "certificate", "insecure transport", "mixed content", "hsts"],
        "finding_identifier_patterns": ["CWE-295", "CWE-319"],
    },
    {
        "risk_patterns": ["unauthorized access"],
        "scanner_types": ["nmap"],
        "finding_title_keywords": ["open port", "exposed service", "unauthorized", "unprotected"],
        "finding_identifier_patterns": [],
    },
    {
        "risk_patterns": ["source code disclosure"],
        "scanner_types": ["semgrep", "zap"],
        "finding_title_keywords": ["secret", "hardcoded", "hard-coded", "api key", "password in source", "credential"],
        "finding_identifier_patterns": ["CWE-540", "CWE-798"],
    },
    {
        "risk_patterns": ["software supply chain", "supply chain"],
        "scanner_types": ["osv"],
        "finding_title_keywords": ["supply chain", "dependency", "malicious package"],
        "finding_identifier_patterns": [],
    },
    {
        "risk_patterns": ["input validation", "injection"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["injection", "command injection", "code injection", "ldap injection", "xpath injection", "input validation"],
        "finding_identifier_patterns": ["CWE-78", "CWE-94", "CWE-90", "CWE-91"],
    },
    {
        "risk_patterns": ["insufficient logging", "logging"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["logging", "log injection", "insufficient logging"],
        "finding_identifier_patterns": ["CWE-778", "CWE-117"],
    },
    {
        "risk_patterns": ["data breach", "sensitive data", "information disclosure"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["information disclosure", "sensitive data", "data exposure", "pii", "private information"],
        "finding_identifier_patterns": ["CWE-200", "CWE-359"],
    },
    {
        "risk_patterns": ["brute force", "denial of service"],
        "scanner_types": ["zap", "nmap"],
        "finding_title_keywords": ["brute force", "rate limit", "denial of service", "dos", "account lockout"],
        "finding_identifier_patterns": ["CWE-307"],
    },
    {
        "risk_patterns": ["dns spoofing", "dns"],
        "scanner_types": ["nmap"],
        "finding_title_keywords": ["dns", "dns spoofing", "dns cache"],
        "finding_identifier_patterns": [],
    },
    {
        "risk_patterns": ["path traversal", "directory traversal"],
        "scanner_types": ["zap", "semgrep"],
        "finding_title_keywords": ["path traversal", "directory traversal", "local file inclusion", "lfi"],
        "finding_identifier_patterns": ["CWE-22"],
    },
]

import os


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@cyberbridge_db:5432/postgres",
)

NMAP_SERVICE_URL = os.environ.get("NMAP_SERVICE_URL", "http://nmap:8000")
ZAP_SERVICE_URL = os.environ.get("ZAP_SERVICE_URL", "http://zap:8000")
SEMGREP_SERVICE_URL = os.environ.get("SEMGREP_SERVICE_URL", "http://semgrep:8000")
OSV_SERVICE_URL = os.environ.get("OSV_SERVICE_URL", "http://osv:8000")

# Polling intervals (seconds)
SCANNER_POLL_INTERVAL = int(os.environ.get("SCANNER_POLL_INTERVAL", "3600"))
MITRE_SYNC_INTERVAL = int(os.environ.get("MITRE_SYNC_INTERVAL", "604800"))  # weekly
KEV_SYNC_INTERVAL = int(os.environ.get("KEV_SYNC_INTERVAL", "86400"))  # daily

# Scanner targets (comma-separated)
NMAP_TARGETS = os.environ.get("NMAP_TARGETS", "127.0.0.1")
ZAP_TARGETS = os.environ.get("ZAP_TARGETS", "http://localhost")

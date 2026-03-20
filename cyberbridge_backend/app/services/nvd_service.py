# nvd_service.py
import httpx
import json
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy.orm import Session
from app.database.database import get_db
from app.repositories import nvd_repository
from app.models import models

logger = logging.getLogger(__name__)

# NVD API 2.0 base URL
NVD_API_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Rate limiting constants
RATE_LIMIT_WITHOUT_KEY = 5  # requests per 30 seconds
RATE_LIMIT_WITH_KEY = 50  # requests per 30 seconds
RATE_LIMIT_WINDOW = 30  # seconds
MAX_RESULTS_PER_PAGE = 2000


class CPEGenerator:
    """Generates CPE URIs from Nmap service detection data"""

    # Common vendor mappings for popular services
    VENDOR_MAPPINGS = {
        # SSH
        "openssh": "openbsd",
        "dropbear": "dropbear_ssh_project",
        # Web servers
        "nginx": "nginx",
        "apache": "apache",
        "httpd": "apache",
        "lighttpd": "lighttpd",
        "iis": "microsoft",
        "tomcat": "apache",
        "jetty": "eclipse",
        # Databases
        "mysql": "oracle",
        "mariadb": "mariadb",
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "mongodb": "mongodb",
        "redis": "redis",
        "memcached": "memcached",
        "mssql": "microsoft",
        "sql server": "microsoft",
        "oracle": "oracle",
        # Mail servers
        "postfix": "postfix",
        "sendmail": "sendmail",
        "exim": "exim",
        "dovecot": "dovecot",
        # FTP
        "vsftpd": "vsftpd_project",
        "proftpd": "proftpd",
        "pure-ftpd": "pureftpd",
        # DNS
        "bind": "isc",
        "named": "isc",
        "unbound": "nlnetlabs",
        "dnsmasq": "thekelleys",
        # Other common services
        "openssl": "openssl",
        "samba": "samba",
        "cups": "apple",
        "docker": "docker",
        "kubernetes": "kubernetes",
        "jenkins": "jenkins",
        "gitlab": "gitlab",
        "grafana": "grafana",
        "elasticsearch": "elastic",
        "kibana": "elastic",
        "logstash": "elastic",
        "rabbitmq": "pivotal_software",
        "zookeeper": "apache",
        "kafka": "apache",
        "hadoop": "apache",
        "spark": "apache",
        "cassandra": "apache",
        "couchdb": "apache",
        "php": "php",
        "python": "python",
        "perl": "perl",
        "ruby": "ruby-lang",
        "node": "nodejs",
        "nodejs": "nodejs",
        "java": "oracle",
        "openjdk": "openjdk",
    }

    # Product name normalizations
    PRODUCT_NORMALIZATIONS = {
        "httpd": "http_server",
        "apache httpd": "http_server",
        "apache http server": "http_server",
        "microsoft-iis": "internet_information_services",
        "iis": "internet_information_services",
        "sql server": "sql_server",
        "ms-sql": "sql_server",
        "mssql": "sql_server",
    }

    @classmethod
    def generate_cpe(cls, service_name: str, product: Optional[str] = None,
                     version: Optional[str] = None) -> Optional[str]:
        """
        Generate a CPE 2.3 URI from service information.

        Args:
            service_name: The service name (e.g., 'ssh', 'http')
            product: The product name (e.g., 'OpenSSH', 'nginx')
            version: The version string (e.g., '7.4', '1.18.0')

        Returns:
            CPE URI string or None if cannot generate
        """
        if not product:
            return None

        # Normalize product name
        product_lower = product.lower().strip()
        normalized_product = cls.PRODUCT_NORMALIZATIONS.get(product_lower, product_lower)
        # Remove special characters and spaces
        normalized_product = re.sub(r'[^a-z0-9_]', '_', normalized_product)
        normalized_product = re.sub(r'_+', '_', normalized_product).strip('_')

        # Get vendor
        vendor = cls._get_vendor(product_lower, service_name)
        if not vendor:
            vendor = normalized_product  # Use product name as vendor if unknown

        # Normalize vendor
        vendor = re.sub(r'[^a-z0-9_]', '_', vendor.lower())
        vendor = re.sub(r'_+', '_', vendor).strip('_')

        # Parse version
        version_part = cls._normalize_version(version) if version else "*"

        # Build CPE 2.3 URI
        # Format: cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other
        cpe = f"cpe:2.3:a:{vendor}:{normalized_product}:{version_part}:*:*:*:*:*:*:*"

        return cpe

    @classmethod
    def _get_vendor(cls, product: str, service_name: str) -> Optional[str]:
        """Get vendor for a product"""
        # Check direct product mapping
        if product in cls.VENDOR_MAPPINGS:
            return cls.VENDOR_MAPPINGS[product]

        # Check service name mapping
        service_lower = service_name.lower() if service_name else ""
        if service_lower in cls.VENDOR_MAPPINGS:
            return cls.VENDOR_MAPPINGS[service_lower]

        # Check if product name contains a known vendor
        for key, vendor in cls.VENDOR_MAPPINGS.items():
            if key in product:
                return vendor

        return None

    @classmethod
    def _normalize_version(cls, version: str) -> str:
        """Normalize version string for CPE"""
        if not version:
            return "*"

        # Remove common prefixes/suffixes
        version = version.strip()
        version = re.sub(r'^v\.?', '', version, flags=re.IGNORECASE)

        # Extract just the version number (e.g., "7.4p1" -> "7.4p1", "1.18.0-ubuntu" -> "1.18.0")
        # Keep alphanumeric and dots/hyphens that are part of version
        match = re.match(r'^([0-9]+(?:\.[0-9]+)*(?:[a-z][0-9]*)?)', version, re.IGNORECASE)
        if match:
            return match.group(1).lower()

        # Fallback: just clean the version string
        version = re.sub(r'[^a-z0-9._-]', '', version.lower())
        return version if version else "*"

    @classmethod
    def parse_cpe(cls, cpe_uri: str) -> Dict[str, str]:
        """Parse a CPE URI into components"""
        parts = cpe_uri.split(':')
        if len(parts) < 5:
            return {}

        return {
            "vendor": parts[3] if len(parts) > 3 else None,
            "product": parts[4] if len(parts) > 4 else None,
            "version": parts[5] if len(parts) > 5 and parts[5] != '*' else None,
        }


class NVDService:
    """Service for syncing CVE data from NVD API 2.0"""

    def __init__(self, db: Session, api_key: Optional[str] = None):
        self.db = db
        self.api_key = api_key
        self.rate_limit = RATE_LIMIT_WITH_KEY if api_key else RATE_LIMIT_WITHOUT_KEY
        self._request_times: List[datetime] = []

    async def _rate_limit_wait(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.utcnow()

        # Remove old request times
        self._request_times = [t for t in self._request_times
                              if (now - t).total_seconds() < RATE_LIMIT_WINDOW]

        if len(self._request_times) >= self.rate_limit:
            # Calculate wait time
            oldest = min(self._request_times)
            wait_time = RATE_LIMIT_WINDOW - (now - oldest).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time + 0.5)  # Add small buffer

        self._request_times.append(datetime.utcnow())

    async def fetch_cves(self, start_index: int = 0, results_per_page: int = 2000,
                        last_mod_start: Optional[datetime] = None,
                        last_mod_end: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch CVEs from NVD API"""
        await self._rate_limit_wait()

        params = {
            "startIndex": start_index,
            "resultsPerPage": min(results_per_page, MAX_RESULTS_PER_PAGE)
        }

        if last_mod_start:
            params["lastModStartDate"] = last_mod_start.strftime("%Y-%m-%dT%H:%M:%S.000")
        if last_mod_end:
            params["lastModEndDate"] = last_mod_end.strftime("%Y-%m-%dT%H:%M:%S.000")

        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(NVD_API_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    def parse_cve_item(self, cve_item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a CVE item from NVD API response"""
        cve = cve_item.get("cve", {})

        # Get CVE ID
        cve_id = cve.get("id", "")

        # Get description (English preferred)
        descriptions = cve.get("descriptions", [])
        description = None
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value")
                break
        if not description and descriptions:
            description = descriptions[0].get("value")

        # Get CVSS scores
        cvss_v3_score = None
        cvss_v3_severity = None
        cvss_v3_vector = None
        cvss_v2_score = None
        cvss_v2_severity = None

        metrics = cve.get("metrics", {})

        # Try CVSS 3.1 first, then 3.0
        for cvss_key in ["cvssMetricV31", "cvssMetricV30"]:
            if cvss_key in metrics and metrics[cvss_key]:
                cvss_data = metrics[cvss_key][0].get("cvssData", {})
                cvss_v3_score = cvss_data.get("baseScore")
                cvss_v3_severity = cvss_data.get("baseSeverity")
                cvss_v3_vector = cvss_data.get("vectorString")
                break

        # Get CVSS v2 if available
        if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
            cvss_data = metrics["cvssMetricV2"][0].get("cvssData", {})
            cvss_v2_score = cvss_data.get("baseScore")
            cvss_v2_severity = metrics["cvssMetricV2"][0].get("baseSeverity")

        # Get dates
        published_date = None
        last_modified_date = None
        if cve.get("published"):
            try:
                published_date = datetime.fromisoformat(cve["published"].replace("Z", "+00:00"))
            except:
                pass
        if cve.get("lastModified"):
            try:
                last_modified_date = datetime.fromisoformat(cve["lastModified"].replace("Z", "+00:00"))
            except:
                pass

        # Get references
        references = []
        for ref in cve.get("references", []):
            references.append({
                "url": ref.get("url"),
                "source": ref.get("source"),
                "tags": ref.get("tags", [])
            })

        # Get CWE IDs
        cwe_ids = []
        for weakness in cve.get("weaknesses", []):
            for desc in weakness.get("description", []):
                if desc.get("value", "").startswith("CWE-"):
                    cwe_ids.append(desc.get("value"))

        return {
            "cve_id": cve_id,
            "description": description,
            "cvss_v3_score": cvss_v3_score,
            "cvss_v3_severity": cvss_v3_severity,
            "cvss_v3_vector": cvss_v3_vector,
            "cvss_v2_score": cvss_v2_score,
            "cvss_v2_severity": cvss_v2_severity,
            "published_date": published_date,
            "last_modified_date": last_modified_date,
            "vuln_status": cve.get("vulnStatus"),
            "references": references,
            "cwe_ids": cwe_ids
        }

    def parse_cpe_configurations(self, cve_item: Dict[str, Any], cve_db_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Parse CPE configurations from CVE item"""
        cve = cve_item.get("cve", {})
        configurations = cve.get("configurations", [])
        cpe_matches = []

        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    criteria = cpe_match.get("criteria", "")

                    # Parse CPE components
                    parts = criteria.split(":")
                    vendor = parts[3] if len(parts) > 3 else None
                    product = parts[4] if len(parts) > 4 else None
                    version = parts[5] if len(parts) > 5 and parts[5] != '*' else None

                    cpe_matches.append({
                        "cve_id": cve_db_id,
                        "cpe_uri": criteria,
                        "cpe_vendor": vendor,
                        "cpe_product": product,
                        "cpe_version": version,
                        "version_start_including": cpe_match.get("versionStartIncluding"),
                        "version_start_excluding": cpe_match.get("versionStartExcluding"),
                        "version_end_including": cpe_match.get("versionEndIncluding"),
                        "version_end_excluding": cpe_match.get("versionEndExcluding"),
                        "vulnerable": cpe_match.get("vulnerable", True)
                    })

        return cpe_matches

    async def sync_cves(self, sync_status_id: uuid.UUID, full_sync: bool = False) -> Dict[str, int]:
        """
        Sync CVEs from NVD.

        Args:
            sync_status_id: ID of the sync status record to update
            full_sync: If True, fetch all CVEs; otherwise, incremental sync

        Returns:
            Dict with counts of processed, added, and updated CVEs
        """
        stats = {"processed": 0, "added": 0, "updated": 0}

        try:
            # Update status to in_progress
            nvd_repository.update_sync_status(self.db, sync_status_id, "in_progress")

            # Determine date range for sync
            last_mod_start = None
            last_mod_end = None

            if not full_sync:
                # Incremental sync - use date range
                settings = nvd_repository.get_nvd_settings(self.db)
                if settings and settings.last_sync_at:
                    last_mod_start = settings.last_sync_at - timedelta(hours=1)  # Buffer for safety
                else:
                    # First sync - default to last 30 days
                    last_mod_start = datetime.utcnow() - timedelta(days=30)
                last_mod_end = datetime.utcnow()
            # For full_sync, don't set date filters - fetch all CVEs

            # Fetch CVEs with pagination
            start_index = 0
            total_results = None

            while True:
                logger.info(f"Fetching CVEs from index {start_index}")

                response = await self.fetch_cves(
                    start_index=start_index,
                    results_per_page=MAX_RESULTS_PER_PAGE,
                    last_mod_start=last_mod_start,
                    last_mod_end=last_mod_end
                )

                if total_results is None:
                    total_results = response.get("totalResults", 0)
                    logger.info(f"Total CVEs to process: {total_results}")

                vulnerabilities = response.get("vulnerabilities", [])
                if not vulnerabilities:
                    break

                # Process each CVE
                for vuln_item in vulnerabilities:
                    try:
                        cve_data = self.parse_cve_item(vuln_item)

                        # Upsert CVE
                        cve_record, is_new = nvd_repository.upsert_cve(self.db, cve_data)

                        if is_new:
                            stats["added"] += 1
                        else:
                            stats["updated"] += 1

                        # Delete existing CPE matches and create new ones
                        nvd_repository.delete_cpe_matches_for_cve(self.db, cve_record.id)
                        cpe_matches = self.parse_cpe_configurations(vuln_item, cve_record.id)
                        if cpe_matches:
                            nvd_repository.bulk_create_cpe_matches(self.db, cpe_matches)

                        stats["processed"] += 1

                        # Update sync status periodically
                        if stats["processed"] % 100 == 0:
                            nvd_repository.update_sync_status(
                                self.db, sync_status_id, "in_progress",
                                stats["processed"], stats["added"], stats["updated"]
                            )
                            logger.info(f"Processed {stats['processed']}/{total_results} CVEs")

                    except Exception as e:
                        logger.error(f"Error processing CVE: {e}")
                        continue

                start_index += len(vulnerabilities)
                if start_index >= total_results:
                    break

            # Update last sync time
            nvd_repository.update_last_sync_time(self.db)

            # Mark sync as completed
            nvd_repository.update_sync_status(
                self.db, sync_status_id, "completed",
                stats["processed"], stats["added"], stats["updated"]
            )

            logger.info(f"NVD sync completed: {stats}")

        except Exception as e:
            logger.error(f"NVD sync failed: {e}")
            nvd_repository.update_sync_status(
                self.db, sync_status_id, "failed",
                stats["processed"], stats["added"], stats["updated"],
                str(e)
            )
            raise

        return stats


class VulnerabilityCorrelator:
    """Correlates Nmap scan results with CVE data"""

    def __init__(self, db: Session):
        self.db = db

    def correlate_scan(self, scan_history_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Correlate an Nmap scan with known CVEs.

        Args:
            scan_history_id: UUID of the scanner_history record

        Returns:
            List of found vulnerabilities
        """
        # Get the scan record
        scan = self.db.query(models.ScannerHistory).filter(
            models.ScannerHistory.id == scan_history_id,
            models.ScannerHistory.scanner_type == "nmap"
        ).first()

        if not scan:
            raise ValueError(f"Nmap scan not found: {scan_history_id}")

        # Delete existing correlations for this scan
        nvd_repository.delete_vulnerabilities_for_scan(self.db, scan_history_id)

        # Parse scan results
        try:
            results = json.loads(scan.results)
        except json.JSONDecodeError:
            raise ValueError("Invalid scan results format")

        found_vulnerabilities = []

        # Process each host/port/service
        services = self._extract_services(results)

        for service in services:
            vulnerabilities = self._find_vulnerabilities(service)
            for vuln in vulnerabilities:
                vuln["scan_history_id"] = scan_history_id
                nvd_repository.create_service_vulnerability(self.db, vuln)
                found_vulnerabilities.append(vuln)

        return found_vulnerabilities

    def _extract_services(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract services from Nmap scan results"""
        services = []

        # Handle different result formats
        # Format 1: Direct hosts array
        hosts = scan_results.get("hosts", [])
        if not hosts:
            # Format 2: Nested in raw_data
            raw_data = scan_results.get("raw_data", {})
            hosts = raw_data.get("hosts", [])

        for host in hosts:
            host_addr = host.get("ip") or host.get("address") or host.get("host")
            if not host_addr:
                continue

            ports = host.get("ports", [])
            for port_info in ports:
                port = port_info.get("port") or port_info.get("portid")
                if not port:
                    continue

                service = port_info.get("service", {})
                if isinstance(service, str):
                    service = {"name": service}

                services.append({
                    "host": host_addr,
                    "port": int(port),
                    "protocol": port_info.get("protocol", "tcp"),
                    "service_name": service.get("name"),
                    "service_product": service.get("product"),
                    "service_version": service.get("version"),
                    "service_extrainfo": service.get("extrainfo"),
                    "cpe": service.get("cpe") or port_info.get("cpe")  # Some formats include CPE directly
                })

        return services

    def _find_vulnerabilities(self, service: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find vulnerabilities for a service"""
        vulnerabilities = []

        product = service.get("service_product")
        version = service.get("service_version")
        service_name = service.get("service_name")

        if not product:
            # Try to use service name as product
            product = service_name

        if not product:
            return []

        # Generate CPE
        generated_cpe = CPEGenerator.generate_cpe(service_name, product, version)
        if not generated_cpe:
            return []

        # Parse the generated CPE
        cpe_parts = CPEGenerator.parse_cpe(generated_cpe)
        vendor = cpe_parts.get("vendor")
        product_normalized = cpe_parts.get("product")

        if not vendor or not product_normalized:
            return []

        # Find matching CVEs
        cpe_matches = nvd_repository.find_cpe_matches(
            self.db, vendor, product_normalized, version
        )

        for cpe_match in cpe_matches:
            # Determine match type and confidence
            match_type = "exact"
            confidence = 100

            if version:
                if cpe_match.cpe_version and cpe_match.cpe_version != version:
                    if cpe_match.version_start_including or cpe_match.version_end_including:
                        match_type = "version_range"
                        confidence = 90
            else:
                match_type = "product_only"
                confidence = 60

            vulnerabilities.append({
                "cve_id": cpe_match.cve_id,
                "host": service["host"],
                "port": service["port"],
                "protocol": service.get("protocol", "tcp"),
                "service_name": service_name,
                "service_product": product,
                "service_version": version,
                "generated_cpe": generated_cpe,
                "confidence": confidence,
                "match_type": match_type
            })

        return vulnerabilities


# Scheduled job entry point
async def run_nvd_sync():
    """Entry point for scheduled NVD sync job"""
    logger.info("Starting scheduled NVD sync")

    db = next(get_db())
    try:
        # Check if sync is enabled
        settings = nvd_repository.get_nvd_settings(db)
        if not settings:
            # Create default settings
            settings = nvd_repository.create_nvd_settings(db)

        if not settings.sync_enabled:
            logger.info("NVD sync is disabled")
            return

        # Check if another sync is already running
        if nvd_repository.is_sync_in_progress(db):
            logger.info("Another NVD sync is already in progress")
            return

        # Create sync status
        sync_status = nvd_repository.create_sync_status(db, sync_type="incremental")

        # Run sync
        service = NVDService(db, settings.api_key)
        await service.sync_cves(sync_status.id, full_sync=False)

        logger.info("Scheduled NVD sync completed")

    except Exception as e:
        logger.error(f"Scheduled NVD sync failed: {e}")
    finally:
        db.close()

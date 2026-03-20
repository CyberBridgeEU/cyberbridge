import logging

import httpx

from ..config import NMAP_SERVICE_URL, NMAP_TARGETS
from .base import BaseConnector

logger = logging.getLogger(__name__)


class NmapConnector(BaseConnector):
    source_name = "nmap"

    def __init__(self):
        self.nmap_url = NMAP_SERVICE_URL.rstrip("/")
        self.targets = [t.strip() for t in NMAP_TARGETS.split(",") if t.strip()]

    async def fetch_raw_data(self) -> list[dict]:
        results = []
        async with httpx.AsyncClient(timeout=120) as client:
            for target in self.targets:
                try:
                    resp = await client.get(
                        f"{self.nmap_url}/scan/basic",
                        params={"target": target},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    if not data.get("success"):
                        continue

                    nmaprun = (data.get("output") or {}).get("nmaprun", {})
                    hosts = self._normalize_hosts(nmaprun)

                    for host in hosts:
                        ip = self._get_host_ip(host)
                        if not ip:
                            continue
                        ports = self._normalize_ports(host.get("ports", {}))
                        for port_entry in ports:
                            state_info = port_entry.get("state", {})
                            state = state_info.get("@state", "") if isinstance(state_info, dict) else ""
                            if state != "open":
                                continue
                            results.append({"ip": ip, "port_entry": port_entry})

                except httpx.ConnectError:
                    logger.warning("[Nmap] Cannot reach Nmap API at %s", self.nmap_url)
                except Exception as e:
                    logger.error("[Nmap] Error scanning %s: %s", target, e)
        return results

    def normalize(self, raw_item: dict) -> dict:
        ip = raw_item["ip"]
        port_entry = raw_item["port_entry"]

        port_str = port_entry.get("@portid", "0")
        protocol = port_entry.get("@protocol", "tcp").lower()

        service_info = port_entry.get("service", {})
        service = service_info.get("@name", "") if isinstance(service_info, dict) else ""

        try:
            port_num = int(port_str)
        except ValueError:
            port_num = 0

        labels = [
            f"nmap-port-{port_str}",
            f"nmap-protocol-{protocol}",
            "nmap-state-open",
        ]
        if service:
            labels.append(f"nmap-service-{service}")

        service_display = service or "unknown"

        return {
            "name": f"Nmap: open {protocol}/{port_str} on {ip} ({service_display})",
            "description": f"Nmap scan discovered open {protocol} port {port_str} on host {ip}. Service: {service_display}.",
            "confidence": 60,
            "pattern": (
                f"[network-traffic:dst_ref.type = 'ipv4-addr' AND "
                f"network-traffic:dst_ref.value = '{ip}' AND "
                f"network-traffic:dst_port = {port_num}]"
            ),
            "labels": labels,
            "severity": None,
            "ip_address": ip,
            "port": port_num,
            "protocol": protocol,
            "service_name": service,
        }

    def dedup_key(self, normalized: dict) -> str:
        return f"nmap-{normalized['ip_address']}-{normalized['protocol']}-{normalized['port']}"

    # --- Nmap XML parsing helpers (same logic as original connector) ---

    def _normalize_hosts(self, nmaprun: dict) -> list[dict]:
        host_raw = nmaprun.get("host")
        if host_raw is None:
            return []
        if isinstance(host_raw, dict):
            return [host_raw]
        if isinstance(host_raw, list):
            return host_raw
        return []

    def _normalize_ports(self, ports_section: dict) -> list[dict]:
        if not ports_section:
            return []
        port_raw = ports_section.get("port")
        if port_raw is None:
            return []
        if isinstance(port_raw, dict):
            return [port_raw]
        if isinstance(port_raw, list):
            return port_raw
        return []

    def _get_host_ip(self, host: dict) -> str:
        address = host.get("address", {})
        if isinstance(address, dict):
            return address.get("@addr", "")
        if isinstance(address, list):
            for addr in address:
                if isinstance(addr, dict) and addr.get("@addrtype", "") == "ipv4":
                    return addr.get("@addr", "")
            if address:
                return address[0].get("@addr", "")
        return ""

import asyncio
import logging
import requests
import httpx
import json
import os
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session

from app.models import models

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM (llama.cpp and QLON Ai) for AI-powered operations."""

    # llama.cpp endpoints (separate container on port 11435)
    DEFAULT_LLAMACPP_URL_DEV = "http://localhost:11435/v1/chat/completions"
    DEFAULT_LLAMACPP_URL_PROD = "http://llamacpp:11435/v1/chat/completions"

    QLON_CHAT_ENDPOINT = "/v1/chat/completions"

    def __init__(self, db: Session):
        self.db = db
        self.llm_backend = "llamacpp"  # Default; routers override based on org settings
        self.llamacpp_url = self._get_llamacpp_url()

    def _is_production_environment(self) -> bool:
        """Check if we're running in production (Docker) environment."""
        container_env = os.getenv("CONTAINER_ENV")
        db_host = os.getenv("DB_HOST")
        return container_env == "docker" or db_host is not None

    def _get_llamacpp_url(self) -> str:
        """Get llama.cpp URL based on environment."""
        if self._is_production_environment():
            logger.info(f"Production environment. llama.cpp URL: {self.DEFAULT_LLAMACPP_URL_PROD}")
            return self.DEFAULT_LLAMACPP_URL_PROD
        else:
            logger.info(f"Development environment. llama.cpp URL: {self.DEFAULT_LLAMACPP_URL_DEV}")
            return self.DEFAULT_LLAMACPP_URL_DEV

    def _get_optimization_settings(self) -> dict:
        """Get LLM optimization settings from database or use defaults."""
        try:
            settings = self.db.query(models.LLMSettings).first()
            if settings:
                return {
                    "max_questions_per_framework": settings.max_questions_per_framework,
                    "timeout": settings.llm_timeout_seconds,
                    "min_confidence": settings.min_confidence_threshold,
                    "max_correlations": settings.max_correlations
                }
        except Exception as e:
            logger.warning(f"Could not load LLM optimization settings: {str(e)}")

        # Return defaults if no settings found
        return {
            "max_questions_per_framework": 10,
            "timeout": 300,
            "min_confidence": 75,
            "max_correlations": 10
        }

    async def generate_text(self, prompt: str, model: str = None, stream: bool = False, timeout: int = 120) -> str:
        """
        Generate text using the LLM (async version).
        Uses the llama.cpp backend.

        Args:
            prompt: The prompt to send to the LLM
            model: Model name (unused, kept for API compatibility)
            stream: Whether to stream the response
            timeout: Request timeout in seconds

        Returns:
            Generated text response
        """
        return await self._generate_text_llamacpp(prompt, stream, timeout)

    async def _generate_text_llamacpp(self, prompt: str, stream: bool = False, timeout: int = 120) -> str:
        """Generate text using the llama.cpp backend (OpenAI-compatible chat completions API).

        Uses streaming so llama.cpp sends tokens incrementally via SSE.
        Cancellation is handled at the caller level via asyncio task cancellation.
        """
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4096,
            "temperature": 0.3,
            "top_p": 0.9,
            "stream": True
        }

        try:
            logger.info(f"Sending streaming request to llama.cpp at {self.llamacpp_url}")
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    self.llamacpp_url,
                    json=payload,
                    timeout=timeout
                ) as response:
                    response.raise_for_status()

                    full_response = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if delta.get("content") is not None:
                                full_response += delta["content"]

                    return full_response

        except httpx.TimeoutException:
            logger.error("llama.cpp request timed out")
            raise Exception("LLM request timed out. Please try again or reduce the number of questions.")
        except httpx.ConnectError:
            logger.error(f"Could not connect to llama.cpp at {self.llamacpp_url}")
            raise Exception("Could not connect to LLM service. Please ensure the llama.cpp server is running.")
        except Exception as e:
            logger.error(f"Error calling llama.cpp: {str(e)}")
            raise Exception(f"Error calling LLM: {str(e)}")

    async def analyze_question_correlations(
        self,
        questions_a: List[Dict[str, Any]],
        questions_b: List[Dict[str, Any]],
        framework_a_name: str,
        framework_b_name: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze questions from two frameworks and suggest correlations using AI.

        Args:
            questions_a: List of questions from framework A with 'id' and 'text' keys
            questions_b: List of questions from framework B with 'id' and 'text' keys
            framework_a_name: Name of framework A
            framework_b_name: Name of framework B

        Returns:
            List of correlation suggestions with structure:
            [
                {
                    "question_a_id": "...",
                    "question_b_id": "...",
                    "confidence": 85,
                    "reasoning": "Both questions address...",
                    "question_a_text": "...",
                    "question_b_text": "..."
                }
            ]
        """
        logger.info(f"Analyzing correlations between {len(questions_a)} questions from {framework_a_name} and {len(questions_b)} from {framework_b_name}")

        # Get optimization settings from database
        opt_settings = self._get_optimization_settings()

        # Build the prompt for the LLM
        prompt = self._build_correlation_prompt(
            questions_a, questions_b, framework_a_name, framework_b_name, opt_settings
        )

        try:
            # Call the LLM with configurable timeout
            response_text = await self.generate_text(prompt, timeout=opt_settings["timeout"])

            # Parse the response
            suggestions = self._parse_correlation_response(
                response_text, questions_a, questions_b
            )

            logger.info(f"LLM suggested {len(suggestions)} correlations")
            return suggestions

        except Exception as e:
            logger.error(f"Error analyzing correlations with LLM: {str(e)}")
            raise

    def _build_correlation_prompt(
        self,
        questions_a: List[Dict[str, Any]],
        questions_b: List[Dict[str, Any]],
        framework_a_name: str,
        framework_b_name: str,
        opt_settings: dict
    ) -> str:
        """Build the prompt for correlation analysis."""

        # Limit questions based on configuration
        max_questions = opt_settings["max_questions_per_framework"]
        questions_a_limited = questions_a[:max_questions]
        questions_b_limited = questions_b[:max_questions]

        prompt = f"""You are an expert in cybersecurity compliance frameworks. Your task is to analyze questions from two different frameworks and identify which questions are semantically similar or address the same compliance requirements.

Framework A: {framework_a_name}
Framework B: {framework_b_name}

Questions from {framework_a_name}:
"""

        for i, q in enumerate(questions_a_limited, 1):
            # Truncate very long questions to save tokens
            text = q['text'][:300] + "..." if len(q['text']) > 300 else q['text']
            prompt += f"{i}. [ID: {q['id']}] {text}\n"

        prompt += f"\n\nQuestions from {framework_b_name}:\n"

        for i, q in enumerate(questions_b_limited, 1):
            text = q['text'][:300] + "..." if len(q['text']) > 300 else q['text']
            prompt += f"{i}. [ID: {q['id']}] {text}\n"

        prompt += """

Your task:
1. Analyze the questions from both frameworks
2. Identify pairs of questions that are semantically similar or address the same compliance requirement
3. Provide a confidence score (0-100) for each correlation
4. Provide a brief reasoning for each correlation

IMPORTANT: Output ONLY valid JSON with no additional text before or after. Use this exact format:

```json
{
  "correlations": [
    {
      "question_a_id": "uuid-from-framework-a",
      "question_b_id": "uuid-from-framework-b",
      "confidence": 95,
      "reasoning": "Both questions address the requirement for..."
    }
  ]
}
```

Guidelines:
- Only suggest correlations with confidence >= {opt_settings["min_confidence"]}%
- Focus on questions with similar intent, not just similar keywords
- Consider the compliance requirements being addressed
- Limit to the most relevant correlations (maximum {opt_settings["max_correlations"]})
- Include only the JSON output, no explanations before or after
"""

        return prompt

    def _parse_correlation_response(
        self,
        response_text: str,
        questions_a: List[Dict[str, Any]],
        questions_b: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse the LLM response and extract correlation suggestions."""

        try:
            # Extract JSON from the response (in case there's text before/after)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in LLM response")
                return []

            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            if "correlations" not in data:
                logger.warning("No correlations field in response")
                return []

            # Build lookup dictionaries for quick access
            questions_a_dict = {q['id']: q for q in questions_a}
            questions_b_dict = {q['id']: q for q in questions_b}

            suggestions = []
            for corr in data["correlations"]:
                question_a_id = corr.get("question_a_id")
                question_b_id = corr.get("question_b_id")

                # Validate that the question IDs exist
                if question_a_id not in questions_a_dict or question_b_id not in questions_b_dict:
                    logger.warning(f"Invalid question IDs in suggestion: {question_a_id}, {question_b_id}")
                    continue

                suggestions.append({
                    "question_a_id": question_a_id,
                    "question_b_id": question_b_id,
                    "confidence": corr.get("confidence", 0),
                    "reasoning": corr.get("reasoning", ""),
                    "question_a_text": questions_a_dict[question_a_id]['text'],
                    "question_b_text": questions_b_dict[question_b_id]['text']
                })

            # Sort by confidence descending
            suggestions.sort(key=lambda x: x['confidence'], reverse=True)

            return suggestions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return []

    async def process_nmap_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Nmap scan results with LLM analysis.

        Args:
            raw_results: Raw Nmap scan output in JSON format

        Returns:
            Human-readable analysis with security insights
        """
        try:
            logger.info("🔍 Starting Nmap results processing with LLM")
            # Extract key information from Nmap results
            summary = self._extract_nmap_summary(raw_results)
            logger.info(f"📊 Extracted summary: {summary.get('total_hosts', 0)} hosts, {summary.get('total_ports', 0)} ports")

            if not summary.get("hosts"):
                return {
                    "success": True,
                    "analysis": "No hosts were detected in the scan results.",
                    "raw_data": raw_results
                }

            # Build prompt for LLM
            prompt = f"""Analyze this network scan and provide security insights:

Scan Summary:
- Total Hosts: {summary['total_hosts']}
- Hosts Up: {summary['hosts_up']}
- Total Open Ports: {summary['total_ports']}

Host Details:
"""

            for host in summary['hosts'][:5]:  # Limit to first 5 hosts
                prompt += f"\nHost: {host['address']}"
                if host.get('hostname'):
                    prompt += f" ({host['hostname']})"
                prompt += f"\n  Status: {host['status']}"

                if host['ports']:
                    prompt += f"\n  Open Ports ({len(host['ports'])}):"
                    for port in host['ports'][:10]:  # Limit to first 10 ports
                        prompt += f"\n    - {port['port']}/{port['protocol']}: {port['service']}"
                        if port.get('version'):
                            prompt += f" ({port['version']})"
                        if port.get('banner'):
                            prompt += f"\n      Banner: {port['banner']}"
                        if port.get('cpe'):
                            prompt += f"\n      CPE: {', '.join(port['cpe'][:3])}"
                        if port.get('scripts'):
                            for script in port['scripts'][:2]:
                                prompt += f"\n      Script [{script['id']}]: {script['output'][:150]}"

            prompt += """

Provide a concise security analysis covering:
1. Critical security findings (open ports, vulnerable services)
2. Potential security risks
3. Recommended actions

Keep the response focused and actionable."""

            # Call LLM
            logger.info(f"🤖 Calling LLM at {self.llamacpp_url} with prompt length: {len(prompt)} chars")
            analysis = await self.generate_text(prompt, timeout=120)
            logger.info(f"✅ LLM analysis completed, response length: {len(analysis)} chars")

            return {
                "success": True,
                "analysis": analysis,
                "summary": summary,
                "raw_data": raw_results
            }

        except Exception as e:
            logger.error(f"❌ Error processing Nmap results with LLM: {str(e)}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Return formatted fallback
            summary = self._extract_nmap_summary(raw_results)
            logger.info("📝 Returning fallback formatted results instead of LLM analysis")
            return {
                "success": True,
                "analysis": self._format_nmap_fallback(summary),
                "summary": summary,
                "raw_data": raw_results
            }

    def _extract_nmap_summary(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from raw Nmap results."""
        try:
            summary = {
                "total_hosts": 0,
                "hosts_up": 0,
                "total_ports": 0,
                "hosts": []
            }

            if not raw_results.get("success"):
                return summary

            output = raw_results.get("output", {})
            nmaprun = output.get("nmaprun", {})

            # Handle both single host and multiple hosts
            host_data = nmaprun.get("host")
            if not host_data:
                return summary

            hosts = host_data if isinstance(host_data, list) else [host_data]
            summary["total_hosts"] = len(hosts)

            for host in hosts:
                status = host.get("status", {}).get("@state", "unknown")
                if status == "up":
                    summary["hosts_up"] += 1

                address = host.get("address", {})
                addr = address.get("@addr", "unknown") if isinstance(address, dict) else "unknown"

                hostname = ""
                if "hostnames" in host and host["hostnames"]:
                    hostnames = host["hostnames"].get("hostname", [])
                    if hostnames:
                        hostname = hostnames[0].get("@name", "") if isinstance(hostnames, list) else hostnames.get("@name", "")

                ports_list = []
                if "ports" in host and host["ports"]:
                    port_data = host["ports"].get("port", [])
                    ports = port_data if isinstance(port_data, list) else [port_data]

                    for port in ports:
                        if isinstance(port, dict):
                            state = port.get("state", {})
                            if state.get("@state") == "open":
                                service = port.get("service", {})

                                # Build version string with product and version
                                product = service.get("@product", "")
                                version = service.get("@version", "")
                                version_str = f"{product} {version}".strip()

                                # Extract service banner/extra info
                                extrainfo = service.get("@extrainfo", "")
                                ostype = service.get("@ostype", "")

                                # Build banner string from available info
                                banner_parts = []
                                if extrainfo:
                                    banner_parts.append(extrainfo)
                                if ostype:
                                    banner_parts.append(f"OS: {ostype}")
                                banner = " | ".join(banner_parts) if banner_parts else ""

                                # Extract CPE (Common Platform Enumeration)
                                cpe_list = []
                                cpe_data = service.get("cpe", [])
                                if cpe_data:
                                    # Handle single CPE or list of CPEs
                                    if isinstance(cpe_data, list):
                                        cpe_list = [c for c in cpe_data if isinstance(c, str)]
                                    elif isinstance(cpe_data, str):
                                        cpe_list = [cpe_data]

                                # Extract script output (NSE scripts can contain banner info)
                                scripts = []
                                script_data = port.get("script", [])
                                if script_data:
                                    script_list = script_data if isinstance(script_data, list) else [script_data]
                                    for script in script_list:
                                        if isinstance(script, dict):
                                            script_id = script.get("@id", "")
                                            script_output = script.get("@output", "")
                                            if script_output:
                                                scripts.append({
                                                    "id": script_id,
                                                    "output": script_output[:500]  # Limit output length
                                                })

                                ports_list.append({
                                    "port": port.get("@portid", ""),
                                    "protocol": port.get("@protocol", ""),
                                    "service": service.get("@name", "unknown"),
                                    "version": version_str,
                                    "banner": banner,
                                    "cpe": cpe_list,
                                    "scripts": scripts
                                })

                    summary["total_ports"] += len(ports_list)

                summary["hosts"].append({
                    "address": addr,
                    "hostname": hostname,
                    "status": status,
                    "ports": ports_list
                })

            return summary

        except Exception as e:
            logger.error(f"Error extracting Nmap summary: {str(e)}")
            return {"total_hosts": 0, "hosts_up": 0, "total_ports": 0, "hosts": []}

    def _format_nmap_fallback(self, summary: Dict[str, Any]) -> str:
        """Format Nmap summary as human-readable text when LLM fails."""
        text = f"Network Scan Results:\n\n"
        text += f"Total Hosts Scanned: {summary['total_hosts']}\n"
        text += f"Hosts Up: {summary['hosts_up']}\n"
        text += f"Total Open Ports: {summary['total_ports']}\n\n"

        if summary['hosts']:
            text += "Host Details:\n"
            for host in summary['hosts'][:5]:
                text += f"\n{'='*60}\n"
                text += f"Host: {host['address']}"
                if host.get('hostname'):
                    text += f" ({host['hostname']})"
                text += f"\nStatus: {host['status']}\n"

                if host['ports']:
                    text += f"\nOpen Ports ({len(host['ports'])}):\n"
                    text += f"{'-'*40}\n"
                    for port in host['ports'][:15]:
                        # Port and service info
                        text += f"\n  Port {port['port']}/{port['protocol']}: {port['service']}"
                        if port.get('version'):
                            text += f"\n    Version: {port['version']}"
                        if port.get('banner'):
                            text += f"\n    Banner: {port['banner']}"

                        # CPE (Common Platform Enumeration)
                        cpe_list = port.get('cpe', [])
                        if cpe_list:
                            text += f"\n    CPE:"
                            for cpe in cpe_list[:5]:  # Limit to 5 CPEs per port
                                text += f"\n      • {cpe}"

                        # Script output (service detection scripts often contain banners)
                        scripts = port.get('scripts', [])
                        if scripts:
                            text += f"\n    Script Output:"
                            for script in scripts[:3]:  # Limit to 3 scripts per port
                                text += f"\n      [{script['id']}]: {script['output'][:200]}"
                                if len(script['output']) > 200:
                                    text += "..."
                        text += "\n"

        return text

    async def process_semgrep_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Semgrep scan results with LLM analysis.

        Args:
            raw_results: Raw Semgrep scan output in JSON format

        Returns:
            Human-readable analysis with security insights
        """
        try:
            # Extract key information from Semgrep results
            summary = self._extract_semgrep_summary(raw_results)

            if not summary.get("findings"):
                return {
                    "success": True,
                    "analysis": "No security issues were found in the code scan.",
                    "raw_data": raw_results
                }

            # Build prompt for LLM
            prompt = f"""Analyze this code security scan and provide insights:

Scan Summary:
- Total Findings: {summary['total_findings']}
- By Severity: ERROR: {summary['by_severity']['ERROR']}, WARNING: {summary['by_severity']['WARNING']}, INFO: {summary['by_severity']['INFO']}

Top Findings (limited to 20):
"""

            for idx, finding in enumerate(summary['findings'][:20], 1):
                prompt += f"\n{idx}. [{finding['severity']}] {finding['check_id']}"
                prompt += f"\n   File: {finding['file']}:{finding['line']}"
                prompt += f"\n   Message: {finding['message'][:200]}"
                if len(finding['message']) > 200:
                    prompt += "..."
                prompt += "\n"

            prompt += """

Provide a concise security analysis covering:
1. Most critical vulnerabilities found
2. Common security patterns identified
3. Recommended remediation priorities

Keep the response focused and actionable."""

            # Call LLM
            analysis = await self.generate_text(prompt, timeout=120)

            return {
                "success": True,
                "analysis": analysis,
                "summary": summary,
                "raw_data": raw_results
            }

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error processing Semgrep results with LLM: {str(e)}")
            # Return formatted fallback
            summary = self._extract_semgrep_summary(raw_results)
            return {
                "success": True,
                "analysis": self._format_semgrep_fallback(summary),
                "summary": summary,
                "raw_data": raw_results
            }

    def _extract_semgrep_summary(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from raw Semgrep results."""
        try:
            summary = {
                "total_findings": 0,
                "by_severity": {"ERROR": 0, "WARNING": 0, "INFO": 0},
                "findings": []
            }

            results = raw_results.get("results", [])
            summary["total_findings"] = len(results)

            for result in results:
                severity = result.get("extra", {}).get("severity", "INFO").upper()
                summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

                summary["findings"].append({
                    "severity": severity,
                    "check_id": result.get("check_id", "unknown"),
                    "file": result.get("path", "unknown"),
                    "line": result.get("start", {}).get("line", 0),
                    "message": result.get("extra", {}).get("message", "No message"),
                    "code": result.get("extra", {}).get("lines", "")
                })

            # Sort by severity (ERROR > WARNING > INFO)
            severity_order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
            summary["findings"].sort(key=lambda x: severity_order.get(x["severity"], 3))

            return summary

        except Exception as e:
            logger.error(f"Error extracting Semgrep summary: {str(e)}")
            return {"total_findings": 0, "by_severity": {}, "findings": []}

    def _format_semgrep_fallback(self, summary: Dict[str, Any]) -> str:
        """Format Semgrep summary as human-readable text when LLM fails."""
        text = f"Code Security Scan Results:\n\n"
        text += f"Total Findings: {summary['total_findings']}\n"
        text += f"By Severity:\n"
        for severity, count in summary['by_severity'].items():
            text += f"  • {severity}: {count}\n"
        text += "\n"

        if summary['findings']:
            text += "Top Security Issues (limited to 20):\n\n"
            for idx, finding in enumerate(summary['findings'][:20], 1):
                text += f"{idx}. [{finding['severity']}] {finding['check_id']}\n"
                text += f"   File: {finding['file']}:{finding['line']}\n"
                text += f"   {finding['message'][:200]}\n"
                if len(finding['message']) > 200:
                    text += "   ...\n"
                text += "\n"

        return text

    async def process_osv_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process OSV vulnerability scan results with LLM analysis.

        Args:
            raw_results: Raw OSV scan output in JSON format

        Returns:
            Human-readable analysis with security insights
        """
        try:
            # Extract key information from OSV results
            summary = self._extract_osv_summary(raw_results)

            if not summary.get("vulnerabilities"):
                return {
                    "success": True,
                    "analysis": "No vulnerabilities were found in the scanned dependencies.",
                    "raw_data": raw_results
                }

            # Build prompt for LLM
            prompt = f"""Analyze this dependency vulnerability scan and provide insights:

Scan Summary:
- Total Packages Scanned: {summary['total_packages']}
- Vulnerable Packages: {summary['vulnerable_packages']}
- Total Vulnerabilities: {summary['total_vulnerabilities']}

Vulnerable Packages (limited to 15):
"""

            for pkg in summary['vulnerabilities'][:15]:
                prompt += f"\nPackage: {pkg['package']} (Ecosystem: {pkg['ecosystem']})"
                prompt += f"\n  Vulnerabilities: {len(pkg['vulns'])}"
                for vuln in pkg['vulns'][:5]:  # Limit to first 5 vulnerabilities per package
                    prompt += f"\n    - {vuln['id']}: {vuln['summary'][:150]}"
                    if len(vuln['summary']) > 150:
                        prompt += "..."
                prompt += "\n"

            prompt += """

Provide a concise security analysis covering:
1. Most critical vulnerabilities that should be addressed immediately
2. Patterns in vulnerable dependencies
3. Recommended remediation actions

Keep the response focused and actionable."""

            # Call LLM
            analysis = await self.generate_text(prompt, timeout=120)

            return {
                "success": True,
                "analysis": analysis,
                "summary": summary,
                "raw_data": raw_results
            }

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error processing OSV results with LLM: {str(e)}")
            # Return formatted fallback
            summary = self._extract_osv_summary(raw_results)
            return {
                "success": True,
                "analysis": self._format_osv_fallback(summary),
                "summary": summary,
                "raw_data": raw_results
            }

    def _extract_osv_summary(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from raw OSV results."""
        try:
            summary = {
                "total_packages": 0,
                "vulnerable_packages": 0,
                "total_vulnerabilities": 0,
                "vulnerabilities": []
            }

            results = raw_results.get("results", [])

            for result in results:
                packages = result.get("packages", [])
                summary["total_packages"] += len(packages)

                for package in packages:
                    vulns = package.get("vulnerabilities", [])
                    if vulns:
                        summary["vulnerable_packages"] += 1
                        summary["total_vulnerabilities"] += len(vulns)

                        vuln_list = []
                        for vuln in vulns:
                            vuln_list.append({
                                "id": vuln.get("id", "unknown"),
                                "summary": vuln.get("summary", "No summary available"),
                                "severity": vuln.get("database_specific", {}).get("severity", "UNKNOWN")
                            })

                        summary["vulnerabilities"].append({
                            "package": package.get("package", {}).get("name", "unknown"),
                            "version": package.get("package", {}).get("version", "unknown"),
                            "ecosystem": package.get("package", {}).get("ecosystem", "unknown"),
                            "vulns": vuln_list
                        })

            # Sort by number of vulnerabilities (descending)
            summary["vulnerabilities"].sort(key=lambda x: len(x["vulns"]), reverse=True)

            return summary

        except Exception as e:
            logger.error(f"Error extracting OSV summary: {str(e)}")
            return {"total_packages": 0, "vulnerable_packages": 0, "total_vulnerabilities": 0, "vulnerabilities": []}

    def _format_osv_fallback(self, summary: Dict[str, Any]) -> str:
        """Format OSV summary as human-readable text when LLM fails."""
        text = f"Dependency Vulnerability Scan Results:\n\n"
        text += f"Total Packages Scanned: {summary['total_packages']}\n"
        text += f"Vulnerable Packages: {summary['vulnerable_packages']}\n"
        text += f"Total Vulnerabilities: {summary['total_vulnerabilities']}\n\n"

        if summary['vulnerabilities']:
            text += "Vulnerable Packages (limited to 15):\n\n"
            for pkg in summary['vulnerabilities'][:15]:
                text += f"Package: {pkg['package']} v{pkg['version']} ({pkg['ecosystem']})\n"
                text += f"  Vulnerabilities: {len(pkg['vulns'])}\n"
                for vuln in pkg['vulns'][:5]:
                    text += f"    • {vuln['id']}: {vuln['summary'][:150]}\n"
                    if len(vuln['summary']) > 150:
                        text += "      ...\n"
                text += "\n"

        return text

    async def process_syft_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Syft SBOM results with LLM analysis.

        Args:
            raw_results: Raw Syft CycloneDX JSON output

        Returns:
            Human-readable analysis with supply chain insights
        """
        try:
            # Extract key information from Syft results
            summary = self._extract_syft_summary(raw_results)

            if not summary.get("components"):
                return {
                    "success": True,
                    "analysis": "No software components were detected in the scanned project.",
                    "raw_data": raw_results
                }

            # Build prompt for LLM
            prompt = f"""Analyze this Software Bill of Materials (SBOM) and provide supply chain security insights:

SBOM Summary:
- Total Components: {summary['total_components']}
- Component Types: {', '.join(f"{k}: {v}" for k, v in summary['by_type'].items())}
- Unique Licenses: {len(summary['licenses'])}
- Licenses Found: {', '.join(list(summary['licenses'])[:10])}

Top Components (limited to 30):
"""

            for idx, comp in enumerate(summary['components'][:30], 1):
                prompt += f"\n{idx}. {comp['name']} v{comp['version']} (type: {comp['type']})"
                if comp.get('licenses'):
                    prompt += f" [License: {', '.join(comp['licenses'][:3])}]"
                if comp.get('purl'):
                    prompt += f"\n   PURL: {comp['purl']}"

            prompt += """

Provide a concise supply chain security analysis covering:
1. Notable dependencies and their potential risks
2. License compliance observations
3. Supply chain risk assessment
4. Recommendations for dependency management

Keep the response focused and actionable."""

            # Call LLM
            analysis = await self.generate_text(prompt, timeout=120)

            return {
                "success": True,
                "analysis": analysis,
                "summary": summary,
                "raw_data": raw_results
            }

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error processing Syft results with LLM: {str(e)}")
            # Return formatted fallback
            summary = self._extract_syft_summary(raw_results)
            return {
                "success": True,
                "analysis": self._format_syft_fallback(summary),
                "summary": summary,
                "raw_data": raw_results
            }

    def _extract_syft_summary(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from raw Syft CycloneDX JSON results."""
        try:
            summary = {
                "total_components": 0,
                "by_type": {},
                "licenses": set(),
                "components": []
            }

            components = raw_results.get("components", [])
            summary["total_components"] = len(components)

            for comp in components:
                comp_type = comp.get("type", "unknown")
                summary["by_type"][comp_type] = summary["by_type"].get(comp_type, 0) + 1

                # Extract licenses
                comp_licenses = []
                for license_entry in comp.get("licenses", []):
                    license_obj = license_entry.get("license", {})
                    license_id = license_obj.get("id", "")
                    license_name = license_obj.get("name", "")
                    license_str = license_id or license_name
                    if license_str:
                        comp_licenses.append(license_str)
                        summary["licenses"].add(license_str)

                summary["components"].append({
                    "name": comp.get("name", "unknown"),
                    "version": comp.get("version", "unknown"),
                    "type": comp_type,
                    "purl": comp.get("purl", ""),
                    "licenses": comp_licenses
                })

            # Convert set to list for JSON serialization
            summary["licenses"] = list(summary["licenses"])

            return summary

        except Exception as e:
            logger.error(f"Error extracting Syft summary: {str(e)}")
            return {"total_components": 0, "by_type": {}, "licenses": [], "components": []}

    def _format_syft_fallback(self, summary: Dict[str, Any]) -> str:
        """Format Syft summary as human-readable text when LLM fails."""
        text = f"SBOM Analysis Results:\n\n"
        text += f"Total Components: {summary['total_components']}\n"
        text += f"Component Types:\n"
        for comp_type, count in summary['by_type'].items():
            text += f"  - {comp_type}: {count}\n"
        text += f"\nUnique Licenses: {len(summary['licenses'])}\n"
        if summary['licenses']:
            text += f"Licenses: {', '.join(summary['licenses'][:20])}\n"
            if len(summary['licenses']) > 20:
                text += f"  ... and {len(summary['licenses']) - 20} more\n"
        text += "\n"

        if summary['components']:
            text += "Components (limited to 30):\n\n"
            for idx, comp in enumerate(summary['components'][:30], 1):
                text += f"{idx}. {comp['name']} v{comp['version']} ({comp['type']})\n"
                if comp.get('licenses'):
                    text += f"   License: {', '.join(comp['licenses'][:3])}\n"
                if comp.get('purl'):
                    text += f"   PURL: {comp['purl']}\n"
                text += "\n"

        return text

    # ===========================
    # QLON Ai Integration Methods
    # ===========================

    async def generate_text_with_qlon(
        self,
        prompt: str,
        qlon_url: str,
        qlon_api_key: str,
        use_tools: bool = True,
        stream: bool = False,
        timeout: int = 120,
        prompt_details: Optional[str] = None
    ) -> str:
        """
        Generate text using QLON Ai API.

        Args:
            prompt: The main content/data to send to QLON Ai (e.g., scan results)
            qlon_url: Base URL for QLON Ai API (e.g., https://your-qlon-instance.com)
            qlon_api_key: API key for authentication
            use_tools: Whether to enable integration tools
            stream: Whether to stream the response
            timeout: Request timeout in seconds
            prompt_details: Instructions for how to process the prompt (e.g., remediation instructions)

        Returns:
            Generated text response
        """
        # Build the full endpoint URL - ensure it's properly encoded
        endpoint = f"{qlon_url.rstrip('/')}{self.QLON_CHAT_ENDPOINT}"

        # Build payload according to QLON API spec
        # prompt = the data (scan results)
        # prompt_details = the instructions (what to do with the data)
        payload = {
            "prompt": prompt,
            "stream": stream,
            "is_saved": False,
            "is_temporary": True,
            "is_hidden": False
        }

        # Add prompt_details if provided (instructions for the AI)
        if prompt_details:
            payload["prompt_details"] = prompt_details

        # Add integration tools if enabled
        if use_tools:
            payload["enabled_tools"] = ["integration:*"]

        # Ensure API key is ASCII-safe (strip any non-ASCII characters or whitespace)
        clean_api_key = qlon_api_key.strip() if qlon_api_key else ""

        # Log info about the API key (without revealing it)
        logger.info(f"API Key length: {len(clean_api_key)}, first char ord: {ord(clean_api_key[0]) if clean_api_key else 'N/A'}")

        # Check for non-ASCII characters in API key
        try:
            clean_api_key.encode('ascii')
        except UnicodeEncodeError as e:
            logger.error(f"API key contains non-ASCII characters at position {e.start}-{e.end}")
            # Try to extract just ASCII characters
            clean_api_key = ''.join(c for c in clean_api_key if ord(c) < 128)
            logger.info(f"Cleaned API key to ASCII-only, new length: {len(clean_api_key)}")

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "API-Key": clean_api_key
        }

        try:
            logger.info(f"Sending request to QLON Ai at {endpoint}")

            # Serialize payload with ensure_ascii=False for proper Unicode handling
            payload_json = json.dumps(payload, ensure_ascii=False)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    content=payload_json.encode('utf-8'),
                    headers=headers,
                    timeout=timeout
                )
                response.raise_for_status()

                if stream:
                    # Handle streaming response
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    full_response += data["response"]
                                elif "content" in data:
                                    full_response += data["content"]
                                elif "choices" in data and data["choices"]:
                                    choice = data["choices"][0]
                                    if "message" in choice:
                                        full_response += choice["message"].get("content", "")
                                    elif "delta" in choice:
                                        full_response += choice["delta"].get("content", "")
                            except json.JSONDecodeError:
                                continue
                    return full_response
                else:
                    # Handle non-streaming response
                    result = response.json()

                    # Handle different response formats
                    if "response" in result:
                        return result["response"]
                    elif "content" in result:
                        return result["content"]
                    elif "choices" in result and result["choices"]:
                        choice = result["choices"][0]
                        if "message" in choice:
                            return choice["message"].get("content", "")
                        elif "text" in choice:
                            return choice["text"]
                    elif "output" in result:
                        return result["output"]

                    # If no recognized format, return the whole response as string
                    logger.warning(f"Unexpected QLON response format: {list(result.keys())}")
                    return str(result)

        except httpx.TimeoutException:
            logger.error("QLON Ai request timed out")
            raise Exception("QLON Ai request timed out. Please try again.")
        except httpx.ConnectError:
            logger.error(f"Could not connect to QLON Ai at {endpoint}")
            raise Exception("Could not connect to QLON Ai service. Please check the URL.")
        except httpx.HTTPStatusError as e:
            logger.error(f"QLON Ai HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                raise Exception("QLON Ai authentication failed. Please check your API key.")
            elif e.response.status_code == 403:
                raise Exception("QLON Ai access denied. Please check your API key permissions.")
            else:
                raise Exception(f"QLON Ai error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error calling QLON Ai: {str(e)}")
            raise Exception(f"Error calling QLON Ai: {str(e)}")

    async def process_semgrep_results_with_qlon(
        self,
        raw_results: Dict[str, Any],
        qlon_url: str,
        qlon_api_key: str,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process Semgrep scan results with QLON Ai analysis.

        Args:
            raw_results: Raw Semgrep scan output in JSON format
            qlon_url: QLON Ai API URL
            qlon_api_key: QLON Ai API key
            use_tools: Whether to enable QLON integration tools

        Returns:
            Human-readable analysis with security insights
        """
        try:
            logger.info("Processing Semgrep results with QLON Ai")

            # Extract key information from Semgrep results
            summary = self._extract_semgrep_summary(raw_results)

            if not summary.get("findings"):
                return {
                    "success": True,
                    "analysis": "No security issues were found in the code scan.",
                    "raw_data": raw_results,
                    "llm_provider": "qlon"
                }

            # Build prompt for QLON Ai
            prompt = f"""Analyze this code security scan and provide insights:

Scan Summary:
- Total Findings: {summary['total_findings']}
- By Severity: ERROR: {summary['by_severity']['ERROR']}, WARNING: {summary['by_severity']['WARNING']}, INFO: {summary['by_severity']['INFO']}

Top Findings (limited to 20):
"""

            for idx, finding in enumerate(summary['findings'][:20], 1):
                prompt += f"\n{idx}. [{finding['severity']}] {finding['check_id']}"
                prompt += f"\n   File: {finding['file']}:{finding['line']}"
                prompt += f"\n   Message: {finding['message'][:200]}"
                if len(finding['message']) > 200:
                    prompt += "..."
                prompt += "\n"

            prompt += """

Provide a concise security analysis covering:
1. Most critical vulnerabilities found
2. Common security patterns identified
3. Recommended remediation priorities

Keep the response focused and actionable."""

            # Call QLON Ai
            analysis = await self.generate_text_with_qlon(
                prompt=prompt,
                qlon_url=qlon_url,
                qlon_api_key=qlon_api_key,
                use_tools=use_tools,
                timeout=180
            )

            return {
                "success": True,
                "analysis": analysis,
                "summary": summary,
                "raw_data": raw_results,
                "llm_provider": "qlon"
            }

        except Exception as e:
            logger.error(f"Error processing Semgrep results with QLON Ai: {str(e)}")
            # Return formatted fallback
            summary = self._extract_semgrep_summary(raw_results)
            return {
                "success": True,
                "analysis": self._format_semgrep_fallback(summary),
                "summary": summary,
                "raw_data": raw_results,
                "llm_provider": "qlon",
                "llm_error": str(e)
            }

    async def process_nmap_results_with_qlon(
        self,
        raw_results: Dict[str, Any],
        qlon_url: str,
        qlon_api_key: str,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process Nmap scan results with QLON Ai analysis.

        Args:
            raw_results: Raw Nmap scan output in JSON format
            qlon_url: QLON Ai API URL
            qlon_api_key: QLON Ai API key
            use_tools: Whether to enable QLON integration tools

        Returns:
            Human-readable analysis with security insights
        """
        try:
            logger.info("Processing Nmap results with QLON Ai")

            # Extract key information from Nmap results
            summary = self._extract_nmap_summary(raw_results)

            if not summary.get("hosts"):
                return {
                    "success": True,
                    "analysis": "No hosts were detected in the scan results.",
                    "raw_data": raw_results,
                    "llm_provider": "qlon"
                }

            # Build prompt for QLON Ai
            prompt = f"""Analyze this network scan and provide security insights:

Scan Summary:
- Total Hosts: {summary['total_hosts']}
- Hosts Up: {summary['hosts_up']}
- Total Open Ports: {summary['total_ports']}

Host Details:
"""

            for host in summary['hosts'][:5]:  # Limit to first 5 hosts
                prompt += f"\nHost: {host['address']}"
                if host.get('hostname'):
                    prompt += f" ({host['hostname']})"
                prompt += f"\n  Status: {host['status']}"

                if host['ports']:
                    prompt += f"\n  Open Ports ({len(host['ports'])}):"
                    for port in host['ports'][:10]:  # Limit to first 10 ports
                        prompt += f"\n    - {port['port']}/{port['protocol']}: {port['service']}"
                        if port.get('version'):
                            prompt += f" ({port['version']})"
                        if port.get('banner'):
                            prompt += f"\n      Banner: {port['banner']}"
                        if port.get('cpe'):
                            prompt += f"\n      CPE: {', '.join(port['cpe'][:3])}"
                        if port.get('scripts'):
                            for script in port['scripts'][:2]:
                                prompt += f"\n      Script [{script['id']}]: {script['output'][:150]}"

            prompt += """

Provide a concise security analysis covering:
1. Critical security findings (open ports, vulnerable services)
2. Potential security risks
3. Recommended actions

Keep the response focused and actionable."""

            # Call QLON Ai
            analysis = await self.generate_text_with_qlon(
                prompt=prompt,
                qlon_url=qlon_url,
                qlon_api_key=qlon_api_key,
                use_tools=use_tools,
                timeout=180
            )

            return {
                "success": True,
                "analysis": analysis,
                "summary": summary,
                "raw_data": raw_results,
                "llm_provider": "qlon"
            }

        except Exception as e:
            logger.error(f"Error processing Nmap results with QLON Ai: {str(e)}")
            # Return formatted fallback
            summary = self._extract_nmap_summary(raw_results)
            return {
                "success": True,
                "analysis": self._format_nmap_fallback(summary),
                "summary": summary,
                "raw_data": raw_results,
                "llm_provider": "qlon",
                "llm_error": str(e)
            }

    async def process_osv_results_with_qlon(
        self,
        raw_results: Dict[str, Any],
        qlon_url: str,
        qlon_api_key: str,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process OSV vulnerability scan results with QLON Ai analysis.

        Args:
            raw_results: Raw OSV scan output in JSON format
            qlon_url: QLON Ai API URL
            qlon_api_key: QLON Ai API key
            use_tools: Whether to enable QLON integration tools

        Returns:
            Human-readable analysis with security insights
        """
        try:
            logger.info("Processing OSV results with QLON Ai")

            # Extract key information from OSV results
            summary = self._extract_osv_summary(raw_results)

            if not summary.get("vulnerabilities"):
                return {
                    "success": True,
                    "analysis": "No vulnerabilities were found in the scanned dependencies.",
                    "raw_data": raw_results,
                    "llm_provider": "qlon"
                }

            # Build prompt for QLON Ai
            prompt = f"""Analyze this dependency vulnerability scan and provide insights:

Scan Summary:
- Total Packages Scanned: {summary['total_packages']}
- Vulnerable Packages: {summary['vulnerable_packages']}
- Total Vulnerabilities: {summary['total_vulnerabilities']}

Vulnerable Packages (limited to 15):
"""

            for pkg in summary['vulnerabilities'][:15]:
                prompt += f"\nPackage: {pkg['package']} (Ecosystem: {pkg['ecosystem']})"
                prompt += f"\n  Vulnerabilities: {len(pkg['vulns'])}"
                for vuln in pkg['vulns'][:5]:  # Limit to first 5 vulnerabilities per package
                    prompt += f"\n    - {vuln['id']}: {vuln['summary'][:150]}"
                    if len(vuln['summary']) > 150:
                        prompt += "..."
                prompt += "\n"

            prompt += """

Provide a concise security analysis covering:
1. Most critical vulnerabilities that should be addressed immediately
2. Patterns in vulnerable dependencies
3. Recommended remediation actions

Keep the response focused and actionable."""

            # Call QLON Ai
            analysis = await self.generate_text_with_qlon(
                prompt=prompt,
                qlon_url=qlon_url,
                qlon_api_key=qlon_api_key,
                use_tools=use_tools,
                timeout=180
            )

            return {
                "success": True,
                "analysis": analysis,
                "summary": summary,
                "raw_data": raw_results,
                "llm_provider": "qlon"
            }

        except Exception as e:
            logger.error(f"Error processing OSV results with QLON Ai: {str(e)}")
            # Return formatted fallback
            summary = self._extract_osv_summary(raw_results)
            return {
                "success": True,
                "analysis": self._format_osv_fallback(summary),
                "summary": summary,
                "raw_data": raw_results,
                "llm_provider": "qlon",
                "llm_error": str(e)
            }

    # ===========================
    # AI Remediation Methods
    # ===========================

    # Default prompts for AI Remediator
    DEFAULT_ZAP_PROMPT = """You are a cybersecurity expert specializing in web application security.

Analyze the following OWASP ZAP scan results and provide detailed remediation guidance.

For each vulnerability, provide:
1. **Vulnerability Explanation**: Brief description of the security issue
2. **Risk Assessment**: Why this is a security concern
3. **Remediation Steps**: Specific, actionable steps to fix the vulnerability
4. **Code Examples**: Where applicable, provide secure code patterns
5. **Prevention**: How to prevent this in the future

ZAP Scan Results:
{scan_results}

Provide clear, structured guidance that developers can follow."""

    DEFAULT_NMAP_PROMPT = """You are a network security expert specializing in infrastructure hardening.

Analyze the following Nmap scan results and provide detailed remediation guidance.

For each finding, provide:
1. **Service Analysis**: Explanation of the detected service
2. **Security Concerns**: Potential risks with open ports/services
3. **Remediation Steps**: Actions to secure or close unnecessary services
4. **Configuration Examples**: Firewall rules, service hardening
5. **Best Practices**: Industry-standard recommendations

Nmap Scan Results:
{scan_results}

Prioritize findings by risk level. Focus on practical improvements."""

    async def generate_remediation(
        self,
        scanner_type: str,
        scan_results: str,
        custom_prompt: Optional[str] = None,
        llm_provider: str = "llamacpp",
        qlon_url: Optional[str] = None,
        qlon_api_key: Optional[str] = None,
        qlon_use_tools: bool = True
    ) -> str:
        """
        Generate AI remediation guidance for scan results.

        Args:
            scanner_type: Type of scanner ('zap' or 'nmap')
            scan_results: The scan results as JSON string
            custom_prompt: Optional custom prompt template (must contain {scan_results} placeholder)
            llm_provider: LLM provider to use ('llamacpp' or 'qlon')
            qlon_url: QLON Ai API URL (required if llm_provider is 'qlon')
            qlon_api_key: QLON Ai API key (required if llm_provider is 'qlon')
            qlon_use_tools: Whether to enable QLON integration tools

        Returns:
            AI-generated remediation guidance
        """
        try:
            # Parse scan results if it's a string
            if isinstance(scan_results, str):
                try:
                    results_data = json.loads(scan_results)
                except json.JSONDecodeError:
                    results_data = scan_results
            else:
                results_data = scan_results

            # Format the scan results for the prompt
            formatted_results = self._format_scan_results_for_remediation(scanner_type, results_data)

            # Get the appropriate instructions (prompt_details for QLON)
            if custom_prompt and custom_prompt.strip():
                # For custom prompts, remove the {scan_results} placeholder for instructions
                instructions = custom_prompt.replace("{scan_results}", "").strip()
                combined_prompt = custom_prompt.replace("{scan_results}", formatted_results)
            elif scanner_type == "zap":
                instructions = self.DEFAULT_ZAP_PROMPT.replace("{scan_results}", "").replace("ZAP Scan Results:", "").strip()
                combined_prompt = self.DEFAULT_ZAP_PROMPT.replace("{scan_results}", formatted_results)
            elif scanner_type == "nmap":
                instructions = self.DEFAULT_NMAP_PROMPT.replace("{scan_results}", "").replace("Nmap Scan Results:", "").strip()
                combined_prompt = self.DEFAULT_NMAP_PROMPT.replace("{scan_results}", formatted_results)
            else:
                raise ValueError(f"Unsupported scanner type: {scanner_type}")

            logger.info(f"Generating {scanner_type} remediation using {llm_provider}")
            logger.info(f"Scan results length: {len(formatted_results)} chars, Instructions length: {len(instructions)} chars")

            # Call the appropriate LLM provider
            if llm_provider == "qlon" and qlon_url and qlon_api_key:
                logger.info(f"Using QLON Ai at {qlon_url}")
                # For QLON: prompt = scan results, prompt_details = instructions
                remediation = await self.generate_text_with_qlon(
                    prompt=formatted_results,
                    qlon_url=qlon_url,
                    qlon_api_key=qlon_api_key,
                    use_tools=qlon_use_tools,
                    timeout=300,
                    prompt_details=instructions
                )
            else:
                # Use llama.cpp
                self.llm_backend = "llamacpp"
                logger.info(f"Using llama.cpp at {self.llamacpp_url}")
                remediation = await self.generate_text(combined_prompt, timeout=300)

            logger.info(f"Remediation generated, response length: {len(remediation)} chars")
            return remediation

        except Exception as e:
            logger.error(f"Error generating remediation: {str(e)}")
            raise Exception(f"Failed to generate remediation guidance: {str(e)}")

    def _format_scan_results_for_remediation(self, scanner_type: str, results_data: Any) -> str:
        """Format scan results for inclusion in remediation prompt."""
        try:
            if scanner_type == "zap":
                return self._format_zap_results_for_remediation(results_data)
            elif scanner_type == "nmap":
                return self._format_nmap_results_for_remediation(results_data)
            else:
                # Fallback: just return JSON string
                return json.dumps(results_data, indent=2)[:8000]  # Limit to 8000 chars
        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            return str(results_data)[:8000]

    def _format_zap_results_for_remediation(self, results_data: Any) -> str:
        """Format ZAP scan results for remediation prompt."""
        try:
            formatted = []

            # Handle different result formats
            alerts = []
            if isinstance(results_data, list):
                alerts = results_data
            elif isinstance(results_data, dict):
                alerts = results_data.get("alerts", [])
                if not alerts and "raw_data" in results_data:
                    alerts = results_data.get("raw_data", [])
                    if isinstance(alerts, dict):
                        alerts = alerts.get("alerts", [])

            if not alerts:
                return "No alerts found in the scan results."

            # Sort by risk level
            risk_order = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3, "Info": 3}
            alerts_sorted = sorted(alerts, key=lambda x: risk_order.get(x.get("risk", ""), 4))

            formatted.append(f"Total Alerts: {len(alerts_sorted)}")
            formatted.append("")

            for idx, alert in enumerate(alerts_sorted[:20], 1):  # Limit to 20 alerts
                risk = alert.get("risk", "Unknown")
                name = alert.get("name", alert.get("alert", "Unknown"))
                desc = alert.get("description", alert.get("desc", "No description"))
                solution = alert.get("solution", "No solution provided")
                url = alert.get("url", "N/A")
                instances = alert.get("instances", [])

                formatted.append(f"--- Alert {idx} ---")
                formatted.append(f"Risk Level: {risk}")
                formatted.append(f"Name: {name}")
                formatted.append(f"URL: {url}")
                formatted.append(f"Description: {desc[:500]}")
                if solution:
                    formatted.append(f"Suggested Solution: {solution[:300]}")
                if instances:
                    formatted.append(f"Instance Count: {len(instances)}")
                formatted.append("")

            return "\n".join(formatted)

        except Exception as e:
            logger.error(f"Error formatting ZAP results: {str(e)}")
            return json.dumps(results_data, indent=2)[:8000]

    def _format_nmap_results_for_remediation(self, results_data: Any) -> str:
        """Format Nmap scan results for remediation prompt."""
        try:
            formatted = []

            if isinstance(results_data, dict):
                # NEW FORMAT: Check for vulnerabilities array (from NmapVulnerabilityService)
                vulnerabilities = results_data.get("vulnerabilities", [])
                summary = results_data.get("summary", {})

                if vulnerabilities and isinstance(vulnerabilities, list):
                    # Format vulnerability-based results
                    formatted.append("=== NETWORK VULNERABILITY SCAN RESULTS ===")
                    formatted.append("")

                    # Summary counts by severity
                    if summary:
                        high_count = summary.get("high", 0)
                        medium_count = summary.get("medium", 0)
                        low_count = summary.get("low", 0)
                        info_count = summary.get("info", 0)
                        total_count = summary.get("total", len(vulnerabilities))

                        formatted.append("SEVERITY SUMMARY:")
                        formatted.append(f"  - High: {high_count}")
                        formatted.append(f"  - Medium: {medium_count}")
                        formatted.append(f"  - Low: {low_count}")
                        formatted.append(f"  - Informational: {info_count}")
                        formatted.append(f"  - Total Findings: {total_count}")
                        formatted.append("")

                    # Group vulnerabilities by severity for better organization
                    severity_order = ["High", "Medium", "Low", "Info"]
                    vulns_by_severity = {s: [] for s in severity_order}

                    for vuln in vulnerabilities:
                        sev = vuln.get("severity", "Info")
                        if sev in vulns_by_severity:
                            vulns_by_severity[sev].append(vuln)

                    # Format High severity vulnerabilities (CVEs) - most important for remediation
                    for severity in ["High", "Medium", "Low"]:
                        vulns = vulns_by_severity.get(severity, [])
                        if vulns:
                            formatted.append(f"=== {severity.upper()} SEVERITY VULNERABILITIES ({len(vulns)}) ===")
                            formatted.append("")

                            for vuln in vulns[:20]:  # Limit to 20 per severity
                                title = vuln.get("title", "Unknown Vulnerability")
                                host = vuln.get("host", "Unknown")
                                port = vuln.get("port", "")
                                protocol = vuln.get("protocol", "tcp")
                                cve_id = vuln.get("cve_id", "")
                                cvss_score = vuln.get("cvss_score")
                                description = vuln.get("description", "")
                                service_name = vuln.get("service_name", "")
                                service_version = vuln.get("service_version", "")
                                cpe = vuln.get("cpe", "")

                                formatted.append(f"[{severity}] {title}")
                                formatted.append(f"  Host: {host}:{port}/{protocol}" if port else f"  Host: {host}")

                                if service_name:
                                    service_info = f"{service_name} {service_version}".strip()
                                    formatted.append(f"  Service: {service_info}")

                                if cve_id:
                                    formatted.append(f"  CVE: {cve_id}")
                                if cvss_score:
                                    formatted.append(f"  CVSS Score: {cvss_score}")
                                if cpe:
                                    formatted.append(f"  CPE: {cpe}")
                                if description:
                                    # Truncate long descriptions
                                    desc = description[:300] + "..." if len(description) > 300 else description
                                    formatted.append(f"  Description: {desc}")

                                formatted.append("")

                    # Format Info level findings (open ports) - summarize briefly
                    info_vulns = vulns_by_severity.get("Info", [])
                    if info_vulns:
                        # Separate scan summary from port discoveries
                        port_vulns = [v for v in info_vulns if v.get("port")]
                        summary_vulns = [v for v in info_vulns if not v.get("port")]

                        if summary_vulns:
                            formatted.append("=== SCAN SUMMARY ===")
                            for vuln in summary_vulns[:3]:
                                formatted.append(f"  {vuln.get('title', '')}")
                                if vuln.get('description'):
                                    formatted.append(f"  {vuln.get('description', '')}")
                            formatted.append("")

                        if port_vulns:
                            formatted.append(f"=== DISCOVERED OPEN PORTS ({len(port_vulns)}) ===")
                            formatted.append("")

                            # Group by host
                            ports_by_host = {}
                            for vuln in port_vulns:
                                host = vuln.get("host", "Unknown")
                                if host not in ports_by_host:
                                    ports_by_host[host] = []
                                ports_by_host[host].append(vuln)

                            for host, host_vulns in list(ports_by_host.items())[:10]:  # Limit to 10 hosts
                                formatted.append(f"Host: {host}")
                                for vuln in host_vulns[:20]:  # Limit to 20 ports per host
                                    port = vuln.get("port", "")
                                    protocol = vuln.get("protocol", "tcp")
                                    service_name = vuln.get("service_name", "")
                                    service_version = vuln.get("service_version", "")
                                    service_info = f"{service_name} {service_version}".strip() if service_name else "unknown"
                                    formatted.append(f"  - {port}/{protocol}: {service_info}")
                                formatted.append("")

                    return "\n".join(formatted)

                # OLD FORMAT: Handle legacy format with summary.hosts structure
                raw_data = results_data.get("raw_data", results_data)

                if summary and summary.get("hosts"):
                    formatted.append(f"Total Hosts: {summary.get('total_hosts', 0)}")
                    formatted.append(f"Hosts Up: {summary.get('hosts_up', 0)}")
                    formatted.append(f"Total Open Ports: {summary.get('total_ports', 0)}")
                    formatted.append("")

                    hosts = summary.get("hosts", [])
                    for host in hosts[:5]:  # Limit to 5 hosts
                        addr = host.get("address", "Unknown")
                        hostname = host.get("hostname", "")
                        status = host.get("status", "unknown")
                        ports = host.get("ports", [])

                        formatted.append(f"--- Host: {addr} ---")
                        if hostname:
                            formatted.append(f"Hostname: {hostname}")
                        formatted.append(f"Status: {status}")

                        if ports:
                            formatted.append(f"Open Ports ({len(ports)}):")
                            for port in ports[:15]:  # Limit to 15 ports per host
                                port_num = port.get("port", "?")
                                protocol = port.get("protocol", "tcp")
                                service = port.get("service", "unknown")
                                version = port.get("version", "").strip()
                                formatted.append(f"  - {port_num}/{protocol}: {service} {version}")
                        formatted.append("")

                # If no summary, try to extract from raw_data
                elif "output" in raw_data:
                    output = raw_data.get("output", {})
                    nmaprun = output.get("nmaprun", {})
                    host_data = nmaprun.get("host", [])

                    if host_data:
                        hosts = host_data if isinstance(host_data, list) else [host_data]
                        formatted.append(f"Hosts Found: {len(hosts)}")
                        formatted.append("")

                        for host in hosts[:5]:
                            address = host.get("address", {})
                            addr = address.get("@addr", "Unknown") if isinstance(address, dict) else "Unknown"
                            status = host.get("status", {}).get("@state", "unknown")

                            formatted.append(f"--- Host: {addr} ---")
                            formatted.append(f"Status: {status}")

                            ports_data = host.get("ports", {})
                            if ports_data:
                                port_list = ports_data.get("port", [])
                                ports = port_list if isinstance(port_list, list) else [port_list] if port_list else []
                                open_ports = [p for p in ports if p.get("state", {}).get("@state") == "open"]

                                if open_ports:
                                    formatted.append(f"Open Ports ({len(open_ports)}):")
                                    for port in open_ports[:15]:
                                        port_id = port.get("@portid", "?")
                                        protocol = port.get("@protocol", "tcp")
                                        service = port.get("service", {})
                                        svc_name = service.get("@name", "unknown")
                                        svc_product = service.get("@product", "")
                                        svc_version = service.get("@version", "")
                                        formatted.append(f"  - {port_id}/{protocol}: {svc_name} {svc_product} {svc_version}")
                            formatted.append("")

            if not formatted:
                return json.dumps(results_data, indent=2)[:8000]

            return "\n".join(formatted)

        except Exception as e:
            logger.error(f"Error formatting Nmap results: {str(e)}")
            return json.dumps(results_data, indent=2)[:8000]

    # ===========================
    # AI Incident Analysis Methods
    # ===========================

    async def analyze_incident(self, incident_data: dict) -> str:
        """
        Analyze a security incident and provide containment/remediation guidance.

        Args:
            incident_data: Dict with incident details (title, description, severity, etc.)

        Returns:
            JSON string with analysis results
        """
        try:
            prompt = f"""You are a cybersecurity incident response expert. Analyze the following security incident and provide actionable guidance.

Incident Details:
- Title: {incident_data.get('title', 'N/A')}
- Description: {incident_data.get('description', 'N/A')}
- Severity: {incident_data.get('severity', 'N/A')}
- Status: {incident_data.get('status', 'N/A')}
- Reported By: {incident_data.get('reported_by', 'N/A')}
- Discovered At: {incident_data.get('discovered_at', 'N/A')}
- Containment Actions Taken: {incident_data.get('containment_actions', 'None yet')}
- Root Cause (if known): {incident_data.get('root_cause', 'Not yet determined')}
- Remediation Steps Taken: {incident_data.get('remediation_steps', 'None yet')}

IMPORTANT: Output ONLY valid JSON with no additional text before or after. Use this exact format:

```json
{{
  "summary": "Brief incident summary and classification",
  "containment_steps": ["Step 1", "Step 2", "Step 3"],
  "root_cause_analysis": "Likely root cause based on available information",
  "remediation_recommendations": ["Recommendation 1", "Recommendation 2"],
  "severity_assessment": "Assessment of the current severity rating and whether it should be adjusted",
  "lessons_learned": ["Lesson 1", "Lesson 2"]
}}
```

Guidelines:
- Be specific and actionable in your recommendations
- Consider the current status and any actions already taken
- Prioritize containment if the incident is still active
- Include both immediate and long-term remediation steps
- Assess whether the severity rating is appropriate
"""

            response_text = await self.generate_text(prompt, timeout=600)

            # Validate the response is parseable JSON
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > 0:
                    json_str = response_text[json_start:json_end]
                    json.loads(json_str)  # Validate it's valid JSON
                    return json_str
            except json.JSONDecodeError:
                pass

            # If not valid JSON, return the raw text
            return response_text

        except Exception as e:
            logger.error(f"Error analyzing incident: {str(e)}")
            raise

    # ===========================
    # AI Policy Aligner Methods
    # ===========================

    DEFAULT_POLICY_ALIGNER_PROMPT = """You are an expert in cybersecurity compliance and policy management. Your task is to analyze policies and framework questions to identify which policy best addresses each question.

For each question, identify the most relevant policy based on:
1. Direct coverage of the question's requirements
2. Alignment with the question's security domain (access control, data protection, etc.)
3. Completeness of the policy in addressing the question

Return a JSON array with your alignments:
[
  {
    "question_id": "uuid",
    "policy_id": "uuid",
    "confidence_score": 85,
    "reasoning": "Brief explanation of why this policy addresses this question"
  }
]

Only include alignments with confidence >= 80. If no policy adequately addresses a question, omit it from the results."""

    async def generate_policy_alignments(
        self,
        policies: List[Dict[str, Any]],
        questions: List[Dict[str, Any]],
        custom_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered alignments between policies and framework questions.

        Args:
            policies: List of dicts with keys: id, title, body
            questions: List of dicts with keys: id, text
            custom_prompt: Optional custom prompt to override the default

        Returns:
            List of alignment dicts: [{question_id, policy_id, confidence_score, reasoning}]
        """
        logger.info(f"Generating policy alignments for {len(policies)} policies and {len(questions)} questions")

        # Build the prompt
        prompt = self._build_policy_alignment_prompt(policies, questions, custom_prompt)

        try:
            # Call the LLM
            response_text = await self.generate_text(prompt, timeout=300)

            # Parse the response
            alignments = self._parse_policy_alignment_response(response_text, policies, questions)

            logger.info(f"LLM generated {len(alignments)} policy alignments")
            return alignments

        except Exception as e:
            logger.error(f"Error generating policy alignments with LLM: {str(e)}")
            raise

    def _build_policy_alignment_prompt(
        self,
        policies: List[Dict[str, Any]],
        questions: List[Dict[str, Any]],
        custom_prompt: Optional[str] = None
    ) -> str:
        """Build the prompt for policy alignment analysis."""

        # Use custom prompt if provided, otherwise use default
        base_prompt = custom_prompt if custom_prompt and custom_prompt.strip() else self.DEFAULT_POLICY_ALIGNER_PROMPT

        # Format policies
        policies_text = "POLICIES:\n"
        for i, policy in enumerate(policies[:50], 1):  # Limit to 50 policies
            title = policy.get('title', 'Untitled')
            body = policy.get('body', '')
            # Truncate long policy bodies to save tokens
            if len(body) > 500:
                body = body[:500] + "..."
            policies_text += f"\n{i}. [ID: {policy['id']}] {title}\n   {body}\n"

        # Format questions
        questions_text = "\nFRAMEWORK QUESTIONS:\n"
        for i, question in enumerate(questions[:100], 1):  # Limit to 100 questions
            text = question.get('text', '')
            # Truncate long questions
            if len(text) > 300:
                text = text[:300] + "..."
            questions_text += f"\n{i}. [ID: {question['id']}] {text}\n"

        # Combine everything
        full_prompt = f"""{base_prompt}

{policies_text}

{questions_text}

IMPORTANT: Output ONLY valid JSON with no additional text before or after. Use this exact format:

```json
[
  {{
    "question_id": "actual-uuid-from-questions",
    "policy_id": "actual-uuid-from-policies",
    "confidence_score": 85,
    "reasoning": "Brief explanation"
  }}
]
```

Guidelines:
- Only include alignments with confidence >= 80
- Each question should map to at most ONE policy (the best match)
- If no policy adequately addresses a question, omit that question
- Focus on the primary intent and requirements of each question
- Include only the JSON array output, no explanations before or after
"""

        return full_prompt

    def _parse_policy_alignment_response(
        self,
        response_text: str,
        policies: List[Dict[str, Any]],
        questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse the LLM response and extract policy alignments."""

        try:
            # Try to extract JSON array from the response
            # First try to find array directly
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                logger.warning("No JSON array found in LLM response")
                return []

            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            if not isinstance(data, list):
                logger.warning("Response is not a JSON array")
                return []

            # Build lookup dictionaries for validation
            valid_policy_ids = {p['id'] for p in policies}
            valid_question_ids = {q['id'] for q in questions}

            alignments = []
            for item in data:
                question_id = item.get("question_id")
                policy_id = item.get("policy_id")
                confidence_score = item.get("confidence_score", 0)

                # Validate IDs exist
                if question_id not in valid_question_ids:
                    logger.warning(f"Invalid question_id in alignment: {question_id}")
                    continue

                if policy_id not in valid_policy_ids:
                    logger.warning(f"Invalid policy_id in alignment: {policy_id}")
                    continue

                # Only include high-confidence alignments
                if confidence_score < 80:
                    continue

                alignments.append({
                    "question_id": question_id,
                    "policy_id": policy_id,
                    "confidence_score": confidence_score,
                    "reasoning": item.get("reasoning", "")
                })

            # Sort by confidence descending
            alignments.sort(key=lambda x: x['confidence_score'], reverse=True)

            return alignments

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error parsing policy alignment response: {str(e)}")
            return []

    # ===========================
    # Streaming Chat Methods (Chatbot)
    # ===========================

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        provider: str,
        settings: dict
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat response as SSE events. Dispatches to the appropriate provider.
        Yields strings in SSE format: 'data: {"token": "..."}\n\n'

        Args:
            messages: List of {role, content} dicts (system + user/assistant turns)
            provider: LLM provider name (llamacpp, openai, anthropic, xai, google, qlon)
            settings: Effective LLM settings dict from get_effective_llm_settings_for_user
        """
        if provider == "llamacpp":
            async for chunk in self._stream_chat_llamacpp(messages):
                yield chunk
        elif provider in ("openai", "xai", "google"):
            async for chunk in self._stream_chat_openai_compatible(messages, provider, settings):
                yield chunk
        elif provider == "anthropic":
            async for chunk in self._stream_chat_anthropic(messages, settings):
                yield chunk
        elif provider == "qlon":
            async for chunk in self._stream_chat_qlon(messages, settings):
                yield chunk
        else:
            # Default to llamacpp
            async for chunk in self._stream_chat_llamacpp(messages):
                yield chunk

    async def _stream_chat_llamacpp(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream chat via llama.cpp OpenAI-compatible endpoint."""
        payload = {
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.5,
            "top_p": 0.9,
            "stream": True
        }

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    self.llamacpp_url,
                    json=payload,
                    timeout=120
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    yield f'data: {json.dumps({"token": delta["content"]})}\n\n'
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError:
            yield f'data: {json.dumps({"error": "Could not connect to llama.cpp. Please ensure the server is running."})}\n\n'
        except Exception as e:
            logger.error(f"Error in _stream_chat_llamacpp: {str(e)}")
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    async def _stream_chat_openai_compatible(
        self,
        messages: List[Dict[str, str]],
        provider: str,
        settings: dict
    ) -> AsyncGenerator[str, None]:
        """Stream chat via OpenAI-compatible APIs (OpenAI, xAI/Grok, Google/Gemini)."""
        if provider == "openai":
            api_key = settings.get("openai_api_key")
            model = settings.get("openai_model") or "gpt-4o"
            base_url = (settings.get("openai_base_url") or "https://api.openai.com/v1").rstrip("/")
        elif provider == "xai":
            api_key = settings.get("xai_api_key")
            model = settings.get("xai_model") or "grok-3"
            base_url = (settings.get("xai_base_url") or "https://api.x.ai/v1").rstrip("/")
        elif provider == "google":
            api_key = settings.get("google_api_key")
            model = settings.get("google_model") or "gemini-2.0-flash"
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        else:
            yield f'data: {json.dumps({"error": f"Unknown provider: {provider}"})}\n\n'
            return

        if not api_key:
            yield f'data: {json.dumps({"error": f"No API key configured for {provider}. Please configure it in Settings."})}\n\n'
            return

        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.5,
            "stream": True
        }

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    url,
                    json=payload,
                    headers=headers,
                    timeout=120
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    yield f'data: {json.dumps({"token": delta["content"]})}\n\n'
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPStatusError as e:
            error_msg = f"{provider} API error: {e.response.status_code}"
            try:
                body = e.response.json()
                error_msg = body.get("error", {}).get("message", error_msg)
            except Exception:
                pass
            yield f'data: {json.dumps({"error": error_msg})}\n\n'
        except Exception as e:
            logger.error(f"Error in _stream_chat_openai_compatible ({provider}): {str(e)}")
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    async def _stream_chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        settings: dict
    ) -> AsyncGenerator[str, None]:
        """Stream chat via the Anthropic Messages API with streaming."""
        api_key = settings.get("anthropic_api_key")
        model = settings.get("anthropic_model") or "claude-sonnet-4-20250514"

        if not api_key:
            yield f'data: {json.dumps({"error": "No API key configured for Anthropic. Please configure it in Settings."})}\n\n'
            return

        # Separate system message from conversation messages
        system_text = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": 2048,
            "stream": True,
            "messages": chat_messages
        }
        if system_text:
            payload["system"] = system_text

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    url,
                    json=payload,
                    headers=headers,
                    timeout=120
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                event_type = data.get("type", "")
                                if event_type == "content_block_delta":
                                    delta = data.get("delta", {})
                                    if delta.get("type") == "text_delta" and delta.get("text"):
                                        yield f'data: {json.dumps({"token": delta["text"]})}\n\n'
                                elif event_type == "message_stop":
                                    break
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPStatusError as e:
            error_msg = f"Anthropic API error: {e.response.status_code}"
            try:
                body = e.response.json()
                error_msg = body.get("error", {}).get("message", error_msg)
            except Exception:
                pass
            yield f'data: {json.dumps({"error": error_msg})}\n\n'
        except Exception as e:
            logger.error(f"Error in _stream_chat_anthropic: {str(e)}")
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    async def _stream_chat_qlon(
        self,
        messages: List[Dict[str, str]],
        settings: dict
    ) -> AsyncGenerator[str, None]:
        """Non-streaming fallback for QLON Ai - yields the entire response as one chunk."""
        qlon_url = settings.get("qlon_url")
        qlon_api_key = settings.get("qlon_api_key")

        if not qlon_url or not qlon_api_key:
            yield f'data: {json.dumps({"error": "QLON Ai is not configured. Please configure URL and API key in Settings."})}\n\n'
            return

        url = f"{qlon_url.rstrip('/')}{self.QLON_CHAT_ENDPOINT}"
        headers = {
            "Authorization": f"Bearer {qlon_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.5,
            "stream": False
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=120)
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    # Yield in small chunks for a streaming-like effect
                    chunk_size = 10
                    for i in range(0, len(content), chunk_size):
                        yield f'data: {json.dumps({"token": content[i:i+chunk_size]})}\n\n'
        except Exception as e:
            logger.error(f"Error in _stream_chat_qlon: {str(e)}")
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

AVAILABLE_FRAMEWORKS = [
    {"template_id": "CRA", "name": "Cyber Resilience Act (CRA)", "description": "EU regulation for products with digital elements"},
    {"template_id": "ISO_27001_2022", "name": "ISO 27001:2022", "description": "Information security management systems"},
    {"template_id": "NIS2_DIRECTIVE", "name": "NIS2 Directive", "description": "EU directive on network and information security"},
    {"template_id": "GDPR", "name": "GDPR", "description": "EU General Data Protection Regulation"},
    {"template_id": "SOC_2", "name": "SOC 2", "description": "Service Organization Control 2 trust criteria"},
    {"template_id": "PCI_DSS_V4_0", "name": "PCI DSS v4.0", "description": "Payment Card Industry Data Security Standard"},
    {"template_id": "NIST_CSF_2_0", "name": "NIST CSF 2.0", "description": "NIST Cybersecurity Framework"},
    {"template_id": "HIPAA_PRIVACY_RULE", "name": "HIPAA Privacy Rule", "description": "US health information privacy regulation"},
    {"template_id": "CMMC_2_0", "name": "CMMC 2.0", "description": "Cybersecurity Maturity Model Certification for US defense"},
    {"template_id": "CCPA_CALIFORNIA_CONSUMER_PRIVACY_ACT", "name": "CCPA", "description": "California Consumer Privacy Act"},
    {"template_id": "DORA_2022", "name": "DORA", "description": "EU Digital Operational Resilience Act for financial entities"},
    {"template_id": "AUSTRALIA_ENERGY_AESCSF", "name": "AESCSF", "description": "Australian Energy Sector Cyber Security Framework"},
    {"template_id": "COBIT_2019", "name": "COBIT 2019", "description": "IT governance and management framework"},
    {"template_id": "FTC_SAFEGUARDS", "name": "FTC Safeguards Rule", "description": "US Federal Trade Commission data security requirements"},
]

# Patterns for finding relevant internal pages
RELEVANT_PAGE_PATTERNS = re.compile(
    r'/(about|products|services|privacy|security|compliance|solutions|platform|company|industries|customers)',
    re.IGNORECASE
)

USER_AGENT = "Mozilla/5.0 (compatible; CyberBridge Compliance Advisor)"


def _extract_text(soup: BeautifulSoup) -> str:
    """Extract clean text from a BeautifulSoup parsed page."""
    # Remove non-content tags
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'iframe']):
        tag.decompose()

    text = soup.get_text(separator=' ', strip=True)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    # Truncate to 3000 chars per page to keep LLM prompt manageable
    return text[:3000]


def _find_relevant_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Find internal links to relevant pages (about, products, services, etc.)."""
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc
    links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Only follow internal links
        if parsed.netloc != base_domain:
            continue

        # Check if the path matches relevant patterns
        if RELEVANT_PAGE_PATTERNS.search(parsed.path):
            # Normalize URL (remove fragment, strip trailing slash)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
            if clean_url != base_url.rstrip('/'):
                links.add(clean_url)

    return list(links)[:4]  # Max 4 additional pages


async def scrape_website(url: str) -> dict:
    """Scrape a website's homepage and key internal pages."""
    pages = []
    error = None

    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT}
        ) as client:
            # Fetch homepage
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            text = _extract_text(soup)

            pages.append({
                "url": str(response.url),
                "title": title,
                "text": text
            })

            # Find and fetch relevant internal pages
            internal_links = _find_relevant_links(soup, str(response.url))

            for link_url in internal_links:
                try:
                    resp = await client.get(link_url)
                    resp.raise_for_status()
                    page_soup = BeautifulSoup(resp.text, 'html.parser')
                    page_title = page_soup.title.string.strip() if page_soup.title and page_soup.title.string else link_url
                    page_text = _extract_text(page_soup)

                    pages.append({
                        "url": link_url,
                        "title": page_title,
                        "text": page_text
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch internal page {link_url}: {str(e)}")
                    continue

    except Exception as e:
        error = f"Failed to scrape website: {str(e)}"
        logger.error(error)

    return {
        "url": url,
        "pages": pages,
        "error": error
    }


async def analyze_website_for_frameworks(db: Session, scraped_data: dict, llm_settings: dict = None) -> dict:
    """Analyze scraped website content using the LLM to recommend frameworks."""
    # Combine text from all pages, truncated to ~6000 chars total to keep LLM response fast
    combined_text = ""
    for page in scraped_data.get("pages", []):
        page_header = f"\n--- Page: {page['title']} ({page['url']}) ---\n"
        combined_text += page_header + page["text"] + "\n"
        if len(combined_text) > 6000:
            combined_text = combined_text[:6000]
            break

    if not combined_text.strip():
        return {
            "company_summary": "Could not extract any content from the website.",
            "recommendations": [],
            "scraped_pages": len(scraped_data.get("pages", []))
        }

    # Build framework list for the prompt
    framework_list = "\n".join(
        f"- {fw['template_id']}: {fw['name']} - {fw['description']}"
        for fw in AVAILABLE_FRAMEWORKS
    )

    prompt = f"""You are a cybersecurity compliance expert. Analyze the following company website content and recommend which compliance frameworks they should implement.

WEBSITE CONTENT:
{combined_text}

AVAILABLE FRAMEWORKS:
{framework_list}

Based on the website content, determine:
1. What industry/sector the company operates in
2. Where they operate geographically (EU, US, global, etc.)
3. What products or services they offer
4. What type of data they handle (personal data, payment data, health data, etc.)
5. Any existing compliance mentions

Return a JSON object with this exact structure (no markdown, no code fences, just raw JSON):
{{
  "company_summary": "Brief description of what the company does",
  "recommendations": [
    {{
      "template_id": "FRAMEWORK_ID",
      "framework_name": "Display Name",
      "relevance": "high",
      "reasoning": "Why this framework applies to this company",
      "priority": 1
    }}
  ]
}}

Only recommend frameworks that are genuinely relevant. Order by priority (1 = most important).
Do not recommend frameworks that have no clear relevance to the company.
Use only template_ids from the AVAILABLE FRAMEWORKS list above.
The relevance field must be one of: "high", "medium", or "low"."""

    try:
        llm_service = LLMService(db)

        # Use effective LLM settings if provided
        effective_provider = (llm_settings or {}).get("llm_provider", "llamacpp")

        if effective_provider == "qlon" and llm_settings and llm_settings.get("qlon_url") and llm_settings.get("qlon_api_key"):
            response_text = await llm_service.generate_text_with_qlon(
                prompt,
                qlon_url=llm_settings["qlon_url"],
                qlon_api_key=llm_settings["qlon_api_key"],
                use_tools=llm_settings.get("qlon_use_tools", True),
                timeout=600,
            )
        else:
            if effective_provider == "llamacpp":
                llm_service.llm_backend = "llamacpp"
            response_text = await llm_service.generate_text(prompt, timeout=600)

        # Try to parse JSON from the response
        result = _parse_llm_json(response_text)

        if result:
            return {
                "company_summary": result.get("company_summary", "No summary available"),
                "recommendations": result.get("recommendations", []),
                "scraped_pages": len(scraped_data.get("pages", []))
            }
        else:
            return {
                "company_summary": "The AI analysis completed but the response could not be parsed.",
                "recommendations": [],
                "scraped_pages": len(scraped_data.get("pages", []))
            }

    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        return {
            "company_summary": f"AI analysis failed: {str(e)}",
            "recommendations": [],
            "scraped_pages": len(scraped_data.get("pages", []))
        }


def _parse_llm_json(text: str) -> Optional[dict]:
    """Try to extract and parse JSON from LLM response text."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text (between { and })
    try:
        # Find the first { and last }
        start = text.index('{')
        end = text.rindex('}') + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError):
        pass

    logger.warning(f"Could not parse JSON from LLM response: {text[:200]}")
    return None

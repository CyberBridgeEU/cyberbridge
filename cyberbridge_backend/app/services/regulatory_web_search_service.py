import hashlib
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# EUR-Lex CELEX numbers for EU frameworks
EURLEX_CELEX_MAP = {
    "cra": "32024R2847",
    "nis2_directive": "32022L2555",
    "gdpr": "32016R0679",
    "dora_2022": "32022R2554",
}

# NIST publication IDs
NIST_PUB_MAP = {
    "nist_csf_2_0": "sp800-53",
    "cmmc_2_0": "sp800-171",
}


class RegulatoryWebSearchService:
    """Service for searching regulatory content from free sources."""

    def __init__(self, searxng_url: str = "http://searxng:8080"):
        self.searxng_url = searxng_url
        self.timeout = 30.0

    async def search_searxng(
        self,
        query: str,
        categories: str = "general",
        max_results: int = 10
    ) -> List[Dict]:
        """Search via self-hosted SearXNG meta-search engine."""
        results = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.searxng_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "categories": categories,
                        "pageno": 1,
                    }
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("results", [])[:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "source": "searxng",
                        "engine": item.get("engine", ""),
                    })

        except httpx.ConnectError:
            logger.warning("SearXNG not available - skipping search")
        except Exception as e:
            logger.error(f"SearXNG search error for '{query}': {e}")

        return results

    async def fetch_eurlex(self, celex_number: str) -> Optional[Dict]:
        """Fetch regulation text from EUR-Lex REST API (free, no key needed)."""
        try:
            url = f"https://eur-lex.europa.eu/eurlex-ws/rest/search"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use the search endpoint to get document metadata
                response = await client.get(
                    url,
                    params={
                        "text": f"celex:{celex_number}",
                        "type": "CELEX",
                        "lang": "EN"
                    }
                )

                if response.status_code == 200:
                    content = response.text
                    return {
                        "celex": celex_number,
                        "content": content[:50000],  # Limit size
                        "url": f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex_number}",
                        "source": "eurlex_api",
                        "fetched_at": datetime.utcnow().isoformat()
                    }

                # Fallback: fetch the HTML version directly
                html_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex_number}"
                html_response = await client.get(html_url, follow_redirects=True)
                if html_response.status_code == 200:
                    soup = BeautifulSoup(html_response.text, "html.parser")
                    # Extract the main regulation text
                    body = soup.find("div", {"id": "TexteOnly"}) or soup.find("body")
                    text_content = body.get_text(separator="\n", strip=True) if body else ""
                    return {
                        "celex": celex_number,
                        "content": text_content[:50000],
                        "url": html_url,
                        "source": "eurlex_api",
                        "fetched_at": datetime.utcnow().isoformat()
                    }

        except Exception as e:
            logger.error(f"EUR-Lex fetch error for CELEX {celex_number}: {e}")

        return None

    async def fetch_nist_publication(self, pub_id: str) -> Optional[Dict]:
        """Fetch NIST publication info from NIST CSRC."""
        try:
            url = f"https://csrc.nist.gov/pubs/sp/{pub_id.replace('sp', '').replace('-', '/')}"
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    main_content = soup.find("main") or soup.find("div", {"class": "pub-detail"}) or soup.find("body")
                    text_content = main_content.get_text(separator="\n", strip=True) if main_content else ""
                    return {
                        "publication_id": pub_id,
                        "content": text_content[:50000],
                        "url": str(response.url),
                        "source": "nist_api",
                        "fetched_at": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"NIST fetch error for {pub_id}: {e}")

        return None

    async def scrape_page(self, url: str, selectors: List[str] = None) -> Optional[Dict]:
        """Direct web scraping with optional CSS selectors."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "CyberBridge Regulatory Monitor/1.0"}
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    if selectors:
                        content_parts = []
                        for selector in selectors:
                            elements = soup.select(selector)
                            for el in elements:
                                content_parts.append(el.get_text(separator="\n", strip=True))
                        text_content = "\n\n".join(content_parts)
                    else:
                        # Remove script and style elements
                        for element in soup(["script", "style", "nav", "footer", "header"]):
                            element.decompose()
                        text_content = soup.get_text(separator="\n", strip=True)

                    return {
                        "url": url,
                        "content": text_content[:50000],
                        "source": "direct_scrape",
                        "fetched_at": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")

        return None

    async def fetch_for_source(self, source) -> List[Dict]:
        """
        Fetch content based on a RegulatorySource record.
        Returns list of results (each with content, url, source info).
        """
        results = []

        if source.source_type == "eurlex_api":
            celex = source.direct_url or EURLEX_CELEX_MAP.get(source.framework_type)
            if celex:
                result = await self.fetch_eurlex(celex)
                if result:
                    results.append(result)

        elif source.source_type == "nist_api":
            pub_id = source.direct_url or NIST_PUB_MAP.get(source.framework_type)
            if pub_id:
                result = await self.fetch_nist_publication(pub_id)
                if result:
                    results.append(result)

        elif source.source_type == "searxng":
            query = source.search_query or f"{source.framework_type} regulation amendment update"
            search_results = await self.search_searxng(query, max_results=5)

            # Optionally filter by domain
            if source.domain_filter:
                try:
                    allowed_domains = json.loads(source.domain_filter)
                    search_results = [
                        r for r in search_results
                        if any(d in r.get("url", "") for d in allowed_domains)
                    ]
                except json.JSONDecodeError:
                    pass

            # Scrape top results for full content
            for sr in search_results[:3]:
                scraped = await self.scrape_page(sr["url"])
                if scraped:
                    scraped["title"] = sr.get("title", "")
                    scraped["snippet"] = sr.get("content", "")
                    results.append(scraped)

        elif source.source_type == "direct_scrape":
            if source.direct_url:
                result = await self.scrape_page(source.direct_url)
                if result:
                    results.append(result)

        elif source.source_type == "rss":
            # RSS feed parsing
            if source.direct_url:
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(source.direct_url)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, "xml")
                            items = soup.find_all("item")[:5]
                            for item in items:
                                title = item.find("title")
                                link = item.find("link")
                                description = item.find("description")
                                results.append({
                                    "title": title.text if title else "",
                                    "url": link.text if link else "",
                                    "content": description.text if description else "",
                                    "source": "rss",
                                    "fetched_at": datetime.utcnow().isoformat()
                                })
                except Exception as e:
                    logger.error(f"RSS fetch error for {source.direct_url}: {e}")

        return results

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA256 hash of content for dedup."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def sanitize_content(content: str) -> str:
        """Remove NUL bytes and other characters that PostgreSQL Text columns reject."""
        return content.replace("\x00", "")

"""Web scraping fetcher implementation"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from radar.core.models import SourceConfig
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class ScrapeWebFetcher(BaseFetcher):
    """Web scraping fetcher for conference sites, job boards, and structured content"""

    def __init__(self, source_config: SourceConfig):
        super().__init__(source_config)
        self._validate_config()
        self._robots_delay: Optional[float] = None

    def _validate_config(self) -> None:
        """Validate source configuration"""
        config = self.source_config.config

        if not config.get("base_url"):
            raise ValueError(f"Scrape source {self.source_config.id} missing required 'base_url' config")

        if not config.get("selectors"):
            raise ValueError(f"Scrape source {self.source_config.id} missing required 'selectors' config")

        # Validate URL scheme for security
        base_url = config["base_url"]
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme '{parsed.scheme}' in base_url. Only http/https allowed.")

        # Validate domain allowlist if configured
        allowed_domains = config.get("allowed_domains")
        if allowed_domains and not self._is_domain_allowed(base_url):
            raise ValueError(f"Base URL domain not in allowed_domains list")

    def _is_domain_allowed(self, url: str) -> bool:
        """Check if URL domain is in allowlist"""
        allowed_domains = self.source_config.config.get("allowed_domains")
        if not allowed_domains:
            return True

        parsed = urlparse(url)
        return parsed.netloc in allowed_domains

    async def fetch_items(self) -> List[Dict[str, Any]]:
        """Fetch items from web pages with comprehensive error handling"""
        config = self.source_config.config
        base_url = config["base_url"]
        max_pages = config.get("max_pages", 1)
        politeness_delay = config.get("politeness_delay", 1.0)

        logger.info(f"Starting web scraping from: {base_url}")

        # Check robots.txt if requested
        if config.get("respect_robots", False):
            await self._check_robots_txt(base_url)

        items = []

        # Configure HTTP client with security headers
        headers = {
            "User-Agent": f"Radar/1.0 (+https://github.com/radar; respectful web scraper for {self.source_config.id})",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        timeout = httpx.Timeout(30.0, connect=10.0)

        async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                try:
                    # Build URL for current page
                    page_url = self._build_page_url(base_url, page)

                    # Respect politeness delay between requests
                    if page > 1:
                        delay = self._robots_delay or politeness_delay
                        logger.debug(f"Politeness delay: {delay}s before fetching page {page}")
                        await asyncio.sleep(delay)

                    # Fetch page with retry logic
                    html_content = await self._fetch_page_with_retry(client, page_url)

                    if not html_content:
                        logger.warning(f"Empty response from {page_url}")
                        continue

                    # Parse and extract items
                    page_items = self._extract_items_from_html(html_content, page_url)

                    if not page_items:
                        logger.info(f"No items found on page {page}, stopping pagination")
                        break

                    items.extend(page_items)
                    logger.info(f"Extracted {len(page_items)} items from page {page}")

                except Exception as e:
                    logger.exception("Error processing page %d: %s", page, e)
                    # Continue with next page rather than failing completely
                    continue

        logger.info(f"Successfully scraped {len(items)} total items")
        return items

    def _build_page_url(self, base_url: str, page: int) -> str:
        """Build URL for specific page based on pagination config"""
        config = self.source_config.config
        pagination = config.get("pagination")

        if not pagination or page == 1:
            return base_url

        param = pagination.get("param", "page")
        start = pagination.get("start", 1)
        page_num = start + page - 1

        # Simple pagination parameter appending
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}{param}={page_num}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout))
    )
    async def _fetch_page_with_retry(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch page content with retry logic"""
        logger.debug(f"Fetching URL: {url}")

        response = await client.get(url)
        response.raise_for_status()

        # Validate content type
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("text/html"):
            logger.warning(f"Unexpected content type: {content_type}")

        return response.text

    async def _check_robots_txt(self, base_url: str) -> None:
        """Check robots.txt for crawl delay and restrictions"""
        try:
            parsed = urlparse(base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(robots_url)

                if response.status_code == 200:
                    robots_parser = RobotFileParser()
                    robots_parser.set_url(robots_url)
                    robots_parser.feed(response.text)

                    # Extract crawl delay
                    crawl_delay = robots_parser.crawl_delay("*")
                    if crawl_delay:
                        self._robots_delay = float(crawl_delay)
                        logger.info(f"Robots.txt crawl-delay: {self._robots_delay}s")

        except Exception as e:
            logger.debug(f"Could not fetch robots.txt: {e}")
            # Not a critical error, continue without robots.txt constraints

    def _extract_items_from_html(self, html_content: str, page_url: str) -> List[Dict[str, Any]]:
        """Extract items from HTML content using configured selectors"""
        config = self.source_config.config
        selectors = config["selectors"]

        try:
            # Parse HTML with lxml parser for performance
            soup = BeautifulSoup(html_content, 'lxml')

            # Find container elements
            container_selector = selectors.get("container", "body")
            containers = soup.select(container_selector)

            if not containers:
                logger.warning(f"No containers found with selector: {container_selector}")
                return []

            items = []
            fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Process each container to extract items
            for container in containers:
                # Find individual item elements within container
                item_elements = self._find_item_elements(container, selectors)

                for item_elem in item_elements:
                    try:
                        item = self._extract_item_data(item_elem, selectors, page_url, fetched_at)
                        if item:
                            items.append(item)
                    except Exception as e:
                        logger.warning(f"Failed to extract item data: {e}")
                        continue

            return items

        except Exception as e:
            logger.exception("HTML parsing error: %s", e)
            return []

    def _find_item_elements(self, container, selectors: Dict[str, str]) -> List:
        """Find individual item elements within container"""
        # Look for a common parent element that contains item data
        # Try various strategies to identify item boundaries

        title_selector = selectors.get("title")
        if title_selector:
            # Find elements with titles and use their parent containers as items
            title_elements = container.select(title_selector)

            # Group by common parent to identify item boundaries
            item_elements = []
            processed_parents = set()

            for title_elem in title_elements:
                # Find appropriate parent that likely contains the full item
                parent = self._find_item_parent(title_elem, selectors)
                if parent and id(parent) not in processed_parents:
                    item_elements.append(parent)
                    processed_parents.add(id(parent))

            return item_elements
        else:
            # Fallback: treat container children as items
            return [child for child in container.children if hasattr(child, 'select')]

    def _find_item_parent(self, title_element, selectors: Dict[str, str]) -> Optional:
        """Find the appropriate parent element that contains the full item"""
        current = title_element.parent

        while current and current.name:
            # Check if this parent contains other expected elements
            has_link = bool(current.select(selectors.get("link", ""))) if selectors.get("link") else True

            # If parent contains expected elements or is a reasonable container, use it
            if has_link and current.name in ("div", "article", "section", "li", "tr"):
                return current

            current = current.parent

        # Fallback to original title element's immediate parent
        return title_element.parent

    def _extract_item_data(self, item_element, selectors: Dict[str, str], page_url: str, fetched_at: str) -> Optional[Dict[str, Any]]:
        """Extract data from individual item element"""
        try:
            # Extract title
            title = self._extract_text_content(item_element, selectors.get("title", ""))
            if not title:
                return None

            # Sanitize title for XSS prevention
            title = self._sanitize_text(title)

            # Extract link
            link = self._extract_link_content(item_element, selectors.get("link", ""), page_url)
            if not link:
                return None

            # Validate and sanitize URL
            if not self._is_safe_url(link):
                logger.warning(f"Unsafe URL detected, skipping: {link}")
                return None

            # Extract additional metadata
            raw_text_parts = [title]

            for field_name, selector in selectors.items():
                if field_name not in ("title", "link", "container"):
                    content = self._extract_text_content(item_element, selector)
                    if content:
                        sanitized_content = self._sanitize_text(content)
                        raw_text_parts.append(f"{field_name}: {sanitized_content}")

            # Generate stable item ID
            item_id = hashlib.sha1(f"{title}:{link}".encode('utf-8')).hexdigest()

            return {
                "item_id": item_id,
                "title": title,
                "url": link,
                "source_id": self.source_config.id,
                "signal_type": self.source_config.signal_type,
                "audience_tags": self.source_config.audience_tags,
                "timestamp": fetched_at,
                "raw_text": " | ".join(raw_text_parts),
                "metrics": {"score": 0, "comments": 0, "stars": None},
                "relevance_tags": self.source_config.relevance_tags,
                "fetched_at": fetched_at,
                "dedup_key": item_id,
            }

        except Exception as e:
            logger.warning(f"Error extracting item data: {e}")
            return None

    def _extract_text_content(self, element, selector: str) -> str:
        """Extract text content using CSS selector"""
        if not selector:
            return ""

        try:
            selected = element.select_one(selector)
            if selected:
                return selected.get_text(strip=True)
            return ""
        except Exception as e:
            logger.debug(f"Error selecting '{selector}': {e}")
            return ""

    def _extract_link_content(self, element, selector: str, base_url: str) -> str:
        """Extract link URL using CSS selector"""
        if not selector:
            return ""

        try:
            selected = element.select_one(selector)
            if selected:
                # Try href attribute first, then look for data attributes
                href = selected.get('href') or selected.get('data-href') or selected.get('data-url')
                if href:
                    # Convert relative URLs to absolute
                    return urljoin(base_url, href)
            return ""
        except Exception as e:
            logger.debug(f"Error extracting link with '{selector}': {e}")
            return ""

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text content to prevent XSS and normalize whitespace"""
        if not text:
            return ""

        # Remove potentially dangerous content
        # Remove script tags and content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

        # Remove other HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Truncate for storage efficiency
        return text[:500]

    def _is_safe_url(self, url: str) -> bool:
        """Validate URL safety to prevent dangerous schemes"""
        if not url:
            return False

        try:
            parsed = urlparse(url)

            # Only allow http/https schemes
            if parsed.scheme not in ("http", "https"):
                return False

            # Check domain allowlist if configured
            if not self._is_domain_allowed(url):
                return False

            return True

        except Exception:
            return False


# Register with fetcher registry
from .registry import FetcherRegistry
from radar.core.models import SourceType

FetcherRegistry.register_fetcher(SourceType.scrape, ScrapeWebFetcher)
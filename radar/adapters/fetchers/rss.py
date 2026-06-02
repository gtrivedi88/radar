# radar/adapters/fetchers/rss.py
"""RSS feed fetcher implementation"""

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

import feedparser
import httpx

from radar.core.models import SourceConfig
from .base import BaseFetcher

logger = logging.getLogger(__name__)

class RSSFetcher(BaseFetcher):
    """RSS/Atom feed fetcher using feedparser"""

    # Class-level shared executor to avoid resource waste
    _shared_executor: Optional[ThreadPoolExecutor] = None

    def __init__(self, source_config: SourceConfig, transport: Optional[httpx.BaseTransport] = None):
        super().__init__(source_config)
        self._transport = transport

    @classmethod
    def get_executor(cls) -> ThreadPoolExecutor:
        """Get shared executor for RSS processing"""
        if cls._shared_executor is None:
            cls._shared_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="rss-")
        return cls._shared_executor

    @classmethod
    def shutdown_executor(cls):
        """Shutdown shared executor - call during application cleanup"""
        if cls._shared_executor is not None:
            cls._shared_executor.shutdown(wait=True)
            cls._shared_executor = None

    async def fetch_items(self) -> List[Dict[str, Any]]:
        """Fetch items from RSS feed with retry logic"""
        config = self.source_config.config
        feed_url = config.get("feed_url")

        # Add input validation
        if not feed_url:
            raise ValueError(f"RSS source {self.source_config.id} missing required 'feed_url' config")

        logger.info(f"Fetching RSS feed: {feed_url}")

        # Fetch feed data with retry logic
        feed_data = await self._fetch_feed_with_retry(feed_url)
        entries = feed_data.get('entries', [])
        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        logger.info(f"Retrieved {len(entries)} entries from RSS feed")

        # Process entries
        items = self._process_entries(entries, fetched_at)

        logger.info(f"Successfully normalized {len(items)} RSS items")
        return items

    async def _fetch_feed_with_retry(self, feed_url: str) -> Dict[str, Any]:
        """Fetch RSS feed data with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                feed_data = await loop.run_in_executor(self.get_executor(), feedparser.parse, feed_url)

                # Check for parsing issues using getattr for safe access
                if getattr(feed_data, 'bozo', False):
                    bozo_exception = getattr(feed_data, 'bozo_exception', 'Unknown parsing issue')
                    logger.warning(f"RSS feed parsing issues for {feed_url}: {bozo_exception}")
                    if attempt < max_retries - 1 and "timeout" in str(bozo_exception).lower():
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue

                return feed_data  # Success

            except Exception as e:
                logger.warning(f"RSS fetch attempt {attempt + 1} failed for {feed_url}: {e}")
                if attempt == max_retries - 1:
                    raise  # Re-raise on final attempt
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {}  # Fallback (shouldn't reach here)

    def _process_entries(self, entries: List[Dict[str, Any]], fetched_at: str) -> List[Dict[str, Any]]:
        """Process RSS entries into normalized items"""
        items = []
        for entry in entries:
            try:
                item = self._normalize_rss_entry(entry, fetched_at)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to normalize RSS entry: {e}")
                continue
        return items

    def _normalize_rss_entry(self, entry: Dict[str, Any], fetched_at: str) -> Optional[Dict[str, Any]]:
        """Normalize RSS entry to canonical format"""
        title = entry.get('title', '').strip()
        if not title:
            return None

        link = entry.get('link', '')
        if not link:
            return None

        # Validate URL scheme for security
        if not link.startswith(('http://', 'https://')):
            logger.warning(f"Skipping RSS entry with invalid URL scheme: {link}")
            return None

        # Generate stable item ID
        item_id = hashlib.sha1(f"{title}:{link}".encode('utf-8')).hexdigest()

        # Parse published date with fallback
        timestamp = fetched_at
        if 'published' in entry:
            try:
                published_time = entry.get('published_parsed')
                if published_time:
                    dt = datetime(*published_time[:6], tzinfo=timezone.utc)
                    timestamp = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass  # Use fetched_at as fallback

        # Extract and sanitize content with hierarchy
        content = ''
        if 'summary' in entry:
            content = entry['summary']
        elif 'content' in entry and entry['content']:
            content = entry['content'][0].get('value', '')
        elif 'description' in entry:
            content = entry['description']

        # Enhanced content sanitization
        if content:
            # Remove HTML tags more thoroughly (feedparser should handle most)
            content = re.sub(r'<[^>]+>', '', content)
            # Normalize whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            # Truncate for storage
            content = content[:2000]

        return {
            "item_id": item_id,
            "title": title,
            "url": link,
            "source_id": self.source_config.id,
            "signal_type": self.source_config.signal_type,
            "audience_tags": self.source_config.audience_tags,
            "timestamp": timestamp,
            "raw_text": content,
            "metrics": {"score": 0, "comments": 0, "stars": None},
            "relevance_tags": self.source_config.relevance_tags,
            "fetched_at": fetched_at,
            "dedup_key": item_id,
        }


# Register with fetcher registry
from .registry import FetcherRegistry
from radar.core.models import SourceType

FetcherRegistry.register_fetcher(SourceType.rss, RSSFetcher)
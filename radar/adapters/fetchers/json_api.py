"""JSON API fetcher implementations"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

import httpx

from radar.core.models import SourceConfig
from .base import BaseFetcher

logger = logging.getLogger(__name__)


def compute_item_id(title: str, url: str) -> str:
    """Generate stable SHA-1 hash for item identification"""
    h = hashlib.sha1()
    h.update(title.encode("utf-8"))
    h.update(b"\x00")
    h.update(url.encode("utf-8"))
    return h.hexdigest()


def iso_now() -> str:
    """Current UTC time in ISO 8601 format with Z suffix"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class HNAlgoliaFetcher(BaseFetcher):
    """Hacker News fetcher using the public Algolia search API

    No authentication required.
    API Docs: https://hn.algolia.com/api
    """

    def __init__(self, source_config: SourceConfig, transport: Optional[httpx.BaseTransport] = None):
        super().__init__(source_config)
        self._transport = transport

    async def fetch_items(self) -> List[Dict[str, Any]]:
        """Fetch items from HN Algolia API"""
        config = self.source_config.config
        endpoint: str = config["endpoint"]
        params: Dict[str, Any] = config.get("query_params", {})

        logger.info(f"Fetching from HN Algolia: {endpoint}")

        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

        hits = data.get("hits", [])
        fetched_at = iso_now()

        logger.info(f"Retrieved {len(hits)} items from HN Algolia")

        items = []
        for hit in hits:
            try:
                item = await self._normalize_hn_item(hit, fetched_at)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to normalize HN item {hit.get('objectID')}: {e}")
                continue

        logger.info(f"Successfully normalized {len(items)} items")
        return items

    async def _normalize_hn_item(self, hit: Dict[str, Any], fetched_at: str) -> Optional[Dict[str, Any]]:
        """Normalize HN Algolia item to canonical format"""
        title = (hit.get("title") or hit.get("story_title") or "").strip()
        if not title:
            return None

        # Handle URL - if missing, use HN permalink
        url = hit.get("url")
        if not url and hit.get("objectID"):
            url = f"https://news.ycombinator.com/item?id={hit['objectID']}"

        if not url:
            return None

        # Generate stable item ID
        item_id = compute_item_id(title, url)

        # Extract metrics
        metrics = {
            "score": hit.get("points") or 0,
            "comments": hit.get("num_comments") or 0,
            "stars": None,  # HN doesn't have stars
        }

        # Raw text content (story text or summary)
        raw_text = (hit.get("story_text") or hit.get("comment_text") or "")[:2000]

        return {
            "item_id": item_id,
            "title": title,
            "url": url,
            "source_id": self.source_config.id,
            "signal_type": list(self.source_config.signal_type),
            "audience_tags": list(self.source_config.audience_tags),
            "timestamp": hit.get("created_at"),
            "raw_text": raw_text,
            "metrics": metrics,
            "relevance_tags": list(self.source_config.relevance_tags),
            "fetched_at": fetched_at,
            "dedup_key": item_id,  # Use item_id as dedup key by default
        }


# Register the fetcher when module is imported
from .registry import FetcherRegistry
from radar.core.models import SourceType

FetcherRegistry.register_fetcher(SourceType.json_api, HNAlgoliaFetcher)
"""
Enhanced fetchers with autonomous monitoring capabilities
Extends our simple YAML-based fetchers with threshold monitoring
"""

import asyncio
import httpx
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Any
import yaml
from pathlib import Path

from ..core.base import BaseFetcher, IntelligenceItem


class EnhancedYAMLFetcher(BaseFetcher):
    """Enhanced fetcher that reads YAML configs and supports threshold monitoring"""

    @classmethod
    async def create_from_yaml(cls, yaml_path: Path, http_client: httpx.AsyncClient):
        """Create fetcher from YAML configuration"""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)

        return cls(config, http_client)

    async def fetch(self) -> List[IntelligenceItem]:
        """Fetch intelligence items based on source type"""
        if self.config['type'] == 'json_api':
            return await self._fetch_json_api()
        elif self.config['type'] == 'rss':
            return await self._fetch_rss()
        else:
            raise ValueError(f"Unsupported source type: {self.config['type']}")

    async def _fetch_json_api(self) -> List[IntelligenceItem]:
        """Fetch from JSON API with error handling"""
        try:
            config = self.config['config']
            response = await self.client.get(
                config['endpoint'],
                params=config.get('query_params', {}),
                headers=config.get('headers', {}),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            items = []
            raw_items = data.get('hits', data) if isinstance(data, dict) else data

            for item in raw_items[:20]:  # Limit items
                intelligence_item = IntelligenceItem(
                    title=item.get('title', item.get('story_title', 'Untitled')),
                    url=item.get('url', item.get('story_url', '')),
                    score=item.get('points', item.get('score', 0)),
                    comments=item.get('num_comments', 0),
                    timestamp=item.get('created_at', datetime.now(timezone.utc).isoformat()),
                    source_id=self.config['id'],
                    metadata={'raw_item': item}
                )
                items.append(intelligence_item)

            return items

        except Exception as e:
            print(f"Error fetching from {self.config['id']}: {e}")
            return []

    async def _fetch_rss(self) -> List[IntelligenceItem]:
        """Fetch from RSS feed"""
        try:
            config = self.config['config']
            response = await self.client.get(config['endpoint'], timeout=30)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            items = []

            for entry in feed.entries[:10]:
                intelligence_item = IntelligenceItem(
                    title=entry.get('title', 'Untitled'),
                    url=entry.get('link', ''),
                    score=0,  # RSS doesn't have scores
                    comments=0,
                    timestamp=entry.get('published', datetime.now(timezone.utc).isoformat()),
                    source_id=self.config['id'],
                    content=entry.get('summary', ''),
                    metadata={'raw_entry': entry}
                )
                items.append(intelligence_item)

            return items

        except Exception as e:
            print(f"Error fetching RSS from {self.config['id']}: {e}")
            return []

    def has_threshold_signals(self, items: List[IntelligenceItem]) -> Dict[str, Any]:
        """Check if any items meet strategic threshold criteria"""
        high_engagement = [item for item in items if item.score > 500]
        contrarian_signals = [item for item in items if self._is_contrarian(item)]

        return {
            "high_engagement_count": len(high_engagement),
            "contrarian_signals_count": len(contrarian_signals),
            "total_engagement": sum(item.score for item in items),
            "top_item_score": max(item.score for item in items) if items else 0,
            "alert_worthy": len(high_engagement) > 0 or len(contrarian_signals) > 0
        }

    def _is_contrarian(self, item: IntelligenceItem) -> bool:
        """Detect if an item represents contrarian intelligence"""
        # Simple heuristic - look for contrarian keywords in title
        contrarian_keywords = [
            'beats', 'vs', 'wrong about', 'myth', 'actually', 'really',
            'truth about', 'why', 'problem with', 'better than'
        ]

        title_lower = item.title.lower()
        return any(keyword in title_lower for keyword in contrarian_keywords)


class ParallelFetchOrchestrator:
    """Orchestrates parallel fetching from multiple sources with threshold monitoring"""

    def __init__(self, sources_dir: Path):
        self.sources_dir = Path(sources_dir)
        self.http_client = httpx.AsyncClient()

    async def fetch_all_sources(self) -> Dict[str, Any]:
        """Fetch from all configured sources in parallel"""
        yaml_files = list(self.sources_dir.glob("*.yaml"))
        if not yaml_files:
            return {"error": "No source configurations found"}

        # Create fetchers
        fetchers = []
        for yaml_file in yaml_files:
            try:
                fetcher = await EnhancedYAMLFetcher.create_from_yaml(yaml_file, self.http_client)
                fetchers.append(fetcher)
            except Exception as e:
                print(f"Error creating fetcher from {yaml_file}: {e}")

        # Fetch in parallel
        tasks = [fetcher.fetch() for fetcher in fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        all_items = []
        source_results = {}
        threshold_alerts = []

        for fetcher, result in zip(fetchers, results):
            if isinstance(result, Exception):
                print(f"Error fetching from {fetcher.config['id']}: {result}")
                continue

            items = result
            all_items.extend(items)
            source_results[fetcher.config['id']] = {
                "items_count": len(items),
                "items": items
            }

            # Check for threshold signals
            thresholds = fetcher.has_threshold_signals(items)
            if thresholds["alert_worthy"]:
                threshold_alerts.append({
                    "source": fetcher.config['id'],
                    "thresholds": thresholds,
                    "timestamp": datetime.now().isoformat()
                })

        return {
            "total_items": len(all_items),
            "source_results": source_results,
            "threshold_alerts": threshold_alerts,
            "all_items": all_items
        }

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
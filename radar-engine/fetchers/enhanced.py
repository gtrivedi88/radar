"""
Dumb fetchers — fetch data from YAML-configured sources, save to disk.
No intelligence, no keyword matching, no threshold analysis.
"""

import asyncio
import httpx
import feedparser
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
import yaml
from pathlib import Path

from ..core.base import BaseFetcher, IntelligenceItem


class EnhancedYAMLFetcher(BaseFetcher):
    """Fetcher that reads YAML configs and fetches data. No analysis."""

    @classmethod
    async def create_from_yaml(cls, yaml_path: Path, http_client: httpx.AsyncClient):
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        return cls(config, http_client)

    async def fetch(self) -> List[IntelligenceItem]:
        if self.config['type'] == 'json_api':
            items = await self._fetch_json_api()
        elif self.config['type'] == 'rss':
            items = await self._fetch_rss()
        else:
            raise ValueError(f"Unsupported source type: {self.config['type']}")
        return self._apply_pre_filters(items)

    async def _fetch_json_api(self) -> List[IntelligenceItem]:
        """Fetch from JSON API with configurable field mapping"""
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

            results_key = config.get('results_key')
            if results_key:
                raw_items = data.get(results_key, [])
            elif isinstance(data, dict):
                raw_items = data.get('hits', data)
            else:
                raw_items = data

            fm = config.get('field_map', {})
            title_fields = fm.get('title', ['title', 'story_title'])
            url_fields = fm.get('url', ['url', 'story_url'])
            score_fields = fm.get('score', ['points', 'score'])
            comments_fields = fm.get('comments', ['num_comments', 'comment_count', 'comments_count'])
            timestamp_fields = fm.get('timestamp', ['created_at', 'published_timestamp', 'published_at'])
            content_fields = fm.get('content', ['description', 'description_plain', 'summary'])

            items = []
            for item in raw_items[:20]:
                items.append(IntelligenceItem(
                    title=self._extract_field(item, title_fields, 'Untitled'),
                    url=self._extract_field(item, url_fields, ''),
                    score=int(self._extract_field(item, score_fields, 0)),
                    comments=int(self._extract_field(item, comments_fields, 0)),
                    timestamp=self._extract_field(item, timestamp_fields, datetime.now(timezone.utc).isoformat()),
                    source_id=self.config['id'],
                    content=self._extract_field(item, content_fields, ''),
                ))
            return items

        except Exception as e:
            print(f"Error fetching from {self.config['id']}: {e}")
            return []

    async def _fetch_rss(self) -> List[IntelligenceItem]:
        try:
            config = self.config['config']
            response = await self.client.get(config['endpoint'], timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            items = []
            for entry in feed.entries[:10]:
                items.append(IntelligenceItem(
                    title=entry.get('title', 'Untitled'),
                    url=entry.get('link', ''),
                    score=0,
                    comments=0,
                    timestamp=entry.get('published', datetime.now(timezone.utc).isoformat()),
                    source_id=self.config['id'],
                    content=entry.get('summary', ''),
                ))
            return items
        except Exception as e:
            print(f"Error fetching RSS from {self.config['id']}: {e}")
            return []

    @staticmethod
    def _extract_field(item: dict, field_names, default=''):
        if isinstance(field_names, str):
            field_names = [field_names]
        for name in field_names:
            val = item.get(name)
            if val is not None and val != '':
                return val
        return default

    def _apply_pre_filters(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Basic noise floor: engagement minimum, recency, dedup. No keyword analysis."""
        pre_filter = self.config.get('pre_filter', {})
        if not pre_filter:
            return items

        original_count = len(items)
        filtered = items

        # Drop zero-engagement noise
        min_engagement = pre_filter.get('min_engagement', 0)
        if min_engagement > 0:
            filtered = [i for i in filtered if (i.score + i.comments) >= min_engagement]

        # Recency window
        recency_hours = pre_filter.get('recency_window_hours', 0)
        if recency_hours > 0:
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(hours=recency_hours)
            filtered = [i for i in filtered if self._is_recent(i, cutoff)]

        # URL dedup within source
        dedup_key = pre_filter.get('dedup_key', '')
        if dedup_key:
            seen = set()
            deduped = []
            for item in filtered:
                val = getattr(item, dedup_key, None)
                if val and val in seen:
                    continue
                if val:
                    seen.add(val)
                deduped.append(item)
            filtered = deduped

        if len(filtered) != original_count:
            print(f"🔍 Pre-filtered {self.config['id']}: {original_count} → {len(filtered)} items")

        return filtered

    def _is_recent(self, item: IntelligenceItem, cutoff: datetime) -> bool:
        try:
            if isinstance(item.timestamp, str):
                item_time = datetime.fromisoformat(item.timestamp.replace('Z', '+00:00'))
            else:
                item_time = datetime.fromtimestamp(item.timestamp, tz=timezone.utc)
            if item_time.tzinfo is None:
                item_time = item_time.replace(tzinfo=timezone.utc)
            return item_time >= cutoff
        except (ValueError, AttributeError):
            return True


class ParallelFetchOrchestrator:
    """Fetch from all sources in parallel, dedup, save raw JSON. Nothing else."""

    def __init__(self, sources_dir: Path):
        self.sources_dir = Path(sources_dir)
        self.http_client = httpx.AsyncClient()

    async def fetch_all_sources(self) -> Dict[str, Any]:
        yaml_files = list(self.sources_dir.glob("*.yaml"))
        if not yaml_files:
            return {"error": "No source configurations found"}

        enabled_configs = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    config = yaml.safe_load(f)
                if not config.get('enabled', True):
                    print(f"⏭️  Skipping disabled source: {config.get('id', yaml_file.name)}")
                    continue
                enabled_configs.append((yaml_file, config))
            except Exception as e:
                print(f"Error reading config from {yaml_file}: {e}")

        enabled_configs.sort(key=lambda x: x[1].get('priority', 3))

        if len(enabled_configs) > 1:
            priority_info = [f"{cfg['id']}(p{cfg.get('priority', 3)})" for _, cfg in enabled_configs]
            print(f"📋 Source priority order: {' → '.join(priority_info)}")

        fetchers = []
        for yaml_file, config in enabled_configs:
            try:
                fetcher = await EnhancedYAMLFetcher.create_from_yaml(yaml_file, self.http_client)
                fetchers.append(fetcher)
            except Exception as e:
                print(f"Error creating fetcher from {yaml_file}: {e}")

        tasks = [fetcher.fetch() for fetcher in fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items = []
        source_results = {}
        for fetcher, result in zip(fetchers, results):
            if isinstance(result, Exception):
                print(f"Error fetching from {fetcher.config['id']}: {result}")
                continue
            all_items.extend(result)
            source_results[fetcher.config['id']] = {"items_count": len(result), "items": result}

        # Cross-source URL dedup
        seen_urls = set()
        deduped = []
        dupes = 0
        for item in all_items:
            if item.url and item.url in seen_urls:
                dupes += 1
                continue
            if item.url:
                seen_urls.add(item.url)
            deduped.append(item)
        if dupes:
            print(f"🔗 Removed {dupes} cross-source duplicates")
        all_items = deduped

        # Save raw data
        if source_results:
            self._save_raw_data(source_results)

        return {
            "total_items": len(all_items),
            "source_results": source_results,
            "all_items": all_items
        }

    def _save_raw_data(self, source_results: Dict[str, Any]):
        today = datetime.now().strftime("%Y-%m-%d")
        raw_dir = Path("raw") / today
        raw_dir.mkdir(parents=True, exist_ok=True)

        for source_id, data in source_results.items():
            if "items" in data:
                json_items = [{
                    "title": item.title,
                    "url": item.url,
                    "score": item.score,
                    "comments": item.comments,
                    "timestamp": item.timestamp,
                    "source_id": item.source_id,
                    "content": item.content,
                } for item in data["items"]]

                file_path = raw_dir / f"{source_id}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_items, f, indent=2, ensure_ascii=False, default=str)
                print(f"💾 Saved {len(json_items)} items to {file_path}")

    async def close(self):
        await self.http_client.aclose()

#!/usr/bin/env python3
"""
Simple source fetcher for Radar v1
Fetches from YAML-configured sources and stores as JSON
"""

import json
import os
import sys
import yaml
import httpx
import feedparser
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

def load_sources() -> List[Dict[str, Any]]:
    """Load all enabled sources from sources/ directory"""
    sources = []
    sources_dir = Path("sources")

    for yaml_file in sources_dir.glob("*.yaml"):
        with open(yaml_file, 'r') as f:
            source = yaml.safe_load(f)
            if source.get('enabled', True):
                sources.append(source)

    return sources

def fetch_json_api(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch from JSON API endpoint"""
    config = source['config']

    try:
        response = httpx.get(
            config['endpoint'],
            params=config.get('query_params', {}),
            headers=config.get('headers', {}),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        # Extract items (handle different API structures)
        if 'hits' in data:  # HN Algolia format
            items = data['hits']
        elif isinstance(data, list):
            items = data
        else:
            items = [data]

        # Normalize format
        normalized = []
        for item in items[:20]:  # Limit to 20 items
            normalized.append({
                'title': item.get('title', item.get('story_title', 'Untitled')),
                'url': item.get('url', item.get('story_url', '')),
                'score': item.get('points', item.get('score', 0)),
                'comments': item.get('num_comments', 0),
                'timestamp': item.get('created_at', datetime.now(timezone.utc).isoformat()),
                'source_id': source['id'],
                'raw_item': item
            })

        return normalized

    except Exception as e:
        print(f"Error fetching {source['id']}: {e}")
        return []

def fetch_rss(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch from RSS feed"""
    config = source['config']

    try:
        feed = feedparser.parse(config['endpoint'])

        normalized = []
        for entry in feed.entries[:10]:  # Limit to 10 items
            normalized.append({
                'title': entry.get('title', 'Untitled'),
                'url': entry.get('link', ''),
                'score': 0,  # RSS doesn't have scores
                'comments': 0,
                'timestamp': entry.get('published', datetime.now(timezone.utc).isoformat()),
                'summary': entry.get('summary', ''),
                'source_id': source['id'],
                'raw_item': entry
            })

        return normalized

    except Exception as e:
        print(f"Error fetching RSS {source['id']}: {e}")
        return []

def main():
    """Fetch all enabled sources and save to raw/ directory"""

    # Create raw directory with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    raw_dir = Path(f"raw/{today}")
    raw_dir.mkdir(parents=True, exist_ok=True)

    sources = load_sources()
    total_items = 0

    for source in sources:
        print(f"Fetching {source['name']} ({source['id']})...")

        if source['type'] == 'json_api':
            items = fetch_json_api(source)
        elif source['type'] == 'rss':
            items = fetch_rss(source)
        else:
            print(f"Unknown source type: {source['type']}")
            continue

        # Save to file
        output_file = raw_dir / f"{source['id']}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'source': source['id'],
                'fetched_at': datetime.now(timezone.utc).isoformat(),
                'items': items
            }, f, indent=2)

        print(f"  → Saved {len(items)} items to {output_file}")
        total_items += len(items)

    print(f"\n✅ Fetched {total_items} total items from {len(sources)} sources")
    print(f"Data saved to: {raw_dir}")

if __name__ == "__main__":
    main()
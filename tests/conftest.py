"""Test configuration and fixtures"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

import pytest
import httpx
from httpx import MockTransport, Response

from radar.core.models import SourceConfig, SourceType, PreFilter


@pytest.fixture
def temp_radar_root(tmp_path: Path) -> Path:
    """Isolated radar environment for testing"""
    for subdir in ("state", "sources", "raw", "intermediate"):
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def sample_source_config() -> SourceConfig:
    """Standard test source configuration"""
    return SourceConfig(
        id="test-source",
        name="Test Source",
        type=SourceType.json_api,
        config={"endpoint": "https://api.example.com"},
        poll_cadence="daily",
        signal_type=["news"],
        audience_tags=["test"],
        pre_filter=PreFilter(),
        priority=1,
    )


@pytest.fixture
def hn_source_config() -> SourceConfig:
    """HN Algolia source configuration for testing"""
    return SourceConfig(
        id="hn-algolia",
        name="Hacker News (Algolia)",
        type=SourceType.json_api,
        config={
            "endpoint": "https://hn.algolia.com/api/v1/search",
            "query_params": {"tags": "front_page"}
        },
        poll_cadence="daily",
        signal_type=["news", "capability"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["hn"],
        pre_filter=PreFilter(min_engagement=50, recency_window_days=14),
        priority=1,
    )


@pytest.fixture
def mock_hn_response() -> Dict[str, Any]:
    """Mock HN Algolia API response"""
    return {
        "hits": [
            {
                "objectID": "1001",
                "title": "Claude 4.7 launches with enhanced capabilities",
                "url": "https://www.anthropic.com/news/claude-4-7",
                "points": 420,
                "num_comments": 88,
                "created_at": "2026-05-26T12:00:00Z",
                "story_text": None,
            },
            {
                "objectID": "1002",
                "title": "Ask HN: Best practices for prompt caching",
                "url": None,
                "points": 75,
                "num_comments": 33,
                "created_at": "2026-05-25T10:00:00Z",
                "story_text": "I have been experimenting with...",
            },
        ]
    }


@pytest.fixture
def mock_transport() -> MockTransport:
    """HTTP mock transport for testing"""
    def handler(request: httpx.Request) -> Response:
        return Response(200, json={"test": "data"})
    return MockTransport(handler)


@pytest.fixture
def mock_hn_transport(mock_hn_response: Dict[str, Any]) -> MockTransport:
    """Mock transport specifically for HN Algolia responses"""
    def handler(request: httpx.Request) -> Response:
        if "hn.algolia.com" in str(request.url):
            return Response(200, json=mock_hn_response)
        return Response(404, json={"error": "Not found"})
    return MockTransport(handler)


@pytest.fixture(scope="session")
def event_loop():
    """Provide event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_state_files(temp_radar_root: Path) -> Dict[str, Path]:
    """Create mock state files with sample content"""
    state_dir = temp_radar_root / "state"

    # Create sample profile
    profile = state_dir / "profile.md"
    profile.write_text("""# Operator Profile

## Identity
- Name: Test Operator
- Audiences served: tech_writer, devs_curious_ai, hardcore_tech
- Voice DNA: technical, direct, evidence-based

## Beat
- AI tools for technical writing
- Developer experience evolution
- Claude Code workflows
""")

    # Create sample catalog
    catalog = state_dir / "catalog.md"
    catalog.write_text("""# Published Work

## Blog Posts
- 2026-05-01 | Getting Started with Claude Code | /claude-code-intro/
""")

    # Create empty state files
    for filename in ["trajectory.md", "feedback.md", "signals.jsonl", "watermarks.json", "fetch-errors.jsonl"]:
        (state_dir / filename).touch()

    return {
        "profile": profile,
        "catalog": catalog,
        "trajectory": state_dir / "trajectory.md",
        "feedback": state_dir / "feedback.md",
        "signals": state_dir / "signals.jsonl",
        "watermarks": state_dir / "watermarks.json",
        "errors": state_dir / "fetch-errors.jsonl",
    }


@pytest.fixture
def sample_source_yaml(temp_radar_root: Path) -> Path:
    """Create sample source YAML file"""
    sources_dir = temp_radar_root / "sources"
    source_file = sources_dir / "hn-algolia.yaml"
    source_file.write_text("""
id: hn-algolia
name: Hacker News (Algolia, front page)
type: json_api
config:
  endpoint: https://hn.algolia.com/api/v1/search
  query_params:
    tags: front_page
poll_cadence: daily
signal_type:
  - news
  - capability
audience_tags:
  - hardcore_tech
  - devs_curious_ai
relevance_tags:
  - hn
pre_filter:
  min_engagement: 50
  recency_window_days: 14
  dedup_key: title_url
priority: 1
fragility_tier: stable
staleness_threshold_days: 14
""")
    return source_file
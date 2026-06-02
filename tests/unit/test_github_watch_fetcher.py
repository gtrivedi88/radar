# tests/unit/test_github_watch_fetcher.py
"""Comprehensive test suite for GitHub Watch fetcher"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import json
import os

from radar.adapters.fetchers.github_watch import GitHubWatchFetcher
from radar.core.models import SourceConfig, SourceType


@pytest.fixture
def github_source_config():
    """Base GitHub source configuration for testing"""
    return SourceConfig(
        id="test-github-watch",
        name="Test GitHub Watch",
        type=SourceType.github_watch,
        config={
            "endpoint": "trending_repos",
            "language": "python",
            "since": "daily"
        },
        signal_type=["capability", "trend"],
        audience_tags=["devs_curious_ai", "hardcore_tech"]
    )


@pytest.fixture
def github_user_activity_config():
    """GitHub user activity source configuration"""
    return SourceConfig(
        id="test-user-activity",
        name="Test User Activity",
        type=SourceType.github_watch,
        config={
            "endpoint": "user_activity",
            "username": "octocat"
        },
        signal_type=["activity"],
        audience_tags=["devs_curious_ai"]
    )


@pytest.fixture
def github_releases_config():
    """GitHub releases source configuration"""
    return SourceConfig(
        id="test-releases",
        name="Test Releases",
        type=SourceType.github_watch,
        config={
            "endpoint": "releases",
            "owner": "microsoft",
            "repo": "vscode"
        },
        signal_type=["release"],
        audience_tags=["tech_writer"]
    )


@pytest.fixture
def mock_trending_response():
    """Mock GitHub trending repositories search response"""
    return {
        "total_count": 2,
        "incomplete_results": False,
        "items": [
            {
                "id": 123456,
                "name": "awesome-ai-tool",
                "full_name": "openai/awesome-ai-tool",
                "html_url": "https://github.com/openai/awesome-ai-tool",
                "description": "Revolutionary AI tool for developers",
                "stargazers_count": 15420,
                "watchers_count": 1200,
                "forks_count": 3400,
                "open_issues_count": 45,
                "language": "Python",
                "created_at": "2026-01-15T10:00:00Z",
                "updated_at": "2026-05-30T14:30:00Z",
                "pushed_at": "2026-05-30T12:00:00Z",
                "topics": ["ai", "machine-learning", "python"],
                "license": {"name": "MIT License"},
                "owner": {
                    "login": "openai",
                    "type": "Organization"
                }
            },
            {
                "id": 789101,
                "name": "claude-code-helper",
                "full_name": "anthropic/claude-code-helper",
                "html_url": "https://github.com/anthropic/claude-code-helper",
                "description": "Helper tools for Claude Code development",
                "stargazers_count": 8900,
                "watchers_count": 650,
                "forks_count": 1200,
                "open_issues_count": 12,
                "language": "TypeScript",
                "created_at": "2026-03-01T09:00:00Z",
                "updated_at": "2026-05-29T16:45:00Z",
                "pushed_at": "2026-05-29T15:30:00Z",
                "topics": ["claude", "ai-assistant", "development-tools"],
                "license": {"name": "Apache License 2.0"},
                "owner": {
                    "login": "anthropic",
                    "type": "Organization"
                }
            }
        ]
    }


@pytest.fixture
def mock_user_events_response():
    """Mock GitHub user activity events response"""
    return [
        {
            "id": "event123",
            "type": "PushEvent",
            "actor": {
                "login": "octocat",
                "display_login": "octocat"
            },
            "repo": {
                "name": "octocat/Hello-World",
                "url": "https://api.github.com/repos/octocat/Hello-World"
            },
            "payload": {
                "commits": [
                    {
                        "message": "Add AI integration features",
                        "url": "https://api.github.com/repos/octocat/Hello-World/commits/abc123"
                    }
                ]
            },
            "public": True,
            "created_at": "2026-05-30T10:00:00Z"
        },
        {
            "id": "event456",
            "type": "CreateEvent",
            "actor": {
                "login": "octocat",
                "display_login": "octocat"
            },
            "repo": {
                "name": "octocat/ai-experiment",
                "url": "https://api.github.com/repos/octocat/ai-experiment"
            },
            "payload": {
                "ref": None,
                "ref_type": "repository",
                "description": "Experimenting with new AI APIs"
            },
            "public": True,
            "created_at": "2026-05-29T15:30:00Z"
        }
    ]


@pytest.fixture
def mock_releases_response():
    """Mock GitHub releases response"""
    return [
        {
            "id": 98765,
            "name": "v1.85.0",
            "tag_name": "v1.85.0",
            "html_url": "https://github.com/microsoft/vscode/releases/tag/v1.85.0",
            "body": "## What's New\n\n- Enhanced AI integration\n- Improved performance\n- Bug fixes",
            "prerelease": False,
            "draft": False,
            "created_at": "2026-05-30T10:00:00Z",
            "published_at": "2026-05-30T11:00:00Z",
            "author": {
                "login": "vscode-bot",
                "type": "Bot"
            },
            "assets": [
                {
                    "name": "VSCodeSetup-x64.exe",
                    "download_count": 125000,
                    "size": 89123456
                }
            ]
        },
        {
            "id": 98764,
            "name": "v1.84.2",
            "tag_name": "v1.84.2",
            "html_url": "https://github.com/microsoft/vscode/releases/tag/v1.84.2",
            "body": "Hotfix release:\n- Critical security patch\n- Performance improvements",
            "prerelease": False,
            "draft": False,
            "created_at": "2026-05-25T14:00:00Z",
            "published_at": "2026-05-25T15:00:00Z",
            "author": {
                "login": "vscode-bot",
                "type": "Bot"
            },
            "assets": []
        }
    ]


@pytest.fixture
def mock_rate_limit_headers():
    """Mock GitHub rate limit headers"""
    return {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": str(int(datetime.now(timezone.utc).timestamp()) + 3600),
        "X-RateLimit-Used": "1",
        "X-RateLimit-Resource": "core"
    }


@pytest.mark.asyncio
async def test_github_fetcher_trending_repos(github_source_config, mock_trending_response, mock_rate_limit_headers):
    """Test fetching trending repositories"""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_trending_response
    mock_response.headers = mock_rate_limit_headers
    mock_response.status_code = 200

    async def mock_get(*args, **kwargs):
        mock_response.raise_for_status.return_value = None
        return mock_response

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get

            fetcher = GitHubWatchFetcher(github_source_config)
            items = await fetcher.fetch_items()

    assert len(items) == 2

    # Check first item normalization
    item = items[0]
    assert item['title'] == 'awesome-ai-tool'
    assert item['url'] == 'https://github.com/openai/awesome-ai-tool'
    assert item['source_id'] == 'test-github-watch'
    assert item['metrics']['stars'] == 15420
    assert item['metrics']['forks'] == 3400
    assert item['metrics']['open_issues'] == 45
    assert 'item_id' in item
    assert 'fetched_at' in item


@pytest.mark.asyncio
async def test_github_fetcher_user_activity(github_user_activity_config, mock_user_events_response, mock_rate_limit_headers):
    """Test fetching user activity events"""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_user_events_response
    mock_response.headers = mock_rate_limit_headers
    mock_response.status_code = 200

    async def mock_get(*args, **kwargs):
        mock_response.raise_for_status.return_value = None
        return mock_response

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get

            fetcher = GitHubWatchFetcher(github_user_activity_config)
            items = await fetcher.fetch_items()

    assert len(items) == 2

    # Check event normalization
    push_event = items[0]
    assert push_event['title'] == 'PushEvent: octocat/Hello-World'
    assert push_event['url'] == 'https://github.com/octocat/Hello-World'
    assert 'Add AI integration features' in push_event['raw_text']

    create_event = items[1]
    assert create_event['title'] == 'CreateEvent: octocat/ai-experiment'
    assert create_event['url'] == 'https://github.com/octocat/ai-experiment'


@pytest.mark.asyncio
async def test_github_fetcher_releases(github_releases_config, mock_releases_response, mock_rate_limit_headers):
    """Test fetching repository releases"""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_releases_response
    mock_response.headers = mock_rate_limit_headers
    mock_response.status_code = 200

    async def mock_get(*args, **kwargs):
        mock_response.raise_for_status.return_value = None
        return mock_response

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get

            fetcher = GitHubWatchFetcher(github_releases_config)
            items = await fetcher.fetch_items()

    assert len(items) == 2

    # Check release normalization
    release = items[0]
    assert release['title'] == 'Release: v1.85.0'
    assert release['url'] == 'https://github.com/microsoft/vscode/releases/tag/v1.85.0'
    assert 'Enhanced AI integration' in release['raw_text']
    assert release['metrics']['downloads'] == 125000


@pytest.mark.asyncio
async def test_github_fetcher_missing_endpoint():
    """Test validation for missing endpoint config"""
    config = SourceConfig(
        id="test-invalid",
        name="Test Invalid GitHub",
        type=SourceType.github_watch,
        config={},  # Missing endpoint
        signal_type=["test"],
        audience_tags=["test"]
    )

    fetcher = GitHubWatchFetcher(config)

    with pytest.raises(ValueError, match="missing required 'endpoint' config"):
        await fetcher.fetch_items()


@pytest.mark.asyncio
async def test_github_fetcher_invalid_endpoint():
    """Test validation for invalid endpoint"""
    config = SourceConfig(
        id="test-invalid",
        name="Test Invalid GitHub",
        type=SourceType.github_watch,
        config={"endpoint": "invalid_type"},
        signal_type=["test"],
        audience_tags=["test"]
    )

    fetcher = GitHubWatchFetcher(config)

    with pytest.raises(ValueError, match="invalid endpoint"):
        await fetcher.fetch_items()


@pytest.mark.asyncio
async def test_github_fetcher_missing_required_params():
    """Test validation for missing required parameters per endpoint type"""
    # Test missing username for user_activity
    config = SourceConfig(
        id="test-invalid",
        name="Test Invalid",
        type=SourceType.github_watch,
        config={"endpoint": "user_activity"},  # Missing username
        signal_type=["test"],
        audience_tags=["test"]
    )

    fetcher = GitHubWatchFetcher(config)
    with pytest.raises(ValueError, match="missing required 'username'"):
        await fetcher.fetch_items()

    # Test missing owner/repo for releases
    config.config = {"endpoint": "releases", "owner": "test"}  # Missing repo
    fetcher = GitHubWatchFetcher(config)
    with pytest.raises(ValueError, match="missing required 'repo'"):
        await fetcher.fetch_items()


@pytest.mark.asyncio
async def test_github_fetcher_unauthenticated_fallback(github_source_config, mock_trending_response, mock_rate_limit_headers):
    """Test graceful fallback when GitHub token is missing"""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_trending_response
    mock_response.headers = {**mock_rate_limit_headers, "X-RateLimit-Limit": "60"}  # Unauthenticated limit
    mock_response.status_code = 200

    async def mock_get(*args, **kwargs):
        # Verify no Authorization header when token is missing
        assert 'headers' not in kwargs or 'Authorization' not in kwargs.get('headers', {})
        mock_response.raise_for_status.return_value = None
        return mock_response

    with patch.dict(os.environ, {}, clear=True):  # Clear GITHUB_TOKEN
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get

            fetcher = GitHubWatchFetcher(github_source_config)
            items = await fetcher.fetch_items()

    assert len(items) == 2


@pytest.mark.asyncio
async def test_github_fetcher_rate_limit_429_error(github_source_config):
    """Test handling of rate limit exceeded (429) responses"""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {"X-RateLimit-Reset": str(int(datetime.now(timezone.utc).timestamp()) + 3600)}

    def mock_raise_for_status():
        raise httpx.HTTPStatusError("Rate limit exceeded", request=MagicMock(), response=mock_response)

    mock_response.raise_for_status = mock_raise_for_status

    async def mock_get(*args, **kwargs):
        return mock_response

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get

            fetcher = GitHubWatchFetcher(github_source_config)

            with pytest.raises(httpx.HTTPStatusError, match="Rate limit exceeded"):
                await fetcher.fetch_items()


@pytest.mark.asyncio
async def test_github_fetcher_network_retry_logic(github_source_config, mock_trending_response, mock_rate_limit_headers):
    """Test retry logic for network failures"""
    call_count = 0

    async def mock_get_with_failure(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ConnectError("Network error")

        mock_response = MagicMock()
        mock_response.json.return_value = mock_trending_response
        mock_response.headers = mock_rate_limit_headers
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        return mock_response

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get_with_failure

            fetcher = GitHubWatchFetcher(github_source_config)
            items = await fetcher.fetch_items()

    assert len(items) == 2
    assert call_count == 2  # Should have retried once


@pytest.mark.asyncio
async def test_github_fetcher_max_retries_exceeded(github_source_config):
    """Test failure after maximum retries exceeded"""
    async def mock_get_always_fail(*args, **kwargs):
        raise httpx.ConnectError("Persistent network error")

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get_always_fail

            fetcher = GitHubWatchFetcher(github_source_config)

            with pytest.raises(httpx.ConnectError, match="Persistent network error"):
                await fetcher.fetch_items()


@pytest.mark.asyncio
async def test_github_fetcher_invalid_json_response(github_source_config, mock_rate_limit_headers):
    """Test handling of invalid JSON responses"""
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
    mock_response.headers = mock_rate_limit_headers
    mock_response.status_code = 200
    mock_response.text = "Invalid JSON content"

    async def mock_get(*args, **kwargs):
        mock_response.raise_for_status.return_value = None
        return mock_response

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get

            fetcher = GitHubWatchFetcher(github_source_config)

            with pytest.raises(ValueError, match="Invalid JSON response"):
                await fetcher.fetch_items()


@pytest.mark.asyncio
async def test_github_fetcher_empty_response(github_source_config, mock_rate_limit_headers):
    """Test handling of empty API responses"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}  # Empty trending response
    mock_response.headers = mock_rate_limit_headers
    mock_response.status_code = 200

    async def mock_get(*args, **kwargs):
        mock_response.raise_for_status.return_value = None
        return mock_response

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get

            fetcher = GitHubWatchFetcher(github_source_config)
            items = await fetcher.fetch_items()

    assert len(items) == 0


def test_github_fetcher_url_validation():
    """Test URL validation for security"""
    from radar.adapters.fetchers.github_watch import GitHubWatchFetcher

    # Valid GitHub URLs
    assert GitHubWatchFetcher._validate_github_url("https://github.com/owner/repo")
    assert GitHubWatchFetcher._validate_github_url("https://api.github.com/repos/owner/repo")

    # Invalid URLs
    assert not GitHubWatchFetcher._validate_github_url("javascript:alert('xss')")
    assert not GitHubWatchFetcher._validate_github_url("http://evil-site.com/github")
    assert not GitHubWatchFetcher._validate_github_url("ftp://github.com/file")
    assert not GitHubWatchFetcher._validate_github_url("")
    assert not GitHubWatchFetcher._validate_github_url(None)


def test_github_fetcher_id_generation():
    """Test stable ID generation for different item types"""
    from radar.adapters.fetchers.github_watch import GitHubWatchFetcher

    # Test repository ID
    repo_data = {
        "full_name": "owner/repo",
        "html_url": "https://github.com/owner/repo"
    }
    id1 = GitHubWatchFetcher._generate_item_id("repo", repo_data)
    id2 = GitHubWatchFetcher._generate_item_id("repo", repo_data)
    assert id1 == id2  # Should be stable
    assert len(id1) == 40  # SHA-1 hex digest length

    # Test event ID
    event_data = {
        "id": "event123",
        "type": "PushEvent",
        "created_at": "2026-05-30T10:00:00Z"
    }
    event_id = GitHubWatchFetcher._generate_item_id("event", event_data)
    assert len(event_id) == 40

    # Test release ID
    release_data = {
        "tag_name": "v1.0.0",
        "html_url": "https://github.com/owner/repo/releases/tag/v1.0.0"
    }
    release_id = GitHubWatchFetcher._generate_item_id("release", release_data)
    assert len(release_id) == 40


def test_github_fetcher_rate_limit_parsing():
    """Test rate limit information parsing"""
    from radar.adapters.fetchers.github_watch import GitHubWatchFetcher

    headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": "1234567890",
        "X-RateLimit-Used": "1"
    }

    rate_info = GitHubWatchFetcher._parse_rate_limit_info(headers)
    assert rate_info["limit"] == 5000
    assert rate_info["remaining"] == 4999
    assert rate_info["reset_timestamp"] == 1234567890
    assert rate_info["used"] == 1

    # Test missing headers
    empty_rate_info = GitHubWatchFetcher._parse_rate_limit_info({})
    assert empty_rate_info["limit"] == 0
    assert empty_rate_info["remaining"] == 0


def test_github_fetcher_registration():
    """Test fetcher auto-registration with registry"""
    from radar.adapters.fetchers.registry import FetcherRegistry
    from radar.core.models import SourceType

    # Create test config
    config = SourceConfig(
        id="test-github",
        name="Test GitHub",
        type=SourceType.github_watch,
        config={"endpoint": "trending_repos"},
        signal_type=["test"],
        audience_tags=["test"]
    )

    fetcher_class = FetcherRegistry.get_fetcher(config)
    assert fetcher_class is not None
    assert fetcher_class.__name__ == "GitHubWatchFetcher"
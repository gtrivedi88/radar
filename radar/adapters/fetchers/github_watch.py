# radar/adapters/fetchers/github_watch.py
"""GitHub Watch API fetcher implementation with comprehensive monitoring capabilities"""

import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import asyncio
import json

import httpx

from radar.core.models import SourceConfig
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class GitHubWatchFetcher(BaseFetcher):
    """Production-ready GitHub API fetcher for trending repositories, user activity, and releases monitoring

    Features:
    - Multiple endpoint types: trending_repos, user_activity, releases
    - Rate limit awareness and respect for GitHub API limits
    - Authentication with GitHub token (with graceful fallback)
    - Retry logic with exponential backoff
    - Comprehensive error handling and validation
    - Security-focused URL validation
    - Efficient resource management
    """

    # GitHub API base URLs
    API_BASE_URL = "https://api.github.com"
    SEARCH_BASE_URL = "https://api.github.com/search"

    # Supported endpoint types
    SUPPORTED_ENDPOINTS = {
        "trending_repos": "search/repositories",
        "user_activity": "users/{username}/events",
        "releases": "repos/{owner}/{repo}/releases"
    }

    # Rate limiting constants
    AUTHENTICATED_RATE_LIMIT = 5000  # per hour
    UNAUTHENTICATED_RATE_LIMIT = 60  # per hour
    DEFAULT_RETRY_ATTEMPTS = 3
    RETRY_BACKOFF_BASE = 2

    def __init__(self, source_config: SourceConfig, transport: Optional[httpx.BaseTransport] = None):
        super().__init__(source_config)
        self._transport = transport
        self._github_token = os.getenv("GITHUB_TOKEN")

        # Setup headers for authentication if token is available
        self._default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Radar-Intelligence-System/1.0"
        }

        if self._github_token:
            self._default_headers["Authorization"] = f"Bearer {self._github_token}"
            logger.debug("GitHub fetcher initialized with authentication token")
        else:
            logger.info("GitHub fetcher initialized without authentication (rate limits will be lower)")

    async def fetch_items(self) -> List[Dict[str, Any]]:
        """Fetch items from GitHub API with comprehensive error handling and retry logic"""
        config = self.source_config.config
        endpoint = config.get("endpoint")

        # Validate endpoint type
        if not endpoint:
            raise ValueError(f"GitHub source {self.source_config.id} missing required 'endpoint' config")

        if endpoint not in self.SUPPORTED_ENDPOINTS:
            raise ValueError(f"GitHub source {self.source_config.id} has invalid endpoint: {endpoint}. "
                           f"Supported types: {list(self.SUPPORTED_ENDPOINTS.keys())}")

        logger.info(f"Fetching GitHub {endpoint} for source {self.source_config.id}")

        # Build request URL and parameters based on endpoint type
        url, params = self._build_request_params(endpoint, config)

        # Fetch data with retry logic
        try:
            data = await self._fetch_with_retry(url, params)
            fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Process and normalize data based on endpoint type
            items = self._process_response_data(data, endpoint, fetched_at)

            logger.info(f"Successfully fetched and normalized {len(items)} items from GitHub {endpoint}")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch GitHub {endpoint}: {e}")
            raise

    def _build_request_params(self, endpoint: str, config: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Build request URL and parameters for different endpoint types"""
        params = {}

        if endpoint == "trending_repos":
            url = f"{self.SEARCH_BASE_URL}/repositories"

            # Build search query for trending repositories
            query_parts = []

            # Language filter
            if "language" in config:
                query_parts.append(f"language:{config['language']}")

            # Date range for trending
            since = config.get("since", "daily")
            if since == "daily":
                query_parts.append("created:>2026-05-30")  # Last day
            elif since == "weekly":
                query_parts.append("created:>2026-05-24")  # Last week
            elif since == "monthly":
                query_parts.append("created:>2026-05-01")  # Last month

            # Stars threshold for quality
            min_stars = config.get("min_stars", 100)
            if min_stars > 0:
                query_parts.append(f"stars:>{min_stars}")

            # Additional filters
            if config.get("topic"):
                query_parts.append(f"topic:{config['topic']}")

            params["q"] = " ".join(query_parts) if query_parts else "stars:>100"
            params["sort"] = config.get("sort", "stars")
            params["order"] = config.get("order", "desc")
            params["per_page"] = min(config.get("limit", 30), 100)  # GitHub max is 100

        elif endpoint == "user_activity":
            username = config.get("username")
            if not username:
                raise ValueError(f"GitHub user_activity source {self.source_config.id} missing required 'username' config")

            url = f"{self.API_BASE_URL}/users/{username}/events"
            params["per_page"] = min(config.get("limit", 30), 100)

        elif endpoint == "releases":
            owner = config.get("owner")
            repo = config.get("repo")

            if not owner:
                raise ValueError(f"GitHub releases source {self.source_config.id} missing required 'owner' config")
            if not repo:
                raise ValueError(f"GitHub releases source {self.source_config.id} missing required 'repo' config")

            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/releases"
            params["per_page"] = min(config.get("limit", 30), 100)

        return url, params

    async def _fetch_with_retry(self, url: str, params: Dict[str, Any]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetch data from GitHub API with exponential backoff retry logic"""
        last_exception = None

        for attempt in range(self.DEFAULT_RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(
                    transport=self._transport,
                    timeout=30.0,
                    headers=self._default_headers
                ) as client:

                    logger.debug(f"GitHub API request (attempt {attempt + 1}): {url}")
                    response = await client.get(url, params=params)

                    # Handle rate limiting
                    if response.status_code == 429:
                        rate_info = self._parse_rate_limit_info(response.headers)
                        reset_time = datetime.fromtimestamp(rate_info["reset_timestamp"], timezone.utc)
                        logger.warning(f"GitHub rate limit exceeded. Resets at: {reset_time}")
                        response.raise_for_status()  # Will raise HTTPStatusError

                    response.raise_for_status()

                    # Log rate limit information for monitoring
                    rate_info = self._parse_rate_limit_info(response.headers)
                    logger.debug(f"GitHub rate limit: {rate_info['remaining']}/{rate_info['limit']} remaining")

                    # Parse JSON response
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response from GitHub API: {e}")
                        logger.debug(f"Response content: {response.text[:500]}")
                        raise ValueError(f"Invalid JSON response from GitHub API: {e}")

                    return data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit - don't retry immediately
                    last_exception = e
                    break
                elif e.response.status_code in (500, 502, 503, 504):
                    # Server errors - retry with backoff
                    last_exception = e
                    if attempt < self.DEFAULT_RETRY_ATTEMPTS - 1:
                        wait_time = self.RETRY_BACKOFF_BASE ** attempt
                        logger.warning(f"GitHub API server error (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    # Client errors - don't retry
                    logger.error(f"GitHub API client error: {e}")
                    raise

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                # Network errors - retry with backoff
                last_exception = e
                if attempt < self.DEFAULT_RETRY_ATTEMPTS - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"GitHub API network error (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue

            except Exception as e:
                # Other errors - don't retry
                logger.error(f"Unexpected error during GitHub API request: {e}")
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("All retry attempts failed with no recorded exception")

    def _process_response_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]],
                             endpoint: str, fetched_at: str) -> List[Dict[str, Any]]:
        """Process and normalize response data based on endpoint type"""
        items = []

        if endpoint == "trending_repos":
            # Search API returns data with 'items' field
            repos = data.get("items", []) if isinstance(data, dict) else []
            for repo in repos:
                try:
                    item = self._normalize_repository_item(repo, fetched_at)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to normalize repository {repo.get('full_name', 'unknown')}: {e}")
                    continue

        elif endpoint == "user_activity":
            # Events API returns array directly
            events = data if isinstance(data, list) else []
            for event in events:
                try:
                    item = self._normalize_event_item(event, fetched_at)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to normalize event {event.get('id', 'unknown')}: {e}")
                    continue

        elif endpoint == "releases":
            # Releases API returns array directly
            releases = data if isinstance(data, list) else []
            for release in releases:
                try:
                    item = self._normalize_release_item(release, fetched_at)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to normalize release {release.get('tag_name', 'unknown')}: {e}")
                    continue

        return items

    def _normalize_repository_item(self, repo: Dict[str, Any], fetched_at: str) -> Optional[Dict[str, Any]]:
        """Normalize repository data to canonical format"""
        name = repo.get("name", "").strip()
        full_name = repo.get("full_name", "").strip()
        url = repo.get("html_url", "")

        if not name or not url or not self._validate_github_url(url):
            return None

        # Generate stable item ID
        item_id = self._generate_item_id("repo", repo)

        # Extract description with fallback
        description = repo.get("description") or ""
        if description:
            description = re.sub(r'\s+', ' ', description).strip()[:500]

        # Build raw text content
        topics = repo.get("topics", [])
        language = repo.get("language") or "Unknown"
        owner_type = repo.get("owner", {}).get("type", "User")
        license_name = repo.get("license", {}).get("name") if repo.get("license") else "None"

        raw_text_parts = [
            f"Repository: {full_name}",
            f"Description: {description}" if description else "",
            f"Language: {language}",
            f"Owner: {owner_type}",
            f"License: {license_name}",
            f"Topics: {', '.join(topics)}" if topics else ""
        ]
        raw_text = "\n".join(part for part in raw_text_parts if part)

        return {
            "item_id": item_id,
            "title": name,
            "url": url,
            "source_id": self.source_config.id,
            "signal_type": list(self.source_config.signal_type),
            "audience_tags": list(self.source_config.audience_tags),
            "timestamp": repo.get("updated_at") or repo.get("created_at") or fetched_at,
            "raw_text": raw_text[:2000],
            "metrics": {
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "watchers": repo.get("watchers_count", 0),
                "open_issues": repo.get("open_issues_count", 0)
            },
            "relevance_tags": list(self.source_config.relevance_tags),
            "fetched_at": fetched_at,
            "dedup_key": item_id,
        }

    def _normalize_event_item(self, event: Dict[str, Any], fetched_at: str) -> Optional[Dict[str, Any]]:
        """Normalize user activity event data to canonical format"""
        event_type = event.get("type", "")
        repo_name = event.get("repo", {}).get("name", "")
        actor = event.get("actor", {}).get("login", "")

        if not event_type or not repo_name:
            return None

        # Generate title based on event type
        title = f"{event_type}: {repo_name}"

        # Build GitHub URL for the repository
        url = f"https://github.com/{repo_name}"
        if not self._validate_github_url(url):
            return None

        # Generate stable item ID
        item_id = self._generate_item_id("event", event)

        # Extract meaningful content from payload
        payload = event.get("payload", {})
        raw_text_parts = [f"Event: {event_type} by {actor}"]

        if event_type == "PushEvent":
            commits = payload.get("commits", [])
            if commits:
                messages = [commit.get("message", "") for commit in commits[:3]]  # First 3 commits
                raw_text_parts.append(f"Commits: {'; '.join(messages)}")
        elif event_type == "CreateEvent":
            ref_type = payload.get("ref_type", "")
            description = payload.get("description", "")
            raw_text_parts.append(f"Created {ref_type}: {description}")
        elif event_type == "IssuesEvent":
            action = payload.get("action", "")
            issue_title = payload.get("issue", {}).get("title", "")
            raw_text_parts.append(f"Issue {action}: {issue_title}")
        elif event_type == "PullRequestEvent":
            action = payload.get("action", "")
            pr_title = payload.get("pull_request", {}).get("title", "")
            raw_text_parts.append(f"PR {action}: {pr_title}")

        raw_text = "\n".join(raw_text_parts)

        return {
            "item_id": item_id,
            "title": title,
            "url": url,
            "source_id": self.source_config.id,
            "signal_type": list(self.source_config.signal_type),
            "audience_tags": list(self.source_config.audience_tags),
            "timestamp": event.get("created_at", fetched_at),
            "raw_text": raw_text[:2000],
            "metrics": {"score": 0, "comments": 0, "stars": None},
            "relevance_tags": list(self.source_config.relevance_tags),
            "fetched_at": fetched_at,
            "dedup_key": item_id,
        }

    def _normalize_release_item(self, release: Dict[str, Any], fetched_at: str) -> Optional[Dict[str, Any]]:
        """Normalize release data to canonical format"""
        tag_name = release.get("tag_name", "").strip()
        name = release.get("name", tag_name).strip()
        url = release.get("html_url", "")

        if not tag_name or not url or not self._validate_github_url(url):
            return None

        # Skip drafts and prereleases unless explicitly configured
        if release.get("draft", False) or release.get("prerelease", False):
            config = self.source_config.config
            if not config.get("include_drafts", False) and release.get("draft"):
                return None
            if not config.get("include_prereleases", False) and release.get("prerelease"):
                return None

        # Generate stable item ID
        item_id = self._generate_item_id("release", release)

        # Build title
        title = f"Release: {name or tag_name}"

        # Extract release notes content
        body = release.get("body") or ""
        if body:
            # Clean up markdown and limit length
            body = re.sub(r'```[^`]*```', '[code block]', body)  # Remove code blocks
            body = re.sub(r'!\[[^\]]*\]\([^)]*\)', '[image]', body)  # Remove images
            body = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', body)  # Convert links to text
            body = re.sub(r'[#*`_]+', '', body)  # Remove markdown formatting
            body = re.sub(r'\s+', ' ', body).strip()[:1000]

        # Calculate download metrics
        assets = release.get("assets", [])
        total_downloads = sum(asset.get("download_count", 0) for asset in assets)

        # Build raw text content
        author = release.get("author", {}).get("login", "Unknown")
        published_at = release.get("published_at", "")

        raw_text_parts = [
            f"Release: {tag_name}",
            f"Author: {author}",
            f"Published: {published_at}",
            f"Assets: {len(assets)} files",
            f"Downloads: {total_downloads}",
            body if body else ""
        ]
        raw_text = "\n".join(part for part in raw_text_parts if part)

        return {
            "item_id": item_id,
            "title": title,
            "url": url,
            "source_id": self.source_config.id,
            "signal_type": list(self.source_config.signal_type),
            "audience_tags": list(self.source_config.audience_tags),
            "timestamp": release.get("published_at") or release.get("created_at") or fetched_at,
            "raw_text": raw_text[:2000],
            "metrics": {
                "downloads": total_downloads,
                "assets": len(assets),
                "is_prerelease": release.get("prerelease", False)
            },
            "relevance_tags": list(self.source_config.relevance_tags),
            "fetched_at": fetched_at,
            "dedup_key": item_id,
        }

    @staticmethod
    def _validate_github_url(url: str) -> bool:
        """Validate GitHub URLs for security"""
        if not url or not isinstance(url, str):
            return False

        # Must be HTTPS
        if not url.startswith("https://"):
            return False

        # Must be GitHub domain
        github_domains = ["github.com", "api.github.com", "raw.githubusercontent.com"]
        return any(domain in url for domain in github_domains)

    @staticmethod
    def _generate_item_id(item_type: str, data: Dict[str, Any]) -> str:
        """Generate stable SHA-1 hash for item identification"""
        if item_type == "repo":
            # Use full_name + html_url for repositories
            identifier = f"{data.get('full_name', '')}:{data.get('html_url', '')}"
        elif item_type == "event":
            # Use event id + type + created_at for events
            identifier = f"{data.get('id', '')}:{data.get('type', '')}:{data.get('created_at', '')}"
        elif item_type == "release":
            # Use tag_name + html_url for releases
            identifier = f"{data.get('tag_name', '')}:{data.get('html_url', '')}"
        else:
            # Fallback to JSON representation
            identifier = str(data)

        return hashlib.sha1(identifier.encode('utf-8')).hexdigest()

    @staticmethod
    def _parse_rate_limit_info(headers: Dict[str, str]) -> Dict[str, int]:
        """Parse GitHub rate limit information from response headers"""
        return {
            "limit": int(headers.get("X-RateLimit-Limit", 0)),
            "remaining": int(headers.get("X-RateLimit-Remaining", 0)),
            "reset_timestamp": int(headers.get("X-RateLimit-Reset", 0)),
            "used": int(headers.get("X-RateLimit-Used", 0))
        }


# Register with fetcher registry
from .registry import FetcherRegistry
from radar.core.models import SourceType

FetcherRegistry.register_fetcher(SourceType.github_watch, GitHubWatchFetcher)
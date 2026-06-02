"""Pluggable fetcher system"""

from .base import BaseFetcher
from .registry import FetcherRegistry

# Import fetcher implementations to trigger registration
from . import json_api
from . import rss
from . import github_watch
from . import scrape

__all__ = [
    "BaseFetcher",
    "FetcherRegistry",
]
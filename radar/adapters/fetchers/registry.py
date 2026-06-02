"""Fetcher auto-discovery registry"""

from typing import Type, Dict, Optional
import logging

from radar.core.models import SourceConfig, SourceType
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class FetcherRegistry:
    """Auto-discovers and manages fetcher implementations"""

    _fetchers: Dict[str, Type[BaseFetcher]] = {}

    @classmethod
    def register_fetcher(cls, source_type: SourceType, fetcher_class: Type[BaseFetcher]) -> None:
        """Register a fetcher for a source type"""
        cls._fetchers[source_type.value] = fetcher_class
        logger.debug(f"Registered fetcher {fetcher_class.__name__} for type {source_type.value}")

    @classmethod
    def get_fetcher(cls, source_config: SourceConfig) -> Optional[Type[BaseFetcher]]:
        """Get fetcher class for a source configuration"""
        fetcher_class = cls._fetchers.get(source_config.type.value)
        if not fetcher_class:
            logger.warning(f"No fetcher registered for source type: {source_config.type.value}")
        return fetcher_class

    @classmethod
    def list_registered_types(cls) -> list[str]:
        """List all registered source types"""
        return list(cls._fetchers.keys())

    @classmethod
    def create_fetcher(cls, source_config: SourceConfig) -> Optional[BaseFetcher]:
        """Create fetcher instance for a source configuration"""
        fetcher_class = cls.get_fetcher(source_config)
        if fetcher_class:
            return fetcher_class(source_config)
        return None
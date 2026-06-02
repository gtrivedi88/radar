"""Base fetcher interface"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from radar.core.models import SourceConfig


class BaseFetcher(ABC):
    """Abstract base class for all source fetchers"""

    def __init__(self, source_config: SourceConfig):
        self.source_config = source_config

    @abstractmethod
    async def fetch_items(self) -> List[Dict[str, Any]]:
        """Fetch items from the source and return in canonical format"""
        pass

    def get_source_id(self) -> str:
        """Get the source ID"""
        return self.source_config.id

    def get_source_type(self) -> str:
        """Get the source type"""
        return self.source_config.type.value
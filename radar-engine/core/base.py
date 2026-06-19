"""Core data types for Radar Engine"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import httpx


@dataclass
class IntelligenceItem:
    """A single piece of intelligence from any source"""
    title: str
    url: str
    score: int
    comments: int
    timestamp: str
    source_id: str
    content: str = ""


class BaseFetcher(ABC):
    """Base class for intelligence fetchers"""

    def __init__(self, config: Dict[str, Any], http_client: httpx.AsyncClient):
        self.config = config
        self.client = http_client

    @abstractmethod
    async def fetch(self) -> List[IntelligenceItem]:
        pass

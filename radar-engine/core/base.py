"""
Core abstractions for Radar Engine
Simplified and focused on our strategic intelligence use case
"""

from abc import ABC, abstractmethod
from datetime import datetime
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
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseFetcher(ABC):
    """Base class for all intelligence fetchers"""

    def __init__(self, config: Dict[str, Any], http_client: httpx.AsyncClient):
        self.config = config
        self.client = http_client

    @abstractmethod
    async def fetch(self) -> List[IntelligenceItem]:
        """Fetch intelligence items from this source"""
        pass

    def generate_id(self, native_id: str) -> str:
        """Generate unique ID for this source"""
        return f"{self.config['id']}:{native_id}"


class AutonomousLoop:
    """Represents a running autonomous intelligence loop"""

    def __init__(self, prompt: str, frequency: str, threshold_callback=None):
        self.prompt = prompt
        self.frequency = frequency  # "2d", "1w", etc.
        self.threshold_callback = threshold_callback
        self.last_run: datetime = None
        self.active = True

    def should_run(self) -> bool:
        """Check if this loop should run now"""
        if not self.active or not self.last_run:
            return True

        # Parse frequency and check timing
        # Implementation depends on frequency parsing
        return False


class StrategicHook:
    """Represents a threshold-triggered strategic hook"""

    def __init__(self, condition: str, action: str, description: str):
        self.condition = condition
        self.action = action
        self.description = description
        self.triggered_count = 0

    def check_condition(self, data: Dict[str, Any]) -> bool:
        """Check if this hook's condition is met"""
        # This would evaluate the condition string against data
        # For now, simplified
        return False
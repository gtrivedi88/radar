"""
Core abstractions for Radar Engine
Simplified and focused on our strategic intelligence use case
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Union
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
        if not self.active:
            return False

        if not self.last_run:
            return True

        # Parse frequency and check timing
        import re
        from datetime import timedelta

        match = re.match(r'(\d+)([mhdw])', self.frequency.lower())
        if not match:
            # Invalid frequency format, default to not running
            return False

        amount, unit = int(match.group(1)), match.group(2)

        if unit == 'm':
            delta = timedelta(minutes=amount)
        elif unit == 'h':
            delta = timedelta(hours=amount)
        elif unit == 'd':
            delta = timedelta(days=amount)
        elif unit == 'w':
            delta = timedelta(weeks=amount)
        else:
            return False

        # Check if enough time has passed since last run
        return datetime.now() >= (self.last_run + delta)


class StrategicHook:
    """Represents a threshold-triggered strategic hook"""

    def __init__(self, condition: str, action: str, description: str):
        self.condition = condition
        self.action = action
        self.description = description
        self.triggered_count = 0

    def check_condition(self, data: Dict[str, Any]) -> bool:
        """Check if this hook's condition is met"""
        condition = self.condition.strip()

        if self._is_contains_condition(condition):
            return self._check_contains_condition(condition, data)
        elif self._is_numeric_condition(condition):
            return self._check_numeric_condition(condition, data)
        else:
            return False

    def _is_contains_condition(self, condition: str) -> bool:
        """Check if condition is a contains-type condition"""
        import re
        return bool(re.search(r'contains\s+[\'"]([^\'"]+)[\'"]', condition, re.IGNORECASE))

    def _is_numeric_condition(self, condition: str) -> bool:
        """Check if condition is a numeric comparison condition"""
        import re
        return bool(re.search(r'(\w+)\s*([><=!]+)\s*(\d+(?:\.\d+)?)', condition))

    def _check_contains_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Check contains-type conditions"""
        import re

        contains_match = re.search(r'contains\s+[\'"]([^\'"]+)[\'"]', condition, re.IGNORECASE)
        if not contains_match:
            return False

        keyword = contains_match.group(1).lower()
        return self._search_keyword_in_data(keyword, data)

    def _search_keyword_in_data(self, keyword: str, data: Dict[str, Any]) -> bool:
        """Search for keyword in data structure recursively"""
        for value in data.values():
            if self._keyword_found_in_value(keyword, value):
                return True
        return False

    def _keyword_found_in_value(self, keyword: str, value: Any) -> bool:
        """Check if keyword is found in a single value"""
        if isinstance(value, str):
            return keyword in value.lower()
        elif isinstance(value, list):
            return self._keyword_found_in_list(keyword, value)
        elif isinstance(value, dict):
            return self._keyword_found_in_dict(keyword, value)
        return False

    def _keyword_found_in_list(self, keyword: str, items: List[Any]) -> bool:
        """Check if keyword is found in any list item"""
        for item in items:
            if self._keyword_found_in_value(keyword, item):
                return True
        return False

    def _keyword_found_in_dict(self, keyword: str, data_dict: Dict[str, Any]) -> bool:
        """Check if keyword is found in any dict value"""
        for sub_value in data_dict.values():
            if isinstance(sub_value, str) and keyword in sub_value.lower():
                return True
        return False

    def _check_numeric_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Check numeric comparison conditions"""
        import re

        match = re.search(r'(\w+)\s*([><=!]+)\s*(\d+(?:\.\d+)?)', condition)
        if not match:
            return False

        field, operator, value_str = match.groups()
        field_value = data.get(field)

        if field_value is None:
            return False

        try:
            target_value = float(value_str)
            field_value = float(field_value)
        except (ValueError, TypeError):
            return False

        return self._apply_numeric_operator(field_value, operator, target_value)

    def _apply_numeric_operator(self, field_value: float, operator: str, target_value: float) -> bool:
        """Apply numeric comparison operator"""
        operators_map = {
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '=': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '!': lambda x, y: x != y,
        }

        operation = operators_map.get(operator)
        if operation:
            return operation(field_value, target_value)
        return False
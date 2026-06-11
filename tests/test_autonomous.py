"""
Tests for autonomous system components
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add radar-engine to path for imports
radar_engine_path = os.path.join(os.path.dirname(__file__), '..', 'radar-engine')
sys.path.insert(0, radar_engine_path)

# Fix imports to work with module structure
try:
    from radar_engine.core.base import AutonomousLoop, StrategicHook, IntelligenceItem
    from radar_engine.orchestration.autonomous import AutonomousOrchestrator
except ImportError:
    # Fallback to direct imports with corrected relative imports
    import importlib.util

    # Import base module
    base_spec = importlib.util.spec_from_file_location(
        "radar_engine.core.base",
        os.path.join(radar_engine_path, "core", "base.py")
    )
    base_module = importlib.util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base_module)

    AutonomousLoop = base_module.AutonomousLoop
    StrategicHook = base_module.StrategicHook
    IntelligenceItem = base_module.IntelligenceItem

    # Import orchestrator module - will need base imports fixed first
    # For now, we'll test just the base classes


class TestAutonomousLoop:
    """Test AutonomousLoop functionality"""

    def test_init(self):
        """Test AutonomousLoop initialization"""
        loop = AutonomousLoop("test prompt", "2d")
        assert loop.prompt == "test prompt"
        assert loop.frequency == "2d"
        assert loop.last_run is None
        assert loop.active is True

    def test_should_run_no_last_run(self):
        """Test should_run returns True when no last_run set"""
        loop = AutonomousLoop("test", "1d")
        result = loop.should_run()
        # Currently returns True for no last_run - this is correct behavior
        assert result is True

    def test_should_run_inactive_loop(self):
        """Test should_run returns False for inactive loop"""
        loop = AutonomousLoop("test", "1d")
        loop.active = False
        result = loop.should_run()
        # Fixed: inactive loops should return False
        assert result is False

    def test_should_run_with_frequency_parsing(self):
        """Test should_run with proper frequency parsing"""
        from datetime import datetime, timedelta

        loop = AutonomousLoop("test", "2h")

        # Set last_run to 1 hour ago (should not run yet - needs 2 hours)
        loop.last_run = datetime.now() - timedelta(hours=1)
        result = loop.should_run()
        assert result is False

        # Set last_run to 3 hours ago (should run now - exceeds 2 hours)
        loop.last_run = datetime.now() - timedelta(hours=3)
        result = loop.should_run()
        assert result is True

    def test_should_run_frequency_formats(self):
        """Test various frequency format parsing"""
        from datetime import datetime, timedelta

        test_cases = [
            ("30m", timedelta(minutes=30), timedelta(minutes=20), False),
            ("30m", timedelta(minutes=30), timedelta(minutes=40), True),
            ("2h", timedelta(hours=2), timedelta(hours=1), False),
            ("2h", timedelta(hours=2), timedelta(hours=3), True),
            ("1d", timedelta(days=1), timedelta(hours=12), False),
            ("1d", timedelta(days=1), timedelta(days=2), True),
            ("1w", timedelta(weeks=1), timedelta(days=3), False),
            ("1w", timedelta(weeks=1), timedelta(days=10), True),
        ]

        for frequency, expected_delta, time_ago, should_run_expected in test_cases:
            loop = AutonomousLoop("test", frequency)
            loop.last_run = datetime.now() - time_ago
            result = loop.should_run()
            assert result is should_run_expected, f"Failed for {frequency} with {time_ago} ago"

    def test_should_run_invalid_frequency(self):
        """Test should_run with invalid frequency format"""
        from datetime import datetime, timedelta

        loop = AutonomousLoop("test", "invalid")
        loop.last_run = datetime.now() - timedelta(days=1)
        result = loop.should_run()
        # Invalid frequency should return False
        assert result is False


class TestStrategicHook:
    """Test StrategicHook functionality"""

    def test_init(self):
        """Test StrategicHook initialization"""
        hook = StrategicHook("score > 1000", "trigger_analysis", "High engagement hook")
        assert hook.condition == "score > 1000"
        assert hook.action == "trigger_analysis"
        assert hook.description == "High engagement hook"
        assert hook.triggered_count == 0

    def test_check_condition_numeric_comparison(self):
        """Test numeric comparison conditions"""
        test_cases = [
            ("score > 1000", {"score": 1500}, True),
            ("score > 1000", {"score": 500}, False),
            ("engagement >= 100", {"engagement": 100}, True),
            ("engagement >= 100", {"engagement": 99}, False),
            ("count < 5", {"count": 3}, True),
            ("count < 5", {"count": 10}, False),
            ("points == 42", {"points": 42}, True),
            ("points == 42", {"points": 43}, False),
            ("points != 0", {"points": 5}, True),
            ("points != 0", {"points": 0}, False),
        ]

        for condition, data, expected in test_cases:
            hook = StrategicHook(condition, "action", "desc")
            result = hook.check_condition(data)
            assert result is expected, f"Failed for condition '{condition}' with data {data}"

    def test_check_condition_contains(self):
        """Test contains-type conditions"""
        test_cases = [
            ("contains 'AI writing'", {"title": "AI writing tools overview"}, True),
            ("contains 'AI writing'", {"title": "Python programming guide"}, False),
            ("contains 'react'", {"content": "React vs Vue comparison"}, True),
            ("contains 'react'", {"title": "Angular tutorial"}, False),
            # Test case insensitive matching
            ("contains 'PYTHON'", {"title": "python programming"}, True),
            # Test nested data structures
            ("contains 'claude'", {"items": [{"title": "Claude API guide"}]}, True),
            ("contains 'claude'", {"metadata": {"description": "Claude Code tutorial"}}, True),
        ]

        for condition, data, expected in test_cases:
            hook = StrategicHook(condition, "action", "desc")
            result = hook.check_condition(data)
            assert result is expected, f"Failed for condition '{condition}' with data {data}"

    def test_check_condition_invalid_format(self):
        """Test invalid condition formats"""
        invalid_conditions = [
            "invalid condition",
            "score >>>",
            "contains without quotes",
            "random text",
            "",
        ]

        data = {"score": 100, "title": "test content"}
        for condition in invalid_conditions:
            hook = StrategicHook(condition, "action", "desc")
            result = hook.check_condition(data)
            assert result is False, f"Invalid condition '{condition}' should return False"

    def test_check_condition_missing_field(self):
        """Test conditions with missing data fields"""
        hook = StrategicHook("nonexistent > 100", "action", "desc")
        data = {"score": 200}
        result = hook.check_condition(data)
        assert result is False


class TestIntelligenceItem:
    """Test IntelligenceItem data structure"""

    def test_init(self):
        """Test IntelligenceItem initialization"""
        item = IntelligenceItem(
            title="Test Item",
            url="https://example.com",
            score=100,
            comments=50,
            timestamp="2026-06-11T10:00:00Z",
            source_id="test_source"
        )
        assert item.title == "Test Item"
        assert item.url == "https://example.com"
        assert item.score == 100
        assert item.comments == 50
        assert item.source_id == "test_source"
        assert item.metadata == {}

    def test_init_with_metadata(self):
        """Test IntelligenceItem with metadata"""
        metadata = {"raw_item": {"id": 123}}
        item = IntelligenceItem("Test", "url", 0, 0, "timestamp", "source", metadata=metadata)
        assert item.metadata == metadata


# Commented out until we fix the import issues with orchestrator
# class TestAutonomousOrchestrator:
#     """Test AutonomousOrchestrator functionality"""
#
#     # Will uncomment and implement after fixing relative imports


# Integration tests that will need updating as we implement the methods
class TestAutonomousIntegration:
    """Integration tests for autonomous system components"""

    @pytest.mark.integration
    def test_frequency_parsing_patterns(self):
        """Test various frequency patterns that should be supported"""
        # These will need implementation in should_run()
        patterns = ["30m", "2h", "1d", "2d", "1w", "2w"]
        for pattern in patterns:
            loop = AutonomousLoop("test", pattern)
            # For now, just verify the frequency is stored
            assert loop.frequency == pattern

    @pytest.mark.integration
    def test_condition_evaluation_patterns(self):
        """Test various condition patterns that should be supported"""
        # These will need implementation in check_condition()
        conditions = [
            "score > 1000",
            "engagement >= 500",
            "contains 'AI writing'",
            "score < 100"
        ]
        for condition in conditions:
            hook = StrategicHook(condition, "action", "desc")
            # For now, just verify the condition is stored
            assert hook.condition == condition


if __name__ == "__main__":
    pytest.main([__file__])
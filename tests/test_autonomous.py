"""
Tests for radar-engine fetcher components
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch
import sys
import os

radar_engine_path = os.path.join(os.path.dirname(__file__), '..', 'radar-engine')
sys.path.insert(0, radar_engine_path)

try:
    from radar_engine.core.base import IntelligenceItem, BaseFetcher
except ImportError:
    import importlib.util
    base_spec = importlib.util.spec_from_file_location(
        "radar_engine.core.base",
        os.path.join(radar_engine_path, "core", "base.py")
    )
    base_module = importlib.util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base_module)
    IntelligenceItem = base_module.IntelligenceItem
    BaseFetcher = base_module.BaseFetcher


class TestIntelligenceItem:
    """Test IntelligenceItem data structure"""

    def test_init(self):
        item = IntelligenceItem(
            title="Test Item",
            url="https://example.com",
            score=100,
            comments=50,
            timestamp="2026-06-19T10:00:00Z",
            source_id="test_source"
        )
        assert item.title == "Test Item"
        assert item.url == "https://example.com"
        assert item.score == 100
        assert item.comments == 50
        assert item.source_id == "test_source"
        assert item.content == ""

    def test_init_with_content(self):
        item = IntelligenceItem("Test", "url", 0, 0, "ts", "src", content="Article description here")
        assert item.content == "Article description here"


class TestSourceConfigs:
    """Test that source YAML configs are valid"""

    def test_all_sources_have_required_fields(self):
        import yaml
        sources_dir = Path(__file__).parent.parent / "sources"
        for yaml_file in sources_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
            assert "id" in config, f"{yaml_file.name} missing 'id'"
            assert "type" in config, f"{yaml_file.name} missing 'type'"
            assert "config" in config, f"{yaml_file.name} missing 'config'"
            assert "endpoint" in config["config"], f"{yaml_file.name} missing 'config.endpoint'"

    def test_enabled_sources_have_valid_type(self):
        import yaml
        sources_dir = Path(__file__).parent.parent / "sources"
        for yaml_file in sources_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
            if config.get("enabled", True):
                assert config["type"] in ("json_api", "rss"), \
                    f"{yaml_file.name} has unsupported type: {config['type']}"

    def test_source_ids_are_unique(self):
        import yaml
        sources_dir = Path(__file__).parent.parent / "sources"
        ids = []
        for yaml_file in sources_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
            ids.append(config["id"])
        assert len(ids) == len(set(ids)), f"Duplicate source IDs: {ids}"


class TestRawDataFormat:
    """Test that saved raw data follows expected format"""

    def test_raw_json_is_array_of_items(self, tmp_path):
        items = [
            {"title": "Test", "url": "https://example.com", "score": 10,
             "comments": 5, "timestamp": "2026-06-19T10:00:00Z",
             "source_id": "test", "content": ""}
        ]
        path = tmp_path / "test.json"
        with open(path, 'w') as f:
            json.dump(items, f)

        with open(path) as f:
            loaded = json.load(f)
        assert isinstance(loaded, list)
        assert loaded[0]["title"] == "Test"
        assert "metadata" not in loaded[0]


if __name__ == "__main__":
    pytest.main([__file__])

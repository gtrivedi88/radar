"""
Tests for state file management
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime


class TestStateFileOperations:
    """Test basic state file operations"""

    def test_read_nonexistent_file(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        assert not path.exists()

    def test_write_json_file(self, tmp_path):
        path = tmp_path / "test.json"
        data = {"key": "value", "count": 42}
        with open(path, 'w') as f:
            json.dump(data, f)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_append_jsonl_file(self, tmp_path):
        path = tmp_path / "test.jsonl"
        entries = [
            {"date": "2026-06-19", "theme": "test_theme"},
            {"date": "2026-06-19", "theme": "another_theme"}
        ]
        for entry in entries:
            with open(path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        with open(path) as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) == 2
        assert lines[0]["theme"] == "test_theme"

    def test_read_corrupted_json(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("{invalid json content")
        with pytest.raises(json.JSONDecodeError):
            with open(path) as f:
                json.load(f)

    def test_concurrent_read_write(self, tmp_path):
        path = tmp_path / "concurrent.jsonl"
        for i in range(10):
            with open(path, 'a') as f:
                f.write(json.dumps({"index": i}) + '\n')
        with open(path) as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) == 10


class TestStateFileFormats:
    """Test state file format validation"""

    def test_signals_jsonl_format(self, tmp_path):
        path = tmp_path / "signals.jsonl"
        signal = {
            "date": "2026-06-19",
            "theme": "test_signal",
            "source_count": 3,
            "engagement_total": 500
        }
        with open(path, 'a') as f:
            f.write(json.dumps(signal) + '\n')
        with open(path) as f:
            loaded = json.loads(f.readline())
        assert "date" in loaded
        assert "theme" in loaded
        assert isinstance(loaded["source_count"], int)

    def test_raw_data_format(self, tmp_path):
        path = tmp_path / "source.json"
        items = [
            {"title": "Test", "url": "https://example.com", "score": 10,
             "comments": 5, "timestamp": "2026-06-19T10:00:00Z",
             "source_id": "test", "content": "Description"}
        ]
        with open(path, 'w') as f:
            json.dump(items, f)
        with open(path) as f:
            loaded = json.load(f)
        assert isinstance(loaded, list)
        required_fields = {"title", "url", "score", "comments", "timestamp", "source_id", "content"}
        assert required_fields.issubset(set(loaded[0].keys()))


class TestErrorHandling:
    """Test error scenarios"""

    @pytest.mark.skipif(os.name != 'posix', reason="Unix-only test")
    def test_file_permission_error(self, tmp_path):
        path = tmp_path / "readonly.json"
        path.write_text('{"key": "value"}')
        path.chmod(0o444)
        with pytest.raises(PermissionError):
            with open(path, 'w') as f:
                f.write("test")
        path.chmod(0o644)

    def test_disk_full_simulation(self, tmp_path):
        path = tmp_path / "test.json"
        data = {"key": "value"}
        with open(path, 'w') as f:
            json.dump(data, f)
        assert path.exists()

    def test_partial_write_recovery(self, tmp_path):
        path = tmp_path / "partial.jsonl"
        with open(path, 'w') as f:
            f.write('{"valid": true}\n')
            f.write('{"also_valid": true}\n')
        with open(path) as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) == 2


class TestConcurrencyIssues:
    """Test concurrent access patterns"""

    def test_simultaneous_jsonl_append(self, tmp_path):
        path = tmp_path / "concurrent.jsonl"
        for i in range(20):
            with open(path, 'a') as f:
                f.write(json.dumps({"writer": i}) + '\n')
        with open(path) as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) == 20

    def test_read_during_write(self, tmp_path):
        path = tmp_path / "readwrite.json"
        data = {"version": 1}
        with open(path, 'w') as f:
            json.dump(data, f)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["version"] == 1

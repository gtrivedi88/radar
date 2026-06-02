# tests/unit/test_quality_validator.py
import pytest
from radar.core.quality_validator import QualityValidator, SynthesisQualityResult
from radar.core.models import SourceConfig, SourceType, PreFilter

@pytest.fixture
def quality_validator():
    return QualityValidator()

@pytest.fixture
def sample_source_config():
    return SourceConfig(
        id="test-source",
        name="Test Source",
        type=SourceType.json_api,
        signal_type=["capability"],
        audience_tags=["hardcore_tech"]
    )

def test_validate_source_signal_strength(quality_validator, sample_source_config):
    # Test source quality validation
    raw_items = [{"item_id": f"item_{i}", "title": f"Title {i}", "metrics": {"score": 100}} for i in range(5)]
    filtered_items = raw_items[:3]  # 3 items pass filters

    result = quality_validator.validate_source_quality(sample_source_config.id, raw_items, filtered_items)

    assert result.source_id == "test-source"
    assert result.signal_strength >= 2  # Must contribute ≥2 items
    assert result.is_valid == True

def test_validate_synthesis_quality(quality_validator):
    insights = [
        {"type": "contrarian", "evidence_level": "infrastructure"},
        {"type": "mainstream", "evidence_level": "behavioral"}
    ]
    source_hierarchy = {
        "infrastructure": ["github-trending"],
        "behavioral": ["dev-community"]
    }

    result = quality_validator.validate_synthesis_quality(insights, source_hierarchy)

    assert isinstance(result, SynthesisQualityResult)
    assert result.is_valid == True

def test_validate_source_quality_empty_data(quality_validator, sample_source_config):
    """Test handling of empty filtered items"""
    raw_items = [{"item_id": "1", "title": "Test"}]
    filtered_items = []

    result = quality_validator.validate_source_quality(sample_source_config.id, raw_items, filtered_items)

    assert result.signal_strength == 0
    assert not result.is_valid
    assert "Signal strength 0 below minimum 2" in result.issues

def test_validate_source_quality_invalid_inputs(quality_validator):
    """Test input validation"""
    with pytest.raises(ValueError, match="source_id must be string"):
        quality_validator.validate_source_quality(123, [], [])

    with pytest.raises(ValueError, match="raw_items must be list"):
        quality_validator.validate_source_quality("test", "not-a-list", [])

    with pytest.raises(ValueError, match="filtered_items must be list"):
        quality_validator.validate_source_quality("test", [], "not-a-list")

def test_validate_source_quality_malformed_metrics(quality_validator, sample_source_config):
    """Test handling of malformed metrics data"""
    raw_items = [
        {"item_id": "1", "title": "Test 1", "metrics": "invalid"},  # String instead of dict
        {"item_id": "2", "title": "Test 2", "metrics": {"score": -10}},  # Negative score
        {"item_id": "3", "title": "Test 3", "metrics": {"score": 100}},  # Valid
        {"item_id": "4", "title": "Test 4", "metrics": {"score": 50}},   # Valid
    ]
    filtered_items = raw_items

    result = quality_validator.validate_source_quality(sample_source_config.id, raw_items, filtered_items)

    assert result.signal_strength == 4
    # Should calculate engagement from valid metrics only (100 + 50 = 150, mean = 37.5)
    assert result.engagement_distribution["mean"] > 0

def test_validate_source_quality_no_metrics(quality_validator, sample_source_config):
    """Test handling of items with no metrics"""
    raw_items = [
        {"item_id": "1", "title": "Test 1"},  # No metrics field
        {"item_id": "2", "title": "Test 2", "metrics": {}},  # Empty metrics
    ]
    filtered_items = raw_items

    result = quality_validator.validate_source_quality(sample_source_config.id, raw_items, filtered_items)

    assert result.signal_strength == 2
    assert abs(result.engagement_distribution["mean"] - 0.0) < 1e-6
    assert "No engagement data available" in result.issues
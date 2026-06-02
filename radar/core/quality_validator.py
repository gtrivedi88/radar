"""Signal quality validation framework for elite intelligence"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class SourceQualityResult:
    """Result of source quality validation"""
    source_id: str
    signal_strength: int  # Number of items passing filters
    engagement_distribution: Dict[str, float]  # Score distribution stats
    is_valid: bool
    issues: List[str]

@dataclass
class SynthesisQualityResult:
    """Result of synthesis quality validation"""
    contrarian_detection_rate: float  # % of insights contradicting consensus
    evidence_hierarchy_ratio: Dict[str, float]  # Infrastructure:Economic:Behavioral ratio
    actionability_score: float  # % insights with specific action windows
    is_valid: bool
    issues: List[str]

class QualityValidator:
    """Validates signal quality at source and synthesis levels"""

    def __init__(self):
        # Quality thresholds from design spec
        self.min_signal_strength = 2
        self.target_contrarian_rate = 0.30
        self.target_hierarchy_ratio = {"infrastructure": 0.40, "economic": 0.30, "behavioral": 0.20, "opinion": 0.10}

    def validate_source_quality(
        self,
        source_id: str,
        raw_items: List[Dict[str, Any]],
        filtered_items: List[Dict[str, Any]]
    ) -> SourceQualityResult:
        """Validate source signal quality (Layer 1)"""

        # Add input validation
        if not isinstance(source_id, str):
            raise ValueError(f"source_id must be string, got {type(source_id)}")
        if not isinstance(raw_items, list):
            raise ValueError(f"raw_items must be list, got {type(raw_items)}")
        if not isinstance(filtered_items, list):
            raise ValueError(f"filtered_items must be list, got {type(filtered_items)}")

        signal_strength = len(filtered_items)
        issues = []

        # Signal strength validation
        if signal_strength < self.min_signal_strength:
            issues.append(f"Signal strength {signal_strength} below minimum {self.min_signal_strength}")

        # Calculate engagement distribution with better error handling
        engagement_scores = []
        for item in filtered_items:
            metrics = item.get("metrics", {})
            if not isinstance(metrics, dict):
                continue  # Skip invalid metrics
            score = 0
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and value >= 0:
                    score += value
            engagement_scores.append(score)

        if engagement_scores and any(score > 0 for score in engagement_scores):
            engagement_distribution = {
                "mean": sum(engagement_scores) / len(engagement_scores),
                "max": max(engagement_scores),
                "min": min(engagement_scores)
            }
        else:
            engagement_distribution = {"mean": 0.0, "max": 0.0, "min": 0.0}
            issues.append("No engagement data available")

        is_valid = len(issues) == 0

        logger.info(f"Source quality validation for {source_id}: {signal_strength} items, valid={is_valid}")

        return SourceQualityResult(
            source_id=source_id,
            signal_strength=signal_strength,
            engagement_distribution=engagement_distribution,
            is_valid=is_valid,
            issues=issues
        )

    def validate_synthesis_quality(
        self,
        insights: List[Dict[str, Any]],
        source_hierarchy: Dict[str, List[str]]
    ) -> SynthesisQualityResult:
        """Validate synthesis quality (Layer 2) - stub for now"""
        # TODO: Implement contrarian detection, evidence hierarchy validation
        return SynthesisQualityResult(
            contrarian_detection_rate=0.0,
            evidence_hierarchy_ratio={},
            actionability_score=0.0,
            is_valid=True,
            issues=[]
        )
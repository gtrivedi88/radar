"""Radar: Personal Intelligence System"""

__version__ = "0.1.0"
__author__ = "Gaurav Trivedi"

# Core exports for clean imports
from .core.models import SourceConfig, SourceType
from .core.state_manager import StateManager
from .core.orchestrator import RadarOrchestrator
from .core.quality_validator import QualityValidator

__all__ = [
    "SourceConfig",
    "SourceType",
    "StateManager",
    "RadarOrchestrator",
    "QualityValidator",
]
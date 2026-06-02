"""Core data models and configuration"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceType(str, Enum):
    """Supported source types"""
    rss = "rss"
    json_api = "json_api"
    github_watch = "github_watch"
    scrape = "scrape"
    search_query = "search_query"
    investor_signal = "investor_signal"
    skill_velocity = "skill_velocity"
    pain_point = "pain_point"


class FragilityTier(str, Enum):
    """Source reliability tiers"""
    stable = "stable"
    moderate = "moderate"
    fragile = "fragile"


class PreFilter(BaseModel):
    """Source pre-filtering configuration"""
    min_engagement: int = 0
    recency_window_days: int = 14
    dedup_key: str = "title_url"


class SourceConfig(BaseModel):
    """Source configuration model"""
    id: str
    name: str
    type: SourceType
    config: Dict[str, Any] = Field(default_factory=dict)
    poll_cadence: Literal["hourly", "daily", "weekly"] = "weekly"
    signal_type: List[str]
    audience_tags: List[str]
    relevance_tags: List[str] = Field(default_factory=list)
    pre_filter: PreFilter = Field(default_factory=PreFilter)
    priority: int = 3
    fragility_tier: FragilityTier = FragilityTier.stable
    staleness_threshold_days: int = 14


class RadarConfig(BaseSettings):
    """Global Radar configuration from environment"""

    # Paths
    data_dir: Path = Path("./state")
    sources_dir: Path = Path("./sources")
    raw_dir: Path = Path("./raw")
    intermediate_dir: Path = Path("./intermediate")

    # Logging
    log_level: str = "INFO"

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    github_token: Optional[str] = None

    # v2: Plugin configuration
    plugins_dir: Path = Path("./plugins")
    cache_ttl: int = 300

    model_config = SettingsConfigDict(env_prefix="RADAR_")
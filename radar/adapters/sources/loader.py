"""Source configuration loader"""

from pathlib import Path
from typing import List
import yaml
import logging

from radar.core.models import SourceConfig

logger = logging.getLogger(__name__)


class SourceLoader:
    """Loads and validates source configurations from YAML files"""

    def __init__(self, sources_dir: Path):
        self.sources_dir = sources_dir

    async def load_all_sources(self) -> List[SourceConfig]:
        """Load all source configurations from the sources directory"""
        sources = []

        if not self.sources_dir.exists():
            logger.warning(f"Sources directory does not exist: {self.sources_dir}")
            return sources

        for yaml_file in self.sources_dir.glob("*.yaml"):
            if yaml_file.name.startswith("_"):
                # Skip configuration files like _groups.yaml
                continue

            try:
                source_config = await self.load_source(yaml_file)
                if source_config:
                    sources.append(source_config)
            except Exception as e:
                logger.error(f"Failed to load source from {yaml_file}: {e}")

        logger.info(f"Loaded {len(sources)} source configurations")
        return sources

    async def load_source(self, yaml_file: Path) -> SourceConfig:
        """Load a single source configuration from YAML file"""
        with yaml_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return SourceConfig.model_validate(data)

    async def load_groups_config(self) -> dict:
        """Load source groups configuration"""
        groups_file = self.sources_dir / "_groups.yaml"
        if groups_file.exists():
            with groups_file.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {"groups": {}}
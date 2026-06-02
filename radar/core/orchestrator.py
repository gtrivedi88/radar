"""Main coordination logic for Radar"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

from .models import RadarConfig, SourceConfig
from .state_manager import StateManager

logger = logging.getLogger(__name__)


class RadarOrchestrator:
    """Coordinates the full Radar pipeline: ingestion → synthesis → delivery"""

    def __init__(self, config: RadarConfig):
        self.config = config
        self.state_manager = StateManager(config)

    async def run_ingestion(self, sources: List[SourceConfig]) -> Dict[str, Any]:
        """Run the ingestion pipeline for given sources"""
        logger.info(f"Starting ingestion for {len(sources)} sources")

        # TODO: Implement full ingestion pipeline
        # For v0: basic structure that can be extended
        results = {
            "sources_processed": len(sources),
            "items_fetched": 0,
            "items_filtered": 0,
            "errors": [],
        }

        return results

    async def run_synthesis(self) -> Dict[str, Any]:
        """Run the MRR synthesis pipeline"""
        logger.info("Starting synthesis pipeline")

        # TODO: Implement MRR synthesis
        # For v0: basic structure that integrates with Claude Code
        results = {
            "sections_generated": 0,
            "predictions_tracked": 0,
            "digest_path": None,
        }

        return results

    async def health_check(self) -> Dict[str, Any]:
        """Check system health and configuration"""
        logger.info("Running health check")

        health = {
            "status": "healthy",
            "directories": {},
            "state_files": {},
            "config": {
                "data_dir": str(self.config.data_dir),
                "sources_dir": str(self.config.sources_dir),
            }
        }

        # Check directories exist
        for name, path in [
            ("data_dir", self.config.data_dir),
            ("sources_dir", self.config.sources_dir),
            ("raw_dir", self.config.raw_dir),
        ]:
            health["directories"][name] = path.exists()

        # Check state files exist
        for name, filename in [
            ("profile", "profile.md"),
            ("catalog", "catalog.md"),
            ("trajectory", "trajectory.md"),
            ("signals", "signals.jsonl"),
        ]:
            file_path = self.config.data_dir / filename
            health["state_files"][name] = file_path.exists()

        return health
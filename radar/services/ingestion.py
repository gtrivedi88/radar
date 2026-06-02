"""Ingestion service coordinating fetchers and storage"""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Union, Tuple
import logging
import time

from radar.core.models import SourceConfig, RadarConfig
from radar.adapters.fetchers import FetcherRegistry
from radar.adapters.storage import FileStorage
from radar.core.quality_validator import QualityValidator

logger = logging.getLogger(__name__)


class IngestionService:
    """Coordinates source ingestion pipeline"""

    def __init__(self, config: RadarConfig, max_concurrent_sources: int = 5):
        self.config = config
        self.storage = FileStorage(config.raw_dir)
        self.quality_validator = QualityValidator()
        self.semaphore = asyncio.Semaphore(max_concurrent_sources)

    async def ingest_sources(self, sources: List[SourceConfig]) -> Dict[str, Any]:
        """Ingest data from all provided sources with parallel processing"""
        run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        logger.info(f"Starting parallel ingestion for {len(sources)} sources on {run_date}")
        start_time = time.time()

        results = {
            "run_date": run_date,
            "sources_processed": 0,
            "total_items": 0,
            "successful_sources": [],
            "failed_sources": [],
            "errors": [],
            "quality_results": [],
            "timing": {
                "total_duration": 0.0,
                "per_source_timing": {}
            }
        }

        if not sources:
            logger.info("No sources to process")
            return results

        # Parallel processing with error isolation
        tasks = [self._ingest_single_source_with_error_handling(source, run_date) for source in sources]
        source_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for source, result in zip(sources, source_results):
            if isinstance(result, Exception):
                # Handle unexpected exceptions that weren't caught in error handler
                logger.error(f"Unexpected error for source {source.id}: {result}")
                results["failed_sources"].append(source.id)
                results["errors"].append({
                    "source_id": source.id,
                    "error": str(result),
                    "error_type": type(result).__name__
                })
            elif result["success"]:
                results["sources_processed"] += 1
                results["total_items"] += result["item_count"]
                results["successful_sources"].append(source.id)
                results["quality_results"].append(result["quality_result"])
                results["timing"]["per_source_timing"][source.id] = result["duration"]
                logger.info(f"Successfully ingested {result['item_count']} items from {source.id}")
            else:
                results["failed_sources"].append(source.id)
                results["errors"].append({
                    "source_id": source.id,
                    "error": result["error"],
                    "error_type": result["error_type"]
                })
                results["timing"]["per_source_timing"][source.id] = result["duration"]

        end_time = time.time()
        results["timing"]["total_duration"] = end_time - start_time

        logger.info(
            f"Parallel ingestion complete: {results['sources_processed']}/{len(sources)} sources, "
            f"{results['total_items']} total items in {results['timing']['total_duration']:.2f}s"
        )
        return results

    async def _ingest_single_source_with_error_handling(
        self, source: SourceConfig, run_date: str
    ) -> Dict[str, Any]:
        """Ingest data from a single source with comprehensive error handling and quality validation"""
        source_start_time = time.time()

        try:
            async with self.semaphore:  # Concurrency control
                # Fetch and process items
                raw_items = await self._fetch_source_items(source)
                filtered_items = self._apply_prefiltering(raw_items)
                await self.storage.save_raw_data(run_date, source.id, filtered_items)

                # Quality validation
                quality_result = self.quality_validator.validate_source_quality(
                    source.id, raw_items, filtered_items
                )

                source_duration = time.time() - source_start_time

                return {
                    "success": True,
                    "item_count": len(filtered_items),
                    "quality_result": quality_result,
                    "duration": source_duration,
                    "error": None,
                    "error_type": None
                }

        except Exception as e:
            source_duration = time.time() - source_start_time
            logger.exception(f"Failed to ingest source {source.id}")

            return {
                "success": False,
                "item_count": 0,
                "quality_result": None,
                "duration": source_duration,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def _fetch_source_items(self, source: SourceConfig) -> List[Dict[str, Any]]:
        """Fetch raw items from a source"""
        fetcher = FetcherRegistry.create_fetcher(source)
        if not fetcher:
            raise ValueError(f"No fetcher available for source type: {source.type}")

        return await fetcher.fetch_items()

    def _apply_prefiltering(
        self, raw_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply prefiltering to raw items"""
        # v1: Enhanced prefiltering will be implemented in prefilter service
        return raw_items  # For now, return all items

    async def _ingest_single_source(self, source: SourceConfig, run_date: str) -> List[Dict[str, Any]]:
        """Legacy method for backward compatibility - ingest data from a single source"""
        fetcher = FetcherRegistry.create_fetcher(source)
        if not fetcher:
            raise ValueError(f"No fetcher available for source type: {source.type}")

        # Fetch raw items
        raw_items = await fetcher.fetch_items()

        # Apply prefiltering (enhanced in v1)
        filtered_items = self._apply_prefiltering(raw_items)

        # Save to storage
        await self.storage.save_raw_data(run_date, source.id, filtered_items)

        return filtered_items
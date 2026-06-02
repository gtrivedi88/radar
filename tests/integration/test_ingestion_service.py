"""Integration tests for parallel processing ingestion service"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import List, Dict, Any

from radar.services.ingestion import IngestionService
from radar.core.models import SourceConfig, RadarConfig
from radar.core.quality_validator import QualityValidator, SourceQualityResult


class MockFetcher:
    """Mock fetcher for testing"""

    def __init__(self, items: List[Dict[str, Any]], delay: float = 0.1, should_fail: bool = False):
        self.items = items
        self.delay = delay
        self.should_fail = should_fail

    async def fetch_items(self) -> List[Dict[str, Any]]:
        """Mock fetch with configurable delay and failure"""
        await asyncio.sleep(self.delay)
        if self.should_fail:
            raise ValueError("Mock fetch failure")
        return self.items


@pytest.fixture
def radar_config(tmp_path):
    """Create test radar config"""
    return RadarConfig(
        raw_dir=str(tmp_path / "raw"),
        sources_dir=str(tmp_path / "sources"),
        data_dir=str(tmp_path / "state")
    )


@pytest.fixture
def sample_sources():
    """Create sample source configs for testing"""
    return [
        SourceConfig(
            id="fast_source",
            name="Fast Source",
            type="json_api",
            signal_type=["tech"],
            audience_tags=["developers"],
            config={"delay": 0.1}
        ),
        SourceConfig(
            id="slow_source",
            name="Slow Source",
            type="json_api",
            signal_type=["tech"],
            audience_tags=["developers"],
            config={"delay": 0.3}
        ),
        SourceConfig(
            id="medium_source",
            name="Medium Source",
            type="json_api",
            signal_type=["tech"],
            audience_tags=["developers"],
            config={"delay": 0.2}
        )
    ]


@pytest.fixture
def sample_items():
    """Sample items for different sources"""
    return {
        "fast_source": [
            {"title": "Fast Item 1", "metrics": {"score": 10}},
            {"title": "Fast Item 2", "metrics": {"score": 15}}
        ],
        "slow_source": [
            {"title": "Slow Item 1", "metrics": {"score": 20}},
            {"title": "Slow Item 2", "metrics": {"score": 25}},
            {"title": "Slow Item 3", "metrics": {"score": 30}}
        ],
        "medium_source": [
            {"title": "Medium Item 1", "metrics": {"score": 18}}
        ]
    }


class TestParallelIngestionService:
    """Test parallel processing capabilities"""

    @pytest.mark.asyncio
    async def test_parallel_processing_all_success(self, radar_config, sample_sources, sample_items):
        """Test parallel processing with all sources succeeding"""
        service = IngestionService(radar_config)

        # Mock the fetcher creation to return configured fetchers
        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            mock_fetchers = {
                source.id: MockFetcher(sample_items[source.id], delay=float(source.config["delay"]))
                for source in sample_sources
            }
            mock_create.side_effect = lambda source: mock_fetchers[source.id]

            # Mock storage
            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock) as mock_save:
                start_time = asyncio.get_event_loop().time()
                results = await service.ingest_sources(sample_sources)
                end_time = asyncio.get_event_loop().time()

                # Verify parallel execution is faster than sequential
                # Sequential would be: 0.1 + 0.3 + 0.2 = 0.6s
                # Parallel should be: max(0.1, 0.3, 0.2) ≈ 0.3s
                execution_time = end_time - start_time
                assert execution_time < 0.5, f"Execution took {execution_time}s, expected < 0.5s"

                # Verify all sources processed successfully
                assert results["sources_processed"] == 3
                assert len(results["successful_sources"]) == 3
                assert len(results["failed_sources"]) == 0
                assert results["total_items"] == 6

                # Verify all sources saved
                assert mock_save.call_count == 3

                # Verify quality validation results are included
                assert "quality_results" in results
                assert len(results["quality_results"]) == 3


    @pytest.mark.asyncio
    async def test_parallel_processing_with_failures(self, radar_config, sample_sources, sample_items):
        """Test parallel processing with some sources failing"""
        service = IngestionService(radar_config)

        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            # Configure fetchers: fast succeeds, slow fails, medium succeeds
            mock_fetchers = {
                "fast_source": MockFetcher(sample_items["fast_source"], delay=0.1),
                "slow_source": MockFetcher([], delay=0.3, should_fail=True),
                "medium_source": MockFetcher(sample_items["medium_source"], delay=0.2)
            }
            mock_create.side_effect = lambda source: mock_fetchers[source.id]

            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock):
                results = await service.ingest_sources(sample_sources)

                # Verify partial success
                assert results["sources_processed"] == 2  # fast and medium succeeded
                assert len(results["successful_sources"]) == 2
                assert len(results["failed_sources"]) == 1
                assert "slow_source" in results["failed_sources"]
                assert results["total_items"] == 3  # 2 from fast + 1 from medium

                # Verify error details
                assert len(results["errors"]) == 1
                assert results["errors"][0]["source_id"] == "slow_source"
                assert "Mock fetch failure" in results["errors"][0]["error"]

                # Verify quality results only for successful sources
                assert len(results["quality_results"]) == 2


    @pytest.mark.asyncio
    async def test_concurrency_control(self, radar_config):
        """Test semaphore-based concurrency control"""
        service = IngestionService(radar_config)

        # Create 10 sources to test concurrency limits
        many_sources = [
            SourceConfig(
                id=f"source_{i}",
                name=f"Source {i}",
                type="json_api",
                signal_type=["tech"],
                audience_tags=["developers"],
                config={}
            )
            for i in range(10)
        ]

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def tracking_fetch():
            nonlocal concurrent_count, max_concurrent
            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

            await asyncio.sleep(0.1)  # Simulate work

            async with lock:
                concurrent_count -= 1

            return [{"title": "Test item"}]

        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            mock_fetcher = AsyncMock()
            mock_fetcher.fetch_items = tracking_fetch
            mock_create.return_value = mock_fetcher

            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock):
                await service.ingest_sources(many_sources)

                # Verify concurrency was limited (default should be 5)
                assert max_concurrent <= 5, f"Max concurrent was {max_concurrent}, expected <= 5"


    @pytest.mark.asyncio
    async def test_quality_validation_integration(self, radar_config, sample_sources, sample_items):
        """Test quality validation integration"""
        service = IngestionService(radar_config)

        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            mock_fetchers = {
                source.id: MockFetcher(sample_items[source.id])
                for source in sample_sources
            }
            mock_create.side_effect = lambda source: mock_fetchers[source.id]

            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock):
                # Mock the quality validator instance on the service
                mock_validator = MagicMock()
                mock_validator.validate_source_quality.return_value = SourceQualityResult(
                    source_id="test",
                    signal_strength=2,
                    engagement_distribution={"mean": 15.0, "max": 30.0, "min": 10.0},
                    is_valid=True,
                    issues=[]
                )
                service.quality_validator = mock_validator

                results = await service.ingest_sources(sample_sources)

                # Verify quality validation was called for each successful source
                assert mock_validator.validate_source_quality.call_count == 3

                # Verify quality results included
                assert "quality_results" in results
                assert len(results["quality_results"]) == 3


    @pytest.mark.asyncio
    async def test_performance_timing_tracking(self, radar_config, sample_sources, sample_items):
        """Test that performance timing is tracked"""
        service = IngestionService(radar_config)

        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            mock_fetchers = {
                source.id: MockFetcher(sample_items[source.id], delay=0.1)
                for source in sample_sources
            }
            mock_create.side_effect = lambda source: mock_fetchers[source.id]

            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock):
                results = await service.ingest_sources(sample_sources)

                # Verify timing information is included
                assert "timing" in results
                assert "total_duration" in results["timing"]
                assert "per_source_timing" in results["timing"]
                assert len(results["timing"]["per_source_timing"]) == 3


    @pytest.mark.asyncio
    async def test_error_categorization(self, radar_config, sample_sources):
        """Test that errors are properly categorized"""
        service = IngestionService(radar_config)

        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            # Configure different failure types
            mock_fetchers = {
                "fast_source": MockFetcher([], should_fail=True),  # Network error
                "slow_source": MockFetcher([]),  # Success
                "medium_source": MockFetcher([])  # Success
            }

            # Override the first fetcher to raise a specific error type
            async def network_error():
                raise ConnectionError("Network timeout")
            mock_fetchers["fast_source"].fetch_items = network_error

            mock_create.side_effect = lambda source: mock_fetchers[source.id]

            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock):
                results = await service.ingest_sources(sample_sources)

                # Verify error categorization
                assert len(results["errors"]) == 1
                error = results["errors"][0]
                assert error["source_id"] == "fast_source"
                assert "error_type" in error
                assert error["error_type"] == "ConnectionError"


    @pytest.mark.asyncio
    async def test_backward_compatibility(self, radar_config, sample_sources, sample_items):
        """Test that the new parallel implementation maintains API compatibility"""
        service = IngestionService(radar_config)

        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            mock_fetchers = {
                source.id: MockFetcher(sample_items[source.id])
                for source in sample_sources
            }
            mock_create.side_effect = lambda source: mock_fetchers[source.id]

            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock):
                results = await service.ingest_sources(sample_sources)

                # Verify all original fields are present
                required_fields = [
                    "run_date", "sources_processed", "total_items",
                    "successful_sources", "failed_sources", "errors"
                ]
                for field in required_fields:
                    assert field in results, f"Required field '{field}' missing"

                # Verify new fields are present
                new_fields = ["quality_results", "timing"]
                for field in new_fields:
                    assert field in results, f"New field '{field}' missing"


    @pytest.mark.asyncio
    async def test_all_sources_fail(self, radar_config, sample_sources):
        """Test behavior when all sources fail"""
        service = IngestionService(radar_config)

        with patch('radar.adapters.fetchers.FetcherRegistry.create_fetcher') as mock_create:
            mock_fetcher = MockFetcher([], should_fail=True)
            mock_create.return_value = mock_fetcher

            with patch.object(service.storage, 'save_raw_data', new_callable=AsyncMock):
                results = await service.ingest_sources(sample_sources)

                # Verify graceful handling of total failure
                assert results["sources_processed"] == 0
                assert len(results["successful_sources"]) == 0
                assert len(results["failed_sources"]) == 3
                assert results["total_items"] == 0
                assert len(results["errors"]) == 3
                assert len(results["quality_results"]) == 0


    @pytest.mark.asyncio
    async def test_empty_sources_list(self, radar_config):
        """Test behavior with empty sources list"""
        service = IngestionService(radar_config)

        results = await service.ingest_sources([])

        # Verify graceful handling of empty input
        assert results["sources_processed"] == 0
        assert len(results["successful_sources"]) == 0
        assert len(results["failed_sources"]) == 0
        assert results["total_items"] == 0
        assert len(results["errors"]) == 0
        assert len(results["quality_results"]) == 0
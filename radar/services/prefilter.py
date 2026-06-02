"""Prefiltering service for signal processing"""

from typing import List, Dict, Any, Set
from datetime import datetime, timezone, timedelta
import logging

from radar.core.models import SourceConfig, PreFilter

logger = logging.getLogger(__name__)


class PrefilterService:
    """Applies prefiltering rules to raw items"""

    def __init__(self):
        pass

    async def apply_filters(
        self,
        items: List[Dict[str, Any]],
        source_config: SourceConfig,
        seen_dedup_keys: Set[str] = None,
    ) -> List[Dict[str, Any]]:
        """Apply prefiltering pipeline to items"""
        if seen_dedup_keys is None:
            seen_dedup_keys = set()

        prefilter = source_config.pre_filter
        logger.info(f"Applying prefilters to {len(items)} items from {source_config.id}")

        # Step 1: Recency filter
        items = self._filter_by_recency(items, prefilter)
        logger.debug(f"After recency filter: {len(items)} items")

        # Step 2: Engagement filter
        items = self._filter_by_engagement(items, prefilter)
        logger.debug(f"After engagement filter: {len(items)} items")

        # Step 3: Deduplication
        items = self._filter_by_dedup(items, prefilter, seen_dedup_keys)
        logger.debug(f"After dedup filter: {len(items)} items")

        logger.info(f"Prefiltering complete: {len(items)} items passed filters")
        return items

    def _filter_by_recency(self, items: List[Dict[str, Any]], prefilter: PreFilter) -> List[Dict[str, Any]]:
        """Filter items by recency window"""
        if prefilter.recency_window_days <= 0:
            return items

        cutoff = datetime.now(timezone.utc) - timedelta(days=prefilter.recency_window_days)
        filtered_items = []

        for item in items:
            timestamp_str = item.get("timestamp")
            if not timestamp_str:
                continue  # Skip items without timestamp

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if timestamp >= cutoff:
                    filtered_items.append(item)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid timestamp format: {timestamp_str} - {e}")
                continue

        return filtered_items

    def _filter_by_engagement(self, items: List[Dict[str, Any]], prefilter: PreFilter) -> List[Dict[str, Any]]:
        """Filter items by minimum engagement threshold"""
        if prefilter.min_engagement <= 0:
            return items

        filtered_items = []
        for item in items:
            engagement_score = self._calculate_engagement_score(item)
            if engagement_score >= prefilter.min_engagement:
                filtered_items.append(item)

        return filtered_items

    def _filter_by_dedup(
        self,
        items: List[Dict[str, Any]],
        prefilter: PreFilter,
        seen_dedup_keys: Set[str]
    ) -> List[Dict[str, Any]]:
        """Filter out duplicate items based on dedup key"""
        filtered_items = []

        for item in items:
            dedup_key = item.get("dedup_key") or item.get("item_id")
            if dedup_key and dedup_key not in seen_dedup_keys:
                filtered_items.append(item)
                seen_dedup_keys.add(dedup_key)

        return filtered_items

    def _calculate_engagement_score(self, item: Dict[str, Any]) -> int:
        """Calculate total engagement score from available metrics"""
        metrics = item.get("metrics", {})
        total_score = 0

        # Sum common engagement metrics
        for metric_name in ["score", "points", "comments", "stars", "upvotes", "replies"]:
            value = metrics.get(metric_name)
            if isinstance(value, (int, float)):
                total_score += int(value)

        return total_score
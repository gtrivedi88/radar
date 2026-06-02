"""File-based storage adapter"""

import json
from pathlib import Path
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class FileStorage:
    """File-based storage for raw data and state"""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    async def save_raw_data(self, date: str, source_id: str, items: List[Dict[str, Any]]) -> Path:
        """Save raw fetched items to date-organized files"""
        output_dir = self.base_path / date
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{source_id}.json"
        payload = {
            "source_id": source_id,
            "run_date": date,
            "items": items,
            "item_count": len(items),
        }

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(items)} items to {output_file}")
        return output_file

    async def load_raw_data(self, date: str, source_id: str) -> List[Dict[str, Any]]:
        """Load raw data for a specific date and source"""
        data_file = self.base_path / date / f"{source_id}.json"

        if not data_file.exists():
            return []

        with data_file.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        return payload.get("items", [])

    async def list_available_dates(self) -> List[str]:
        """List available data dates"""
        if not self.base_path.exists():
            return []

        dates = []
        for date_dir in self.base_path.iterdir():
            if date_dir.is_dir() and date_dir.name.count("-") == 2:  # YYYY-MM-DD format
                dates.append(date_dir.name)

        return sorted(dates, reverse=True)  # Most recent first
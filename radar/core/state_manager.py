"""State management abstraction"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging

from .models import RadarConfig

logger = logging.getLogger(__name__)


class StateManager:
    """Manages radar state files with versioned schemas"""

    def __init__(self, config: RadarConfig):
        self.config = config
        self.state_dir = config.data_dir
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        for dir_path in [
            self.state_dir,
            self.state_dir / "archive",
            self.config.raw_dir,
            self.config.intermediate_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    async def load_profile(self) -> Optional[str]:
        """Load operator profile"""
        profile_path = self.state_dir / "profile.md"
        if profile_path.exists():
            return profile_path.read_text(encoding="utf-8")
        return None

    async def load_catalog(self) -> Optional[str]:
        """Load published work catalog"""
        catalog_path = self.state_dir / "catalog.md"
        if catalog_path.exists():
            return catalog_path.read_text(encoding="utf-8")
        return None

    async def load_trajectory(self) -> Optional[str]:
        """Load learning trajectory"""
        trajectory_path = self.state_dir / "trajectory.md"
        if trajectory_path.exists():
            return trajectory_path.read_text(encoding="utf-8")
        return None

    async def load_feedback(self) -> Optional[str]:
        """Load feedback log"""
        feedback_path = self.state_dir / "feedback.md"
        if feedback_path.exists():
            return feedback_path.read_text(encoding="utf-8")
        return None

    async def load_signals(self) -> List[Dict[str, Any]]:
        """Load signals from JSONL file"""
        signals_path = self.state_dir / "signals.jsonl"
        if not signals_path.exists():
            return []

        signals = []
        for line in signals_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    signals.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in signals.jsonl: {line} - {e}")
                    continue
        return signals

    async def append_signal(self, signal: Dict[str, Any]) -> None:
        """Append signal to JSONL file"""
        signals_path = self.state_dir / "signals.jsonl"
        with signals_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(signal, ensure_ascii=False) + "\n")

    async def load_watermarks(self) -> Dict[str, str]:
        """Load source watermarks"""
        watermarks_path = self.state_dir / "watermarks.json"
        if not watermarks_path.exists():
            return {}

        try:
            return json.loads(watermarks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Invalid watermarks.json, returning empty dict")
            return {}

    async def save_watermarks(self, watermarks: Dict[str, str]) -> None:
        """Save source watermarks"""
        watermarks_path = self.state_dir / "watermarks.json"
        watermarks_path.write_text(
            json.dumps(watermarks, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )
"""Signal persistence commands"""

import json
import logging
from pathlib import Path

from rich.console import Console

from radar.core.models import RadarConfig
from radar.core.state_manager import StateManager

console = Console()
logger = logging.getLogger(__name__)


async def persist_signal_data(signal_json: str):
    """Persist signal data to signals.jsonl"""
    try:
        # Parse JSON
        signal_data = json.loads(signal_json)

        # Validate required fields
        required_fields = {"date"}
        if not required_fields.issubset(signal_data.keys()):
            missing = required_fields - signal_data.keys()
            console.print(f"❌ [bold red]Missing required fields:[/bold red] {missing}")
            return

        # Save signal
        config = RadarConfig()
        state_manager = StateManager(config)
        await state_manager.append_signal(signal_data)

        console.print(f"✅ [green]Signal persisted successfully[/green]")
        console.print(f"📄 Data: {json.dumps(signal_data, indent=2)}")

    except json.JSONDecodeError as e:
        console.print(f"❌ [bold red]Invalid JSON:[/bold red] {e}")

    except Exception as e:
        console.print(f"❌ [bold red]Failed to persist signal:[/bold red] {e}")
        logger.exception("Signal persistence failed")
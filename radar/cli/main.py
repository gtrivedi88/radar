"""Main CLI application entry point"""

import asyncio
from pathlib import Path
from typing import Optional
import logging

import typer
from rich.console import Console
from rich.logging import RichHandler

from radar.core.models import RadarConfig
from radar.core.orchestrator import RadarOrchestrator
from .commands import ingest, persist

# Create Typer app
app = typer.Typer(
    name="radar",
    help="Personal Intelligence System - Elite predictive intelligence for technical creators",
    no_args_is_help=True,
)

# Add command groups
app.add_typer(ingest.app, name="ingest")

console = Console()


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging with Rich handler"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


@app.callback()
def main(
    log_level: str = typer.Option("INFO", help="Log level"),
    data_dir: Optional[Path] = typer.Option(None, help="Override data directory"),
):
    """Radar: Personal Intelligence System"""
    setup_logging(log_level)


@app.command()
def health():
    """Check system health and configuration"""
    async def _health():
        config = RadarConfig()
        orchestrator = RadarOrchestrator(config)

        console.print("🔍 [bold blue]Running Radar health check...[/bold blue]")
        health_data = await orchestrator.health_check()

        if health_data["status"] == "healthy":
            console.print("✅ [bold green]System is healthy[/bold green]")
        else:
            console.print("❌ [bold red]System has issues[/bold red]")

        console.print("\n📁 [bold]Directories:[/bold]")
        for name, exists in health_data["directories"].items():
            status = "✅" if exists else "❌"
            console.print(f"  {status} {name}")

        console.print("\n📄 [bold]State Files:[/bold]")
        for name, exists in health_data["state_files"].items():
            status = "✅" if exists else "❌"
            console.print(f"  {status} {name}")

        console.print(f"\n⚙️  [bold]Configuration:[/bold]")
        for key, value in health_data["config"].items():
            console.print(f"  {key}: {value}")

    asyncio.run(_health())


@app.command()
def persist_signal(
    signal_json: str = typer.Argument(..., help="JSON signal to persist"),
):
    """Persist a signal to state/signals.jsonl"""
    asyncio.run(persist.persist_signal_data(signal_json))


if __name__ == "__main__":
    app()
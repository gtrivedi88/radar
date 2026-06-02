"""Ingestion CLI commands"""

import asyncio
from pathlib import Path
from typing import Optional
import logging

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from radar.core.models import RadarConfig
from radar.adapters.sources import SourceLoader
from radar.services import IngestionService, GitOpsService

app = typer.Typer(help="Source ingestion commands")
console = Console()
logger = logging.getLogger(__name__)


@app.command()
def run(
    skip_preflight: bool = typer.Option(False, "--skip-preflight", help="Skip git preflight check"),
    sources_dir: Optional[Path] = typer.Option(None, help="Override sources directory"),
):
    """Run ingestion for all configured sources"""
    asyncio.run(_run_ingestion(skip_preflight, sources_dir))


async def _run_ingestion(skip_preflight: bool, sources_dir: Optional[Path]):
    """Main ingestion workflow"""
    config = RadarConfig()
    if sources_dir:
        config.sources_dir = sources_dir

    console.print("🚀 [bold blue]Starting Radar ingestion...[/bold blue]")

    # Git preflight check (R12)
    if not skip_preflight:
        console.print("🔍 Running git preflight check...")
        git_ops = GitOpsService(Path.cwd())
        preflight_result = await git_ops.preflight_check()

        if not preflight_result["success"]:
            console.print(f"❌ [bold red]Git preflight failed:[/bold red] {preflight_result['message']}")
            console.print("💡 Fix conflicts or use --skip-preflight for local testing")
            raise typer.Exit(1)

        console.print("✅ Git preflight passed")

    # Load sources
    console.print("📋 Loading source configurations...")
    source_loader = SourceLoader(config.sources_dir)
    sources = await source_loader.load_all_sources()

    if not sources:
        console.print(f"⚠️  [yellow]No sources found in {config.sources_dir}[/yellow]")
        console.print("💡 Add .yaml files to the sources/ directory")
        raise typer.Exit(0)

    console.print(f"📡 Found {len(sources)} source(s)")

    # Display sources table
    table = Table(title="Sources to Process")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Priority", style="magenta")

    for source in sources:
        table.add_row(source.id, source.name, source.type.value, str(source.priority))

    console.print(table)

    # Run ingestion
    ingestion_service = IngestionService(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Ingesting sources...", total=None)

        try:
            results = await ingestion_service.ingest_sources(sources)
            progress.stop()

            # Display results
            console.print("\n📊 [bold]Ingestion Results:[/bold]")
            console.print(f"  Sources processed: {results['sources_processed']}/{len(sources)}")
            console.print(f"  Total items fetched: {results['total_items']}")

            if results['successful_sources']:
                console.print(f"  ✅ Successful: {', '.join(results['successful_sources'])}")

            if results['failed_sources']:
                console.print(f"  ❌ Failed: {', '.join(results['failed_sources'])}")

                for error in results['errors']:
                    console.print(f"    {error['source_id']}: {error['error']}")

            console.print(f"\n💾 Raw data saved to: {config.raw_dir}/{results['run_date']}/")

        except Exception as e:
            progress.stop()
            console.print(f"❌ [bold red]Ingestion failed:[/bold red] {e}")
            logger.exception("Ingestion failed")
            raise typer.Exit(1)
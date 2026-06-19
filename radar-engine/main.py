"""
Radar Engine - Dumb Fetcher

Python does dumb deterministic fetching. Claude does all the judgment and synthesis.
"""

import asyncio
import argparse
from pathlib import Path
from datetime import datetime

from .fetchers.enhanced import ParallelFetchOrchestrator


async def run():
    """Fetch from all sources, save raw data. That's it."""
    print("📡 Fetching from all sources...")

    fetcher = ParallelFetchOrchestrator(Path("sources"))
    results = await fetcher.fetch_all_sources()

    print(f"✅ Done — {results['total_items']} items from {len(results['source_results'])} sources")
    print(f"   Raw data saved to raw/{datetime.now().strftime('%Y-%m-%d')}/")

    await fetcher.close()
    return results


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Radar Engine - Fetch intelligence sources")
    parser.add_argument("command", choices=["run"], help="Command to execute")
    args = parser.parse_args()

    if args.command == "run":
        await run()


if __name__ == "__main__":
    asyncio.run(main())

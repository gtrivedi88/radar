"""
Main Radar Engine - Autonomous Intelligence Orchestrator
"""

import asyncio
import argparse
from pathlib import Path
from datetime import datetime

from .orchestration.autonomous import AutonomousOrchestrator
from .fetchers.enhanced import ParallelFetchOrchestrator


async def run_autonomous_intelligence():
    """Run a single cycle of autonomous intelligence processing"""
    print("🎯 Running autonomous intelligence cycle...")

    # Fetch from all sources
    fetcher = ParallelFetchOrchestrator(Path("sources"))
    results = await fetcher.fetch_all_sources()

    print(f"📊 Fetched {results['total_items']} items from {len(results['source_results'])} sources")

    # Process through autonomous orchestrator
    orchestrator = AutonomousOrchestrator(Path("state"))
    intelligence_results = await orchestrator.process_intelligence(results['all_items'])

    # Report results
    if intelligence_results['triggered_hooks']:
        print(f"🚨 {len(intelligence_results['triggered_hooks'])} strategic hooks triggered")

    if intelligence_results['loop_alerts']:
        print(f"🔄 {len(intelligence_results['loop_alerts'])} autonomous loops alerted")

    if results['threshold_alerts']:
        print("⚠️  Threshold alerts:")
        for alert in results['threshold_alerts']:
            print(f"   • {alert['source']}: {alert['thresholds']['high_engagement_count']} high-engagement items")

    await fetcher.close()

    return {
        "fetch_results": results,
        "intelligence_results": intelligence_results,
        "timestamp": datetime.now().isoformat()
    }


async def setup_autonomous_loops():
    """Set up default autonomous loops for strategic intelligence"""
    orchestrator = AutonomousOrchestrator(Path("state"))

    # Add strategic loops
    await orchestrator.add_loop(
        "Monitor HTML-first development trend. Track HN mentions >500 points. Alert when engagement suggests content opportunity.",
        "2d"
    )

    await orchestrator.add_loop(
        "Monitor Claude/AI tools performance discussions. Alert when community pain points reach actionable threshold.",
        "1w"
    )

    await orchestrator.add_loop(
        "Track technical writing + AI integration signals. Alert when course opportunity signals align.",
        "1w"
    )

    print("✅ Autonomous loops configured")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Radar Engine - Autonomous Intelligence")
    parser.add_argument("command", choices=["run", "setup-loops", "continuous"],
                       help="Command to execute")

    args = parser.parse_args()

    if args.command == "run":
        results = await run_autonomous_intelligence()
        print(f"\n✅ Autonomous intelligence cycle completed")

    elif args.command == "setup-loops":
        await setup_autonomous_loops()

    elif args.command == "continuous":
        print("🚀 Starting continuous autonomous intelligence...")
        orchestrator = AutonomousOrchestrator(Path("state"))
        await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
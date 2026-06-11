"""
Autonomous Intelligence Orchestrator
Manages loops, hooks, and threshold-triggered deep research
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from pathlib import Path
import json

from ..core.base import AutonomousLoop, StrategicHook, IntelligenceItem


class AutonomousOrchestrator:
    """Orchestrates autonomous intelligence loops and strategic hooks"""

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.loops: List[AutonomousLoop] = []
        self.hooks: List[StrategicHook] = []
        self.running = False

    async def add_loop(self, prompt: str, frequency: str, threshold_callback: Callable = None) -> str:
        """Add a new autonomous loop"""
        loop = AutonomousLoop(prompt, frequency, threshold_callback)
        self.loops.append(loop)

        # Save to state for persistence
        await self._save_loops_state()

        return f"loop-{len(self.loops)}"

    def add_hook(self, condition: str, action: str, description: str) -> str:
        """Add a strategic hook for threshold-triggered actions"""
        hook = StrategicHook(condition, action, description)
        self.hooks.append(hook)

        return f"hook-{len(self.hooks)}"

    async def process_intelligence(self, items: List[IntelligenceItem]) -> Dict[str, Any]:
        """Process intelligence through hooks and loops"""
        results = {
            "triggered_hooks": [],
            "loop_alerts": [],
            "deep_research_triggered": [],
            "sessionstart_hooks_processed": []
        }

        # 1. Read recent SessionStart hook alerts
        hook_alerts = await self._read_recent_hook_alerts()
        if hook_alerts:
            results["sessionstart_hooks_processed"] = hook_alerts

        # 2. Check internal hooks against new intelligence
        for hook in self.hooks:
            if await self._check_hook_condition(hook, items):
                results["triggered_hooks"].append({
                    "hook": hook.description,
                    "action": hook.action,
                    "timestamp": datetime.now().isoformat()
                })

        # 3. Update loop monitoring
        for loop in self.loops:
            if await self._evaluate_loop(loop, items):
                results["loop_alerts"].append({
                    "loop": loop.prompt,
                    "alert": "Threshold reached",
                    "timestamp": datetime.now().isoformat()
                })

        # 4. Check for course opportunity signals
        course_opportunity = self._analyze_course_opportunity(items)
        if course_opportunity:
            results["course_opportunity"] = course_opportunity

        # 5. Determine if deep research should be triggered
        high_engagement_items = [item for item in items if item.score > 1000]
        if high_engagement_items or hook_alerts or course_opportunity:
            results["deep_research_triggered"] = await self._trigger_deep_research(
                high_engagement_items, hook_alerts, course_opportunity
            )

        return results

    async def run_autonomous_cycle(self):
        """Run one cycle of autonomous intelligence processing"""
        if not self.running:
            return

        cycle_start = datetime.now()
        cycle_results = {
            "success": False,
            "loops_executed": 0,
            "items_processed": 0,
            "hooks_triggered": 0,
            "errors": []
        }

        try:
            # 1. Check which loops should run based on frequency
            loops_to_run = [loop for loop in self.loops if loop.should_run()]

            if not loops_to_run:
                # No loops scheduled to run
                cycle_results["success"] = True
                return cycle_results

            # 2. Fetch latest intelligence data
            from ..fetchers.enhanced import ParallelFetchOrchestrator
            from pathlib import Path

            fetcher = ParallelFetchOrchestrator(Path("sources"))
            fetch_results = await fetcher.fetch_all_sources()

            if fetch_results.get("error"):
                cycle_results["errors"].append(f"Fetch failed: {fetch_results['error']}")
                return cycle_results

            all_items = fetch_results.get("all_items", [])
            cycle_results["items_processed"] = len(all_items)

            # 3. Process intelligence through hooks and loops
            intelligence_results = await self.process_intelligence(all_items)
            cycle_results["hooks_triggered"] = len(intelligence_results.get("triggered_hooks", []))

            # 4. Update loop timestamps for executed loops
            for loop in loops_to_run:
                loop.last_run = cycle_start

            cycle_results["loops_executed"] = len(loops_to_run)

            # 5. Save state atomically
            await self._save_loops_state()

            # 6. Log cycle completion
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            await self._log_cycle_result({
                **cycle_results,
                "duration": cycle_duration,
                "timestamp": cycle_start.isoformat()
            })

            await fetcher.close()
            cycle_results["success"] = True

        except Exception as e:
            error_msg = f"Cycle error: {str(e)}"
            cycle_results["errors"].append(error_msg)
            await self._handle_cycle_error(e, cycle_start)

        return cycle_results

    async def _log_cycle_result(self, result: Dict[str, Any]):
        """Log autonomous cycle execution results"""
        # Create cycle log entry
        log_entry = {
            "type": "autonomous_cycle",
            **result
        }

        # Save to cycle log file
        cycle_log_file = self.state_dir / "autonomous_cycles.jsonl"
        try:
            # Simple append for now - will improve with atomic operations later
            with open(cycle_log_file, 'a') as f:
                f.write(json.dumps(log_entry, default=str) + "\n")
        except Exception as e:
            # Don't let logging failures break the cycle
            print(f"Warning: Failed to log cycle result: {e}")

    async def _handle_cycle_error(self, error: Exception, cycle_start: datetime):
        """Handle errors during autonomous cycle execution"""
        error_entry = {
            "type": "cycle_error",
            "error": str(error),
            "timestamp": cycle_start.isoformat(),
            "duration": (datetime.now() - cycle_start).total_seconds()
        }

        # Log error to dedicated error file
        error_log_file = self.state_dir / "autonomous_errors.jsonl"
        try:
            with open(error_log_file, 'a') as f:
                f.write(json.dumps(error_entry, default=str) + "\n")
        except Exception as log_error:
            # Don't let logging failures break error handling
            print(f"Critical: Failed to log cycle error: {log_error}")
            print(f"Original error: {error}")

        # Continue running - don't stop autonomous processing for single cycle errors
        print(f"Autonomous cycle error (continuing): {error}")

    async def _read_recent_hook_alerts(self) -> List[Dict[str, Any]]:
        """Read recent SessionStart hook alerts from threshold_alerts.jsonl"""
        alerts_file = self.state_dir / "threshold_alerts.jsonl"
        if not alerts_file.exists():
            return []

        try:
            recent_alerts = []
            with open(alerts_file, 'r') as f:
                for line in f:
                    if line.strip():
                        alert = json.loads(line.strip())
                        # Only consider alerts from the last hour
                        alert_time = datetime.fromisoformat(alert.get("timestamp", ""))
                        if (datetime.now() - alert_time).total_seconds() < 3600:
                            recent_alerts.append(alert)

            return recent_alerts[-5:]  # Return up to 5 most recent alerts

        except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
            print(f"Warning: Could not read hook alerts: {e}")
            return []

    async def _trigger_deep_research(self, high_engagement_items: List, hook_alerts: List, course_opportunity: Dict = None) -> List[Dict[str, Any]]:
        """Determine what deep research should be triggered"""
        research_triggers = []

        # Trigger research for high-engagement items
        for item in high_engagement_items:
            research_triggers.append({
                "type": "high_engagement",
                "item_title": getattr(item, 'title', 'Unknown'),
                "item_score": getattr(item, 'score', 0),
                "item_url": getattr(item, 'url', ''),
                "reason": f"High engagement ({getattr(item, 'score', 0)} points)",
                "recommended_action": "deep_research_contrarian_angles"
            })

        # Trigger research based on SessionStart hook alerts
        for alert in hook_alerts:
            if alert.get("analysis", {}).get("high_engagement"):
                research_triggers.append({
                    "type": "sessionstart_hook",
                    "alert_timestamp": alert.get("timestamp"),
                    "high_engagement_count": len(alert.get("analysis", {}).get("high_engagement", [])),
                    "reason": "SessionStart hook detected high engagement threshold",
                    "recommended_action": "synthesis_with_contrarian_focus"
                })

        # Trigger research based on course opportunity signals
        if course_opportunity:
            research_triggers.append({
                "type": "course_opportunity",
                "topic": course_opportunity.get("topic", "Unknown"),
                "overall_score": course_opportunity.get("overall_score", 0),
                "pain_strength": course_opportunity.get("pain_point_strength", 0),
                "reason": "Multi-signal course opportunity detected",
                "recommended_action": "course_validation_deep_dive"
            })

        return research_triggers

    def _analyze_course_opportunity(self, items: List) -> Optional[Dict[str, Any]]:
        """Analyze intelligence items for course opportunity using CourseOpportunityValidator"""
        try:
            from ..validators.course_opportunity import CourseOpportunityValidator

            validator = CourseOpportunityValidator()
            opportunity = validator.analyze_course_opportunity(items)

            if opportunity:
                # Convert CourseOpportunity to dict for JSON serialization
                return {
                    "topic": opportunity.topic,
                    "overall_score": opportunity.overall_score,
                    "pain_point_strength": opportunity.pain_point_strength,
                    "skill_gap_strength": opportunity.skill_gap_strength,
                    "economic_strength": opportunity.economic_strength,
                    "runway_strength": opportunity.runway_strength,
                    "course_outline": opportunity.course_outline,
                    "pricing_strategy": opportunity.pricing_strategy,
                    "launch_timeline": opportunity.launch_timeline,
                    "evidence_summary": opportunity.evidence_summary,
                    "timestamp": datetime.now().isoformat(),
                    "validation_status": "TRIGGERED - All thresholds met"
                }

            return None

        except ImportError as e:
            print(f"Warning: Course opportunity validator not available: {e}")
            return None
        except Exception as e:
            print(f"Error in course opportunity analysis: {e}")
            return None

    async def start(self):
        """Start autonomous intelligence processing"""
        self.running = True
        while self.running:
            try:
                await self.run_autonomous_cycle()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in autonomous cycle: {e}")
                await asyncio.sleep(60)

    async def stop(self):
        """Stop autonomous processing"""
        self.running = False

    async def _check_hook_condition(self, hook: StrategicHook, items: List[IntelligenceItem]) -> bool:
        """Check if a hook's condition is triggered by current intelligence"""
        # Example: Check if any item has score > 1000
        if "engagement > 1000" in hook.condition:
            return any(item.score > 1000 for item in items)

        return False

    async def _evaluate_loop(self, loop: AutonomousLoop, items: List[IntelligenceItem]) -> bool:
        """Evaluate if a loop should alert based on current intelligence"""
        # This would implement the loop's monitoring logic
        return False

    async def _save_loops_state(self):
        """Save current loops state for persistence"""
        state_file = self.state_dir / "autonomous-loops.json"
        state = {
            "loops": [
                {
                    "prompt": loop.prompt,
                    "frequency": loop.frequency,
                    "last_run": loop.last_run.isoformat() if loop.last_run else None,
                    "active": loop.active
                }
                for loop in self.loops
            ],
            "updated": datetime.now().isoformat()
        }

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
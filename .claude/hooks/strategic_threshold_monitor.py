#!/usr/bin/env python3
"""
Strategic Threshold Monitor Hook
Runs on SessionStart to check intelligence data for threshold triggers
Automatically executes actions when strategic thresholds are met
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def get_latest_intelligence_data():
    """Get the most recent intelligence data from radar state files"""

    # Check for latest raw intelligence data
    raw_dir = Path("raw")
    if not raw_dir.exists():
        return {"total_items": 0, "high_engagement": [], "framework_discussions": [], "ai_writing_tools": []}

    # Get latest date directory
    date_dirs = sorted([d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("2026")])
    if not date_dirs:
        return {"total_items": 0, "high_engagement": [], "framework_discussions": [], "ai_writing_tools": []}

    latest_dir = date_dirs[-1]

    # Aggregate data from latest intelligence gathering
    all_items = []

    # Load HackerNews data if available
    hn_file = latest_dir / "hackernews-trending.json"
    if hn_file.exists():
        try:
            with open(hn_file) as f:
                hn_data = json.load(f)
                if isinstance(hn_data, dict) and "hits" in hn_data:
                    all_items.extend(hn_data["hits"][:20])  # Top 20 items
        except Exception:
            pass

    return analyze_items_for_thresholds(all_items)


def analyze_items_for_thresholds(items):
    """Analyze intelligence items for strategic threshold signals"""

    high_engagement = []
    framework_discussions = []
    ai_writing_tools = []

    for item in items:
        title = item.get("title", "").lower()
        score = item.get("points", 0)

        # Threshold 1: High engagement items (>1000 points)
        if score > 1000:
            high_engagement.append({
                "title": item.get("title", ""),
                "score": score,
                "url": item.get("url", ""),
                "comments": item.get("num_comments", 0)
            })

        # Threshold 2: HTML-first/framework performance discussions
        framework_keywords = ["html-first", "html first", "vs react", "vs vue", "framework", "performance", "javascript bloat"]
        if any(keyword in title for keyword in framework_keywords) and score > 500:
            framework_discussions.append({
                "title": item.get("title", ""),
                "score": score,
                "url": item.get("url", ""),
                "keywords_matched": [kw for kw in framework_keywords if kw in title]
            })

        # Threshold 3: AI tools + technical writing intersection
        ai_writing_keywords = ["ai writing", "claude", "gpt", "documentation", "technical writing", "docs"]
        writing_keywords = ["writing", "documentation", "docs", "technical writing"]
        ai_keywords = ["ai", "claude", "gpt", "llm", "chatgpt"]

        has_ai = any(keyword in title for keyword in ai_keywords)
        has_writing = any(keyword in title for keyword in writing_keywords)

        if (has_ai and has_writing) or any(keyword in title for keyword in ai_writing_keywords):
            ai_writing_tools.append({
                "title": item.get("title", ""),
                "score": score,
                "url": item.get("url", ""),
                "ai_signals": [kw for kw in ai_keywords if kw in title],
                "writing_signals": [kw for kw in writing_keywords if kw in title]
            })

    return {
        "total_items": len(items),
        "high_engagement": high_engagement,
        "framework_discussions": framework_discussions,
        "ai_writing_tools": ai_writing_tools,
        "analysis_timestamp": datetime.now().isoformat()
    }


def trigger_deep_research(item):
    """Trigger deep research skill for high-engagement items"""

    research_prompt = f"""Analyze this high-engagement signal for contrarian opportunities:

    Title: {item['title']}
    Engagement: {item['score']} points, {item.get('comments', 0)} comments
    URL: {item['url']}

    Look for contrarian angles that oppose mainstream consensus, backed by evidence.
    Focus on what others are missing or getting wrong.
    Output specific action recommendations for Gaurav."""

    return {
        "action": "deep_research",
        "prompt": research_prompt,
        "reason": f"High engagement ({item['score']} points) indicates audience readiness"
    }


def trigger_radar_synthesis(discussions):
    """Trigger radar synthesis for framework discussions"""

    discussion_summary = "\n".join([
        f"- {d['title']} ({d['score']} points)"
        for d in discussions[:3]
    ])

    return {
        "action": "radar_synthesis",
        "prompt": f"Framework performance discussions trending:\n{discussion_summary}\n\nProvide specific post recommendation with 'Ship by Friday' urgency.",
        "reason": f"{len(discussions)} framework discussions show positioning opportunity"
    }


def trigger_course_analysis(ai_tools):
    """Trigger course opportunity analysis for AI writing tools"""

    tool_summary = "\n".join([
        f"- {tool['title']} ({tool['score']} points)"
        for tool in ai_tools[:3]
    ])

    return {
        "action": "course_analysis",
        "prompt": f"AI + technical writing signals detected:\n{tool_summary}\n\nAnalyze for course opportunity: community pain + skill gap + market timing + 6-month runway.",
        "reason": f"{len(ai_tools)} AI writing tool discussions suggest course opportunity"
    }


def execute_strategic_action(action):
    """Execute a strategic action using Claude Code skills"""

    if action["action"] == "deep_research":
        # Trigger deep-research skill
        message = f"🎯 HIGH-ENGAGEMENT SIGNAL DETECTED: Auto-triggering deep research\n\n{action['prompt']}"

    elif action["action"] == "radar_synthesis":
        # Trigger radar synthesis
        message = f"📊 FRAMEWORK DISCUSSION THRESHOLD MET: Auto-triggering radar analysis\n\n{action['prompt']}"

    elif action["action"] == "course_analysis":
        # Trigger course opportunity analysis
        message = f"📚 AI+WRITING SIGNALS CONVERGED: Auto-triggering course analysis\n\n{action['prompt']}"

    else:
        message = f"⚠️ Unknown action type: {action['action']}"

    return message


def main():
    """Main threshold monitoring logic"""

    try:
        # Get latest intelligence data
        analysis = get_latest_intelligence_data()

        # Check if any items exist
        if analysis["total_items"] == 0:
            return  # No data to analyze

        # Check thresholds and build action recommendations
        actions = []

        # Threshold 1: High engagement items (>1000 points)
        for item in analysis["high_engagement"]:
            actions.append(trigger_deep_research(item))

        # Threshold 2: Framework discussions
        if analysis["framework_discussions"]:
            actions.append(trigger_radar_synthesis(analysis["framework_discussions"]))

        # Threshold 3: AI writing tools intersection
        if len(analysis["ai_writing_tools"]) >= 2:  # Multiple signals = stronger opportunity
            actions.append(trigger_course_analysis(analysis["ai_writing_tools"]))

        # If actions triggered, output strategic alert with actionable message
        if actions:
            # Create system message that Claude will see
            messages = [execute_strategic_action(action) for action in actions]
            combined_message = "\n\n".join(messages)

            alert = {
                "systemMessage": combined_message,
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": f"Strategic intelligence thresholds triggered {len(actions)} autonomous actions. Review and execute as needed."
                },
                "analysis_summary": {
                    "total_items": analysis["total_items"],
                    "high_engagement_count": len(analysis["high_engagement"]),
                    "framework_discussions_count": len(analysis["framework_discussions"]),
                    "ai_writing_signals_count": len(analysis["ai_writing_tools"]),
                    "actions_triggered": len(actions)
                },
                "timestamp": datetime.now().isoformat()
            }

            print(json.dumps(alert))

            # Save threshold alerts for reference
            alerts_file = Path("state/threshold_alerts.jsonl")
            alerts_file.parent.mkdir(exist_ok=True)

            with open(alerts_file, "a") as f:
                f.write(json.dumps({
                    "analysis": analysis,
                    "actions": actions,
                    "timestamp": datetime.now().isoformat()
                }) + "\n")

        else:
            # Only show message if there's actually intelligence data but no thresholds
            if analysis["total_items"] > 0:
                quiet_alert = {
                    "systemMessage": f"📡 Intelligence monitoring active: {analysis['total_items']} items analyzed, no strategic thresholds triggered yet."
                }
                print(json.dumps(quiet_alert))

    except Exception as e:
        # Silent failure - don't break session start
        error_log = {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

        error_file = Path("state/hook_errors.jsonl")
        error_file.parent.mkdir(exist_ok=True)

        with open(error_file, "a") as f:
            f.write(json.dumps(error_log) + "\n")


if __name__ == "__main__":
    main()
---
name: autonomous-monitoring
description: Set up autonomous monitoring loops for emerging trends and opportunities
---

# Autonomous Monitoring

Create autonomous intelligence loops that monitor and alert on strategic opportunities without manual intervention.

## What This Enables

Instead of bi-weekly manual synthesis, create **persistent watchers** that:
- Monitor emerging trends continuously  
- Alert when opportunities reach action thresholds
- Research deeper when signals strengthen
- Track competitor movements automatically

## Loop Types

### 1. Trend Watcher Loops
```bash
# Monitor emerging trend until it peaks or dies
/loop 3d "Monitor HTML-first development trend. Track HN mentions, GitHub stars on HTML-first tools, job postings mentioning 'HTML-first'. Alert if engagement >2x baseline or competitors start covering it."
```

### 2. Course Opportunity Loops  
```bash
# Watch for course opportunity maturation
/loop 1w "Monitor Claude performance optimization signals. Track: community pain points, competitor courses, job market demand. Alert when 3+ signals align for course opportunity."
```

### 3. Competitive Intelligence Loops
```bash
# Track what key people in your space are doing
/loop 2d "Monitor activity from top technical writing influencers. Track new content, course launches, conference talks. Alert on positioning gaps or early trend adoption."
```

### 4. Infrastructure Signal Loops
```bash
# Watch for early infrastructure changes
/loop 1d "Monitor Anthropic/OpenAI API changes, new model capabilities, pricing changes. These predict developer workflow shifts 3-6 months early."
```

## Setting Up Loops

### Step 1: Identify What to Monitor
Based on your strategic goals:
- **For content positioning**: Early technical trends
- **For course timing**: Community pain + skill gaps  
- **For speaking**: Peak interest but pre-mainstream topics
- **For competitive advantage**: What others miss or start too late

### Step 2: Create Loop Prompts
```bash
# Template
/loop [frequency] "[specific monitoring task] + [threshold for action] + [what to research when triggered]"
```

### Step 3: Set Alert Thresholds
Define when loop should escalate to you:
- Engagement metrics (>2x baseline)
- Signal count (≥3 confirming sources)
- Competitor activity (someone starts covering it)
- Time-based (signal active >30 days)

## Advanced: Self-Researching Loops

When alerts trigger, loops should **automatically research deeper**:

```bash
/loop 5d "If HTML-first trend engagement >500 HN points OR >3 major blogs cover it, THEN: 1) Research competing content, 2) Analyze skill gap in market, 3) Draft content positioning options, 4) Present strategic recommendation with timeline"
```

## Loop Management

**Active loops** should be logged in:
```
state/active-loops.md
- Loop-001: HTML-first trend monitoring (started 2026-06-11, next check 2026-06-14)
- Loop-002: Claude performance course opportunity (started 2026-06-11, next check 2026-06-18)
```

## Success Metrics

**Elite autonomous monitoring**:
- Alerts you to opportunities 2-4 weeks before they become obvious
- Provides action-ready analysis (not just "something is happening")
- Tracks through complete lifecycle (emergence → peak → decline)
- Prevents missed opportunities due to manual checking cadence

This transforms Radar from **reactive digest tool** into **proactive strategic intelligence system**.
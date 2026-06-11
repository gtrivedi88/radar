---
name: strategic-hooks
description: Configure automated strategic intelligence triggers via Claude Code hooks
---

# Strategic Hooks

Set up automated triggers that fire when strategic thresholds are met, enabling autonomous intelligence amplification.

## Hook Types for Strategic Intelligence

### 1. Trend Threshold Hooks
Trigger when engagement metrics cross strategic thresholds:

```json
// In settings.json
{
  "hooks": {
    "postToolUse:Skill": {
      "when": "skill === 'radar' && signals.some(s => s.engagement_total > 1000)",
      "action": "Skill('deep-research', 'Research this high-engagement trend deeper: provide competitive analysis, market timing, content positioning options')"
    }
  }
}
```

### 2. Course Opportunity Hooks
Auto-research when multiple signals align:

```json
{
  "hooks": {
    "postToolUse:Skill": {
      "when": "skill === 'radar' && courseSignalCount >= 3",
      "action": "Skill('course-opportunity-analysis', 'Multi-signal course opportunity detected. Research: market size, competitor analysis, pricing strategy, launch timeline')"
    }
  }
}
```

### 3. Content Timing Hooks
Alert for optimal content creation windows:

```json
{
  "hooks": {
    "postToolUse:Skill": {
      "when": "skill === 'radar' && trendStage === 'forming' && competitorCoverage < 2",
      "action": "Alert: WRITE NOW opportunity detected. Trend forming with minimal competition. Draft content outline within 48h for maximum positioning advantage."
    }
  }
}
```

### 4. Weekly Deep Intelligence Hooks
Automated deeper analysis on weekly cycles:

```json
{
  "hooks": {
    "cron": {
      "schedule": "0 9 * * 1", // Mondays at 9am
      "action": "Skill('weekly-intelligence-amplification', 'Analyze week's signals for: 1) Emerging opportunities missed by manual review, 2) Trend acceleration patterns, 3) Competitive positioning gaps, 4) Strategic timing recommendations')"
    }
  }
}
```

## Strategic Alert System

### Immediate Action Triggers
- **Infrastructure change** (API updates, new models) → Research impact within 24h
- **High engagement contrarian signal** (>500 points, opposes consensus) → Investigate positioning angle
- **Competitor course launch** → Analyze gap opportunities within 48h

### Weekly Review Triggers  
- **Trend acceleration** (3+ week growth) → Deep market analysis
- **Multiple weak signals aligning** → Research for course opportunity
- **Community pain point amplification** → Content opportunity analysis

### Monthly Strategic Reviews
- **Prediction accuracy assessment** → Update forecasting methodology  
- **Positioning effectiveness review** → Analyze content performance vs predictions
- **Competitive landscape shift** → Update strategic positioning

## Implementation via Update-Config Skill

Use the `update-config` skill to set these up:

```bash
# Example: Set up trend threshold monitoring
Claude: "Configure a hook that triggers deep research when any HN story in our radar feed gets >1000 points"
```

This creates autonomous strategic intelligence that works **while you sleep**, catching opportunities before manual review cycles would find them.

## Elite Intelligence Characteristics

**Current state**: Manual bi-weekly synthesis
**Elite state**: Autonomous continuous intelligence with threshold-triggered deep research

**What elite looks like**:
- You wake up to analysis of overnight trend emergence
- Course opportunities are pre-researched when signals align
- Content timing recommendations appear when windows open
- Competitive gaps are flagged as they develop

This transforms Radar into a **24/7 strategic intelligence operator** instead of a manual tool you run occasionally.
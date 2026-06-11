# Autonomous Intelligence Features

Radar includes autonomous features that monitor intelligence signals and trigger actions when strategic thresholds are met. This creates a genuinely autonomous strategic intelligence system.

## Overview

The autonomous system operates on two levels:
1. **Strategic Hooks** - Real-time threshold monitoring
2. **Autonomous Loops** - Scheduled analysis and research

## Strategic Hooks

Strategic hooks run automatically when Claude Code starts and check for threshold-triggered opportunities.

### How It Works

1. **SessionStart Hook**: Runs `strategic_threshold_monitor.py` on every Claude session start
2. **Threshold Detection**: Analyzes latest intelligence data for strategic signals
3. **Auto-Actions**: When thresholds fire, shows specific action recommendations

### Threshold Conditions

#### Threshold 1: High Engagement (>1000 points)
- **Triggers**: Items with >1000 engagement points
- **Action**: Auto-triggers deep research analysis
- **Purpose**: Catches signals before they become obvious, identifies contrarian opportunities

#### Threshold 2: Framework Performance Discussions
- **Triggers**: HTML-first, framework performance, or "vs React" discussions >500 points
- **Action**: Radar synthesis with specific post timeline
- **Purpose**: Positioning opportunities when community is ready for contrarian takes

#### Threshold 3: AI + Technical Writing Convergence
- **Triggers**: 2+ signals combining AI tools with technical writing/documentation
- **Action**: Course opportunity analysis
- **Purpose**: Multi-signal validation before recommending major time investment

### Hook Output

When thresholds trigger, you'll see messages like:

```
🎯 HIGH-ENGAGEMENT SIGNAL DETECTED: Auto-triggering deep research

Title: HTML-First Beats React: Performance Data Nobody's Talking About
Engagement: 1065 points, 480 comments
URL: https://example.com

Look for contrarian angles that oppose mainstream consensus...
```

## Autonomous Loops

Autonomous loops run on scheduled intervals to provide regular intelligence analysis.

### Active Loops

You can see current loops with:
```bash
claude --list-cron
```

Example loops:
- **Every 6 hours**: Intelligence analysis on latest signals
- **Weekly Monday**: Contrarian signal hunt for opposing mainstream developer consensus  
- **Weekly Thursday**: Course opportunity validation for multi-signal opportunities

### Loop Configuration

Loops are configured using Claude Code's `CronCreate` feature:

```javascript
CronCreate({
  cron: "47 */6 * * *",  // Every 6 hours at :47
  prompt: "Use Gaurav intelligence analysis on latest signals...",
  recurring: true,
  durable: true
})
```

### Loop Types

1. **Intelligence Analysis Loops**: Regular synthesis and threshold checking
2. **Research Loops**: Deep-dive analysis when signals strengthen
3. **Opportunity Validation**: Course/content opportunity assessment

## Configuration

### Hook Configuration

Strategic hooks are configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/strategic_threshold_monitor.py",
            "timeout": 30,
            "statusMessage": "🎯 Checking strategic intelligence thresholds..."
          }
        ]
      }
    ]
  }
}
```

### Threshold Tuning

Modify thresholds in `.claude/hooks/strategic_threshold_monitor.py`:

```python
# Threshold 1: High engagement items
if score > 1000:
    high_engagement.append(item)

# Threshold 2: Framework discussions  
if any(keyword in title for keyword in framework_keywords) and score > 500:
    framework_discussions.append(item)
```

## Monitoring and Logs

### Threshold Alerts Log

All threshold triggers are logged to `state/threshold_alerts.jsonl`:

```json
{
  "analysis": {...},
  "actions": [...],
  "timestamp": "2026-06-11T10:30:00Z"
}
```

### Error Handling

Hook errors are silently logged to `state/hook_errors.jsonl` to prevent breaking Claude sessions:

```json
{
  "error": "Connection timeout",
  "timestamp": "2026-06-11T10:30:00Z"
}
```

## Psychology Calibration

The autonomous system is calibrated to your specific decision-making psychology:

### What It Looks For
- **Contrarian signals**: Catches what others miss
- **Evidence-backed opportunities**: Only triggers on real engagement data  
- **Specific actions**: "Ship by Friday" not "consider exploring"
- **Your beat focus**: AI tools + technical writing + workflows
- **Effort-calibrated**: 4-hour posts, not 40-hour research projects

### What It Filters Out
- Obvious takes everyone's covering
- Generic AI applications
- Late-to-party topics  
- Generic "business" audience content
- Abstract strategy without implementation

## Advanced Features

### Recursive Research Loops

When signals strengthen, loops can auto-research deeper:

```bash
# If HTML-first signal strengthens (>2000 engagement), auto-research:
# - Performance benchmarks
# - Developer adoption data  
# - Framework comparison metrics
# Output: Complete post outline + evidence package
```

### Multi-Signal Correlation

The system tracks signal correlation across sources:
- Cross-validates signals across multiple channels
- Detects early-stage trends before they become obvious
- Identifies contrarian opportunities with strong evidence

### Prediction Accuracy Tracking

Autonomous loops track prediction accuracy over time:
- Log predictions with confidence levels
- Measure accuracy vs actual outcomes
- Auto-tune analysis based on historical performance

## Customization

### Adding New Thresholds

To add custom threshold conditions:

1. **Edit the monitor script**: `.claude/hooks/strategic_threshold_monitor.py`
2. **Add detection logic**: New threshold condition
3. **Define action**: What to do when threshold fires
4. **Test**: Run manually to verify detection

### Custom Loop Prompts

Create domain-specific loops for your beat:

```javascript
CronCreate({
  cron: "0 9 * * 1",  // Monday 9am
  prompt: "Analyze Claude Code workflow innovations from past week. Look for productivity patterns worth documenting.",
  recurring: true
})
```

## Elite Intelligence Flow

```
Sources → Raw Data → Strategic Hooks → Threshold Detection → Auto Actions
                ↓
         Scheduled Loops → Regular Analysis → Digest Creation
                ↓
            Memory Update → State Persistence → Learning
```

This creates genuinely autonomous strategic intelligence that works exactly like your brain when you're at your best - obsessive about quality, allergic to obvious takes, focused on actionable specifics with contrarian angles.
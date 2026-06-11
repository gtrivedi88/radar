# State Management

Radar's memory system uses simple markdown files to maintain context across synthesis runs. This approach keeps state human-readable and easily editable while providing sophisticated memory-aware intelligence.

## State File Overview

All state files live in the `state/` directory:

```
state/
├── profile.md          # Your identity, beat, and preferences
├── catalog.md          # Published work (prevents duplicates)
├── trajectory.md       # Current projects and learning queue
├── feedback.md         # Feedback on past digest items
├── signals.jsonl       # Signal observations for trend computation
├── threshold_alerts.jsonl  # Autonomous threshold trigger log
└── archive/           # Past digests for reference
    ├── radar-2026-06-11.md
    └── radar-2026-06-11-v2.md
```

## Core State Files

### profile.md - Your Intelligence Profile

This is your identity and preferences that guide all synthesis:

```markdown
# Operator Profile

## Identity
- Name: Gaurav Trivedi
- Current role: Technical Creator & AI Intelligence Analyst
- Audiences served: tech_writer, devs_curious_ai, hardcore_tech
- Voice DNA: cinematic, visceral, confrontational, philosophical

## Beat (what I write/teach about)
- AI-for-tech-writers craft and workflow
- Claude Code .md-driven development
- AI tool stacks for non-coders
- Tech writer career evolution under AI

## Topics done / bored of
- Generic "AI will replace writers" takes
- Tool-roundup posts without opinion
- Surface-level AI integration guides
```

**Usage**: Claude reads this for every synthesis to ensure recommendations match your voice, beat, and interests.

### catalog.md - Published Work Registry

Prevents duplicate topic suggestions:

```markdown
# Published Work

## Blog Posts (sorted by date, most recent first)
- 2026-06-01 | Building Elite Intelligence Systems | /elite-intelligence-systems/
- 2026-05-15 | Claude Code Workflow Optimization | /claude-code-workflows/

## Courses
- (empty — no courses launched yet)

## Talks & Presentations  
- 2026-03-12 | AI Tools for Technical Writers | DevWriters Conference
```

**Usage**: Synthesis automatically excludes topics substantially covered here.

### trajectory.md - Active Learning & Projects

Tracks what you're currently working on and what's queued:

```markdown
# Trajectory

## Doing (started, in flight)
- 2026-05-28 | Radar v0 implementation | Building world-class personal intelligence system

## Queued (interested, not started)  
- Elite Claude Code workflow patterns
- Advanced predictive intelligence methodologies

## Passed (explored, decided no)
- Generic AI writing tool comparisons

## Finished (done and useful)
- Personal knowledge management automation research
```

**Usage**: 
- Items in "Doing" get priority in synthesis
- "Queued" items receive 2x boost for relevance scoring
- "Passed" items are filtered out of recommendations

### feedback.md - Item Feedback Loop

Tracks your responses to past digest recommendations:

```markdown
# Feedback Log

2026-06-11 | item-html-first | Doing | Perfect contrarian angle, writing the post
2026-06-10 | item-ai-tools | Pass | Too generic, doesn't match my voice
2026-06-10 | item-claude-perf | Watch | Interesting but too early to act
```

**Status Definitions:**
- **Doing**: Actively pursuing this topic/opportunity
- **Pass**: Explicitly rejecting (won't reconsider)  
- **Done**: Completed/acted upon
- **Watch**: Monitor for future development

**Usage**: Synthesis filters out "Pass" items and boosts topics similar to "Doing" items.

### signals.jsonl - Trend Computation

Stores signal observations for trend direction analysis:

```json
{"date": "2026-06-11", "theme": "html_first_development", "source_count": 1, "engagement_total": 1545}
{"date": "2026-06-11", "theme": "claude_performance_scrutiny", "source_count": 1, "engagement_total": 664}
{"date": "2026-06-10", "theme": "html_first_development", "source_count": 1, "engagement_total": 1065}
```

**Usage**: 
- Calculates trend direction (↑/↓/→) by comparing engagement over time
- Identifies emerging vs fading themes
- Powers the "Counter-Signal" section (what's cooling off)

## Memory-Aware Synthesis

The `/radar` command integrates all state for intelligent synthesis:

### Memory Integration Logic

1. **Profile Filtering**: Only surfaces content matching your beat and audiences
2. **Catalog Deduplication**: Excludes topics you've substantially covered  
3. **Trajectory Boosting**: Gives 2x weight to items related to active projects
4. **Feedback Learning**: Filters out "Pass" items, boosts similar to "Doing"
5. **Trend Analysis**: Uses signals.jsonl to compute trend directions

### Quality Thresholds

Memory-aware quality gates prevent noise:

- **Trends require**: ≥3 source presence AND delta vs last digest
- **Course suggestions**: Multi-signal evidence across sources
- **Counter-signals**: At least 2 fading items per digest to prevent tunnel vision

## State File Updates

### Automated Updates

During synthesis, Claude automatically:
- **Appends to signals.jsonl**: New theme observations with engagement
- **Creates archive file**: `state/archive/radar-YYYY-MM-DD.md`

### Manual Updates

You should manually update:
- **profile.md**: When your beat or interests evolve
- **catalog.md**: When you publish new content  
- **trajectory.md**: As projects progress (Doing → Finished, add new Queued)
- **feedback.md**: Mark digest items as Doing/Pass/Done/Watch

### Feedback Loop Integration

After each digest, Claude asks:
> "Mark anything Doing? Provide item-id for trajectory update."

This creates a feedback loop where your actions teach the system your preferences.

## State Persistence Strategy

### What Gets Tracked
- **Long-term memory**: Profile, beat, published work
- **Medium-term**: Active projects, learning queue, preferences
- **Short-term**: Recent signals, trend directions
- **Immediate**: Current digest items and feedback

### What Gets Archived  
- **Past digests**: Full archive for reference and trend comparison
- **Signal history**: For trend computation and prediction accuracy
- **Threshold alerts**: For autonomous system tuning

### What Gets Cleaned
- **Raw data**: Fetched JSON is ephemeral (`raw/` in .gitignore)
- **Intermediate processing**: Temporary analysis files
- **Hook logs**: Error logs older than 30 days

## Advanced Memory Features

### Cross-Digest Learning

The system learns your preferences across digests:
- Tracks which item types you consistently choose "Doing" vs "Pass"
- Identifies your engagement patterns with different content types
- Adapts recommendation scoring based on historical feedback

### Trend Memory

Signal tracking enables sophisticated trend analysis:
- **Momentum detection**: Themes gaining/losing engagement over time
- **Cycle identification**: Recurring patterns in your beat areas
- **Early-stage signals**: Emerging themes before they hit mainstream

### Autonomous Memory Integration  

Strategic hooks use state for threshold tuning:
- **Profile-aware thresholds**: Higher/lower based on your interests
- **Historical context**: Considers past engagement with similar signals
- **Feedback-driven tuning**: Adjusts sensitivity based on your responses

## Memory Maintenance

### Weekly Maintenance
- Review trajectory.md and move completed items to "Finished"
- Update catalog.md with any published content
- Clean up old threshold_alerts.jsonl entries

### Monthly Maintenance  
- Review profile.md for beat evolution
- Archive old digest files you no longer need to reference
- Clean up signals.jsonl if it gets too large (keep last 90 days)

### Quarterly Review
- Analyze feedback.md patterns to tune your profile
- Review prediction accuracy in signals for system improvements
- Update beat focus based on what you're actually writing about

This state system creates persistent, evolving intelligence that gets smarter about your preferences and beat over time.
# Radar — Autonomous Intelligence System

**Radar** is Gaurav's personal autonomous intelligence system that monitors signals across AI tools, technical writing, and developer workflows to identify opportunities for content, courses, and strategic positioning.

## Philosophy

**Python does deterministic fetching, Claude provides autonomous intelligence.**

- Radar-engine fetches data and runs autonomous analysis
- ALL intelligence synthesis happens through Claude Code integration
- Autonomous loops monitor thresholds and trigger actions
- State and memory persist across intelligence cycles

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.lock

# Or use development setup
make install-dev
```

### Basic Usage

```bash
# Run single intelligence cycle
python -m radar-engine run

# Set up autonomous monitoring loops  
python -m radar-engine setup-loops

# Run continuous autonomous intelligence
python -m radar-engine continuous
```

### Integration with Claude Code

The system integrates with Claude Code for synthesis:

```bash
# In Claude Code, trigger synthesis
/radar

# Or use autonomous synthesis (triggered automatically by thresholds)
```

## Features

### 🎯 **Autonomous Intelligence**
- Real-time threshold monitoring via SessionStart hooks
- Scheduled intelligence loops (2d, 1w intervals)
- Multi-signal course opportunity detection
- Strategic hook system for contrarian positioning

### 📊 **Intelligence Sources**
- Hacker News (high-engagement content)
- Anthropic Blog (capability updates)
- Extensible YAML-based source configuration

### 🧠 **Memory & State**
- Cross-run memory via markdown state files
- Intelligence signal tracking (`state/signals.jsonl`)
- Autonomous loop state (`state/autonomous-loops.json`)
- Threshold alert history (`state/threshold_alerts.jsonl`)

### 🚀 **Course Opportunity Validator**
- Multi-signal analysis (pain points + skill gaps + economic demand)
- Automatic course outline + pricing + timeline generation
- Beat-specific focus: AI tools + technical writing + workflows
- Triggers when all thresholds met (>50 pain mentions, clear skill gap, economic demand, 6-month runway)

## Architecture

```
Sources (YAML configs) → Radar Engine → Autonomous Analysis → Claude Synthesis
                             ↓
                        State Persistence
```

### Key Components

- **`radar-engine/`** - Autonomous intelligence orchestration
- **`sources/`** - YAML source configurations  
- **`state/`** - Memory and state persistence
- **`.claude/hooks/`** - Real-time threshold monitoring
- **Tests** - Comprehensive test coverage for autonomous components

## Development

```bash
# Run tests
make test

# Update dependencies  
make update-deps

# Test autonomous cycle
make test-autonomous
```

## State Files

- **`state/profile.md`** - User identity and beat definition
- **`state/catalog.md`** - Published work (prevents topic duplication)
- **`state/trajectory.md`** - Learning queue and active projects
- **`state/feedback.md`** - Item feedback from past digests
- **`state/signals.jsonl`** - Intelligence signal observations
- **`state/autonomous-loops.json`** - Scheduled intelligence loops
- **`state/threshold_alerts.jsonl`** - Hook trigger history

## Autonomous Monitoring

Radar continuously monitors for:

### High-Engagement Signals
- HN posts >1000 points
- Framework performance discussions >500 points  
- AI + technical writing convergence signals

### Course Opportunities
- Community pain points (>50 mentions)
- Skill gaps (no quality content)
- Economic demand (job postings, salary data)
- 6-month runway confidence

### Strategic Positioning
- Contrarian angles on trending topics
- Early capability signals from AI companies
- Technical writing + AI tool intersection opportunities

## Intelligence Flow

1. **Fetch** - Parallel source collection (`ParallelFetchOrchestrator`)
2. **Analyze** - Multi-signal processing through autonomous hooks
3. **Trigger** - Threshold-based action recommendations  
4. **Synthesize** - Claude Code integration for intelligence digests
5. **Persist** - State and memory updates for next cycle

## Configuration

### Adding Sources

Create YAML files in `sources/`:

```yaml
id: new-source
name: "New Intelligence Source"
type: json_api  # or rss
enabled: true

config:
  endpoint: "https://api.example.com/data"
  query_params:
    limit: 20

signal_type: ["trend", "news"]
audience_tags: ["devs_curious_ai"]
```

### Autonomous Loops

Configure in `state/autonomous-loops.json` or via:

```bash
python -m radar-engine setup-loops
```

## Integration

- **Claude Code** - `/radar` synthesis command and autonomous triggers
- **OpenClaw** - Future cloud deployment (containerized)
- **CI/CD** - Automated testing and quality gates (GitHub Actions ready)

---

**Radar transforms raw intelligence into actionable strategic insight through autonomous monitoring and Claude synthesis.**
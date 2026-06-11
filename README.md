# Radar — Personal Intelligence System

**Radar** is an autonomous intelligence system that synthesizes signals across AI, dev tools, technical writing, and creator economy to produce bi-weekly action-oriented intelligence digests.

## Philosophy

**Python does dumb deterministic fetching, Claude does all the judgment and synthesis.**

- Python scripts fetch data from APIs and store as JSON files
- ALL intelligence happens in Claude via the `/radar` synthesis command  
- No complex prediction algorithms in Python - just simple data collection
- Memory and state management through simple markdown files

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure sources**:
   ```bash
   cp sources/hn-algolia.yaml.example sources/hn-algolia.yaml
   # Edit with your preferences
   ```

3. **Fetch intelligence data**:
   ```bash
   python scripts/fetch_sources.py
   ```

4. **Generate digest**:
   ```bash
   # In Claude Code:
   /radar
   ```

## Architecture

```
Sources (YAML configs) → Python Fetchers → Raw JSON → `/radar` → Digest
                                                         ↑
                                                    State Files
```

This keeps complexity in Claude (reasoning) not Python (plumbing).

## Core Components

### Sources
- **Configuration**: YAML files in `sources/` directory
- **Types**: JSON APIs, RSS feeds, web scraping
- **Extensible**: Drop a new YAML file, no code changes needed

### State Management
- **`state/profile.md`**: Who you are, your beat, audiences, current focus
- **`state/catalog.md`**: Published work (prevents duplicate suggestions)
- **`state/trajectory.md`**: Current learning, queued items, completed work
- **`state/feedback.md`**: Feedback on past digest items (Doing/Pass/Done/Watch)
- **`state/signals.jsonl`**: Signal observations for trend computation

### Autonomous Intelligence
- **Strategic Hooks**: Claude Code hooks that monitor for threshold-triggered opportunities
- **Autonomous Loops**: CronCreate jobs that run analysis on schedule
- **Threshold Detection**: Automatically alerts when signals reach strategic importance

## Documentation

- [Setup Guide](docs/setup.md) - Complete installation and configuration
- [Adding Sources](docs/adding-sources.md) - How to configure new intelligence sources
- [Autonomous Features](docs/autonomous-features.md) - Strategic hooks and loops
- [State Management](docs/state-management.md) - Understanding the memory system
- [Customization](docs/customization.md) - Adapting Radar to your beat and voice

## Features

### ✅ **Current (v1)**
- Multi-source data fetching (HN, RSS, APIs)
- Memory-aware synthesis via Claude
- State persistence across runs
- Strategic threshold monitoring
- Autonomous loop scheduling

### 🚧 **Planned (v2)**
- More source types (GitHub, Twitter, Discord)
- Advanced prediction accuracy tracking
- Multi-model synthesis comparison
- Enhanced autonomous research triggers

## Beat Territory

Radar is designed for technical creators focused on:
- AI tooling for technical writers
- Claude Code workflows  
- Developer experience
- Technical writing career evolution
- AI integration patterns for non-coders

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding sources, improving synthesis, and extending autonomous capabilities.

---

**Built with**: Python for fetching, Claude for intelligence, markdown for state.
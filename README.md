# Radar — Personal Intelligence System

**Radar** is Gaurav's personal intelligence system. Python fetches data from sources. Claude synthesizes it into actionable intelligence.

## Quick Start

```bash
pip install -r requirements.lock

# Fetch from all sources
python -m radar-engine run

# Synthesize with Claude (in Claude Code)
/radar
```

## How It Works

```
sources/*.yaml → python fetcher → raw/YYYY-MM-DD/*.json → Claude /radar → digest
                 (dumb)                                     (intelligence)
```

1. **Fetch**: `python -m radar-engine run` pulls from 5 sources in parallel (~1 second), deduplicates, saves raw JSON
2. **Synthesize**: `/radar` command in Claude reads raw data + state files, produces a 10-section digest with trends, pain points, course opportunities, and content angles

## Sources (5 active)

| Source | What it covers |
|--------|---------------|
| HN Front Page | High-engagement tech signals |
| HN Anthropic | Claude/Anthropic ecosystem |
| Dev.to AI | Developer AI practitioner content |
| Dev.to Writing | Technical writing community |
| Dev.to DevOps | AI + workflow intersection |

Add a source by dropping a YAML file in `sources/`. No code changes needed.

## State Files

| File | Purpose |
|------|---------|
| `state/profile.md` | Beat, audiences, voice |
| `state/catalog.md` | Published work (no re-suggestions) |
| `state/trajectory.md` | Active/queued projects |
| `state/signals.jsonl` | Theme observations across runs |
| `state/archive/` | Past digests |

## Development

```bash
make test          # Run tests
make install-dev   # Dev setup
```

## Architecture

Python is deliberately dumb — it handles HTTP, JSON, file I/O. All intelligence (relevance, themes, pain points, courses, trends) is Claude's job via `/radar`. See `CLAUDE.md` for full details.

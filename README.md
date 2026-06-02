# Radar: Personal Intelligence System

Bi-weekly capability & opportunity intelligence for technical creators. Built on modular, configuration-driven architecture that scales from 1 source (v0) to 80+ sources (v2) without core logic changes.

## Architecture

```
Core Logic ← Adapters ← Services ← Interface
     ↑           ↑         ↑         ↑
  Business   External   Use Cases   CLI/Web
   Models   Integrations            
```

**Design Principles:**
- **Configuration Over Code**: Add sources via YAML, zero code changes
- **Pluggable Fetchers**: Auto-discovery system, fetcher registry  
- **Async-First**: Built for v1 parallelization from day 1
- **State Abstraction**: Clean persistence with versioned schemas
- **Testing Isolation**: Every layer unit testable

## Quick Start

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Configure API keys

# v0: Single source ingestion
python -m radar ingest

# Synthesis (in Claude Code session)
/radar
```

## Scaling Path

- **v0** (Week 1): 1 source, manual inbox, end-to-end MRR
- **v1** (Week 2-3): 10 sources, async ingestion, cron automation  
- **v2** (Month 2+): 80+ sources, plugin system, full intelligence

Same core architecture, different configuration depth.

## Development

```bash
# Test suite
pytest

# Add new source
cp sources/hn-algolia.yaml sources/new-source.yaml
# Edit config → automatic discovery

# Add new fetcher
# Implement BaseFetcher → automatic registry
```

See `docs/` for detailed architecture and implementation notes.
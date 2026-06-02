# Radar v0: Modular Architecture Implementation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build highly modular v0 foundation that scales seamlessly to v1 (10 sources) and v2 (80+ sources)

**Architecture:** Abstraction-first design with pluggable components, configuration-driven scaling, and clean separation of concerns

**Tech Stack:** Python 3.11+, pydantic (config), httpx (async), PyYAML (sources), pytest (testing), GitHub Actions (automation)

**Reference Foundation:** `horizon-base/` (read-only reference, never edit directly)

---

## Core Design Principles

1. **Configuration Over Code**: Add new sources = drop YAML file, zero code changes
2. **Pluggable Fetchers**: Abstract base → concrete implementations, auto-registry
3. **Layered Architecture**: Core → Adapters → Sources → Synthesis 
4. **State Abstraction**: Clean state management with versioned schemas
5. **Async-First**: Built for v1 parallelization from day 1
6. **Testing Isolation**: Every component unit testable in isolation

## Modular File Structure

```
radar/
├── pyproject.toml                       # T1 — deps, async-ready
├── README.md                            # T1 — usage + architecture
├── .env.example                         # T1 — config template
├── radar/                               # Main package
│   ├── __init__.py                      # T1 — version, exports
│   ├── core/                            # T2 — business logic abstraction
│   │   ├── __init__.py
│   │   ├── models.py                    # Pydantic models, state schemas
│   │   ├── state_manager.py             # State persistence abstraction
│   │   ├── orchestrator.py             # Main coordination logic
│   │   └── synthesis.py                # MRR synthesis interface
│   ├── adapters/                        # T3 — external system adapters
│   │   ├── __init__.py
│   │   ├── fetchers/                    # Pluggable fetcher system
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Abstract fetcher interface
│   │   │   ├── registry.py              # Auto-discovery system
│   │   │   └── json_api.py             # v0: HN Algolia implementation
│   │   ├── sources/                     # Source configuration system
│   │   │   ├── __init__.py
│   │   │   ├── loader.py               # YAML source loader
│   │   │   └── validator.py            # Source validation
│   │   └── storage/                     # Storage abstractions
│   │       ├── __init__.py
│   │       ├── file_storage.py         # File-based state storage
│   │       └── schemas.py              # Storage schema versions
│   ├── services/                        # T4 — application services
│   │   ├── __init__.py
│   │   ├── ingestion.py                # Source ingestion service
│   │   ├── prefilter.py                # Signal filtering service
│   │   └── git_ops.py                  # Git operations (R12)
│   └── cli/                            # T5 — command line interface
│       ├── __init__.py
│       ├── main.py                     # Entry points
│       └── commands/                   # Individual CLI commands
│           ├── __init__.py
│           ├── ingest.py               # python -m radar ingest
│           └── persist.py              # python -m radar persist-signal
├── sources/                            # T6 — configuration layer
│   ├── _config.yaml                    # Global source configuration
│   ├── _groups.yaml                    # Source grouping for MRR
│   └── hn-algolia.yaml                 # v0: Single source
├── state/                              # T7 — state layer (operator editable)
│   ├── profile.md                      # Operator identity
│   ├── catalog.md                      # Published work
│   ├── trajectory.md                   # Learning trajectory
│   ├── feedback.md                     # Item feedback
│   ├── predictions.jsonl              # Elite intelligence: predictions
│   ├── inflection-watch.md             # Elite intelligence: S-curve monitoring
│   ├── market-sentiment.md             # Elite intelligence: sentiment tracking
│   ├── signals.jsonl                   # Observation log (append-only)
│   ├── watermarks.json                 # Fetcher success tracking
│   ├── fetch-errors.jsonl              # Error log
│   └── archive/.gitkeep                # Digest archive
├── .claude/commands/                   # T8 — Claude Code integration
│   ├── radar.md                        # Enhanced MRR synthesis
│   └── radar-section.md                # v2: Per-section regeneration
├── tests/                              # T9 — comprehensive testing
│   ├── conftest.py                     # Test configuration
│   ├── unit/                           # Unit tests per component
│   │   ├── test_models.py
│   │   ├── test_state_manager.py
│   │   ├── test_fetchers.py
│   │   └── test_orchestrator.py
│   ├── integration/                    # Integration tests
│   │   ├── test_ingestion_flow.py
│   │   └── test_synthesis_flow.py
│   └── fixtures/                       # Test data
│       ├── sample_sources/
│       └── mock_responses/
├── scripts/                            # T10 — deployment/automation
│   ├── setup.py                        # Environment setup
│   └── migrate.py                      # State schema migration
├── .github/workflows/                  # T11 — automation
│   └── ingest.yml                      # Cron ingestion
├── raw/.gitkeep                        # Runtime data (gitignored)
├── intermediate/.gitkeep               # MRR intermediate (gitignored)
└── horizon-base/                       # Reference only (never edit)
```

## Abstraction Layers

### Layer 1: Core Business Logic
**Purpose**: Framework-agnostic business logic
**Components**: Models, State Management, Orchestration
**Testing**: Pure unit tests, no external dependencies

### Layer 2: Adapters
**Purpose**: Interface with external systems (APIs, files, Git)
**Components**: Fetchers, Storage, Source Loading
**Testing**: Mock all external calls, test adapter logic

### Layer 3: Services  
**Purpose**: Coordinate core + adapters for use cases
**Components**: Ingestion, Filtering, Git Operations
**Testing**: Integration tests with real-ish data

### Layer 4: Interface
**Purpose**: CLI, Claude Code commands, web APIs
**Components**: CLI commands, slash commands
**Testing**: End-to-end behavior validation

## Pluggable Fetcher System

### Auto-Discovery Registry

```python
# radar/adapters/fetchers/registry.py
class FetcherRegistry:
    """Auto-discovers fetchers by source type + ID"""
    
    @classmethod
    def get_fetcher(cls, source_config: SourceConfig) -> Type[BaseFetcher]:
        # v0: Direct mapping
        # v1: Plugin discovery via entry points
        # v2: Dynamic loading from fetcher packages
```

### v0 → v1 → v2 Evolution

**v0**: Hard-coded registry (1 fetcher)
**v1**: Entry points discovery (10 fetchers)  
**v2**: Plugin packages (80+ fetchers)

No core logic changes required.

## Configuration-Driven Scaling

### Source Addition Process
1. **v0**: Drop YAML → works
2. **v1**: Drop YAML → fetcher auto-discovered → works
3. **v2**: Drop YAML → plugin auto-discovered → works

### MRR Group Evolution
**v0**: 1 group (manual inbox)
**v1**: 5 groups (thematic)
**v2**: 15 groups (full taxonomy)

Same synthesis logic, different configuration.

---

# Implementation Tasks

## Task 1: Modular Project Bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.env.example`
- Create: `radar/__init__.py`
- Create: `radar/core/__init__.py`
- Create: `radar/adapters/__init__.py`
- Create: `radar/services/__init__.py`
- Create: `radar/cli/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write modular `pyproject.toml`**

```toml
[project]
name = "radar"
version = "0.1.0"
description = "Personal capability & opportunity intelligence system"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",         # Async HTTP client
    "pydantic>=2.9.0",       # Configuration & validation
    "pydantic-settings>=2.5.0",  # Environment config
    "python-dateutil>=2.9.0",    # Date handling
    "pyyaml>=6.0.2",         # Source configuration
    "tenacity>=9.0.0",       # Retry logic
    "rich>=13.9.0",          # CLI formatting
    "typer>=0.12.0",         # CLI framework
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "httpx[dev]>=0.27.0",    # MockTransport for testing
    "ruff>=0.6.0",           # Linting/formatting
]

[project.scripts]
radar = "radar.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra -q --tb=short"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
extend-select = ["I", "N", "UP", "RUF"]
```

- [ ] **Step 2: Write architecture-focused `README.md`**

```markdown
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
```

- [ ] **Step 3: Write `.env.example`**

```bash
# API Keys (optional for v0)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# Configuration
RADAR_LOG_LEVEL=INFO
RADAR_DATA_DIR=./state
RADAR_SOURCES_DIR=./sources

# v2: Plugin Configuration
RADAR_PLUGINS_DIR=./plugins
RADAR_CACHE_TTL=300
```

- [ ] **Step 4: Create modular package structure**

`radar/__init__.py`:
```python
"""Radar: Personal Intelligence System"""

__version__ = "0.1.0"
__author__ = "Gaurav Trivedi"

# Core exports for clean imports
from .core.models import SourceConfig, SourceType
from .core.state_manager import StateManager
from .core.orchestrator import RadarOrchestrator

__all__ = [
    "SourceConfig",
    "SourceType", 
    "StateManager",
    "RadarOrchestrator",
]
```

`radar/core/__init__.py`:
```python
"""Core business logic layer"""

from .models import SourceConfig, SourceType, RadarConfig
from .state_manager import StateManager
from .orchestrator import RadarOrchestrator

__all__ = [
    "SourceConfig",
    "SourceType",
    "RadarConfig", 
    "StateManager",
    "RadarOrchestrator",
]
```

`radar/adapters/__init__.py`:
```python
"""External system adapters"""

from .fetchers import FetcherRegistry, BaseFetcher
from .sources import SourceLoader
from .storage import FileStorage

__all__ = [
    "FetcherRegistry",
    "BaseFetcher",
    "SourceLoader", 
    "FileStorage",
]
```

`radar/services/__init__.py`:
```python
"""Application services layer"""

from .ingestion import IngestionService
from .prefilter import PrefilterService
from .git_ops import GitOpsService

__all__ = [
    "IngestionService",
    "PrefilterService",
    "GitOpsService",
]
```

`radar/cli/__init__.py`:
```python
"""Command line interface"""

from .main import app

__all__ = ["app"]
```

`tests/conftest.py`:
```python
"""Test configuration and fixtures"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import MockTransport

from radar.core.models import SourceConfig, SourceType, PreFilter


@pytest.fixture
def temp_radar_root(tmp_path: Path) -> Path:
    """Isolated radar environment for testing"""
    for subdir in ("state", "sources", "raw", "intermediate"):
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def sample_source_config() -> SourceConfig:
    """Standard test source configuration"""
    return SourceConfig(
        id="test-source",
        name="Test Source",
        type=SourceType.json_api,
        config={"endpoint": "https://api.example.com"},
        poll_cadence="daily",
        signal_type=["news"],
        audience_tags=["test"],
        pre_filter=PreFilter(),
        priority=1,
    )


@pytest.fixture
def mock_transport() -> MockTransport:
    """HTTP mock transport for testing"""
    def handler(request):
        return httpx.Response(200, json={"test": "data"})
    return MockTransport(handler)


@pytest.fixture(scope="session")
def event_loop():
    """Provide event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

- [ ] **Step 5: Verify package structure**

```bash
python -c "import radar; print(radar.__version__)"
python -c "from radar import SourceConfig; print('✓ Modular imports work')"
pytest --collect-only  # Should show 0 tests but no import errors
```

- [ ] **Step 6: Commit modular foundation**

```bash
git add pyproject.toml README.md .env.example radar/ tests/conftest.py
git commit -m "feat(v0): modular architecture foundation

- Layered architecture: Core → Adapters → Services → Interface
- Configuration-driven scaling (v0→v1→v2)
- Pluggable fetcher system with auto-discovery
- Async-first design for v1 parallelization
- Clean package structure with abstraction layers
- Comprehensive test framework setup"
```

---

## Next Tasks Preview

**Task 2**: Core Models & State Management (Pydantic schemas, versioned state)
**Task 3**: Pluggable Fetcher System (Base class, registry, HN implementation)  
**Task 4**: Source Configuration System (YAML loader, validation, grouping)
**Task 5**: Application Services (Ingestion, filtering, git ops)
**Task 6**: Enhanced Claude Code Integration (MRR with elite intelligence)
**Task 7**: End-to-End v0 Validation (HN source + manual inbox → digest)

Each task maintains the modular principles and prepares for seamless v1/v2 scaling.
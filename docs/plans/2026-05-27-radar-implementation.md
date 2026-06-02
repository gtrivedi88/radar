# Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal-native, memory-aware personal capability and opportunity radar that ingests ~80 sources on a bi-weekly cadence and synthesizes a 10-section action-pathed digest via Claude Code, with zero incremental dollar cost.

**Architecture:** Five components — Source Registry (YAML), Ingestion Layer (Python fetchers), State Store (markdown + jsonl), Synthesis Layer (Claude Code slash command using Map-Route-Reduce subagent dispatch), Delivery (git archive + terminal). State is append-only; cron never writes operator-edited files (R12). Each fetcher is isolated in try/except with failures logged and `last_success_at` watermarks (R11).

**Tech Stack:** Python 3.11+, httpx, feedparser, PyYAML, pydantic, tenacity, beautifulsoup4, pytest (with httpx.MockTransport for HTTP mocking), GitHub Actions, Claude Code slash commands.

**Reference clone:** `horizon-base/` is an untouched reference copy of Thysrael/Horizon. Mine its `src/scrapers/` patterns for ideas, but **do not edit or import from it** — write Radar fresh in `scripts/`.

**Spec source of truth:** [docs/specs/2026-05-27-radar-design.md](docs/specs/2026-05-27-radar-design.md). Sections referenced inline below.

---

## File Structure

Files this plan creates or modifies, with responsibilities. Each file has one clear concern.

```
radar/
├── pyproject.toml                       # T1 — deps + pytest config
├── README.md                            # T1 — minimum usage notes
├── inbox.md                             # T12 — operator-pasted links during fortnight
├── .github/workflows/
│   └── ingest.yml                       # T20 — cron Sunday 02:00 UTC, runs ingest, commits raw/
├── .claude/commands/
│   ├── radar.md                         # T11 — synthesis slash command (MRR-aware)
│   └── radar-section.md                 # T27 — per-section regenerate fallback (v2)
├── sources/
│   ├── _groups.yaml                     # T9 / T21 — source grouping for MRR Map phase
│   ├── hn-algolia.yaml                  # T9 — v0 single source
│   ├── (9 more v1 YAMLs)                # T18
│   └── (~70 more v2 YAMLs)              # T25
├── scripts/
│   ├── __init__.py                      # T1
│   ├── common.py                        # T3 — sha1 item_id, append_jsonl, iso_now, log_fetch_error
│   ├── git_preflight.py                 # T4 — `git pull --rebase` guard (R12)
│   ├── sources.py                       # T5 — YAML loader, SourceConfig pydantic model
│   ├── watermarks.py                    # T6 — state/watermarks.json read/write (R11)
│   ├── prefilter.py                     # T7 — recency / engagement / dedup pipeline
│   ├── ingest.py                        # T10 — orchestrator (loads sources, runs fetchers, writes raw/)
│   ├── persist_signal.py                # T11 — CLI helper for slash command to append signals.jsonl
│   ├── maintenance.py                   # T26 — quarterly compaction (v2)
│   └── fetchers/
│       ├── __init__.py                  # T8
│       ├── base.py                      # T8 — BaseFetcher with try/except isolation + watermark update
│       ├── json_api.py                  # T9 — generic JSON endpoint fetcher (used by HN, Reddit)
│       ├── rss.py                       # T14 — feedparser-backed RSS fetcher
│       ├── github_watch.py              # T15 — GitHub API repo activity fetcher
│       ├── scrape.py                    # T16 — BeautifulSoup HTML fetcher
│       ├── pain_point.py                # T19 — Reddit/HN deep comment harvester
│       ├── investor_signal.py           # T23 — composite (YC + a16z + Sequoia + PH + Crunchbase free) (v2)
│       └── skill_velocity.py            # T24 — composite (LinkedIn jobs + HN Who's Hiring + Layoffs.fyi) (v2)
├── tests/
│   ├── conftest.py                      # T1 — repo-root fixture, isolated tmp_path roots
│   ├── test_common.py                   # T3
│   ├── test_git_preflight.py            # T4
│   ├── test_sources.py                  # T5
│   ├── test_watermarks.py               # T6
│   ├── test_prefilter.py                # T7
│   ├── test_base_fetcher.py             # T8
│   ├── test_json_api.py                 # T9
│   ├── test_ingest.py                   # T10
│   ├── test_rss.py                      # T14
│   ├── test_github_watch.py             # T15
│   ├── test_scrape.py                   # T16
│   ├── test_pain_point.py               # T19
│   ├── test_investor_signal.py          # T23
│   ├── test_skill_velocity.py           # T24
│   └── test_maintenance.py              # T26
├── state/
│   ├── profile.md                       # T2 — operator profile (template; operator fills)
│   ├── catalog.md                       # T2 — published work (template)
│   ├── trajectory.md                    # T2 — Doing/Queued/Passed/Finished (template)
│   ├── feedback.md                      # T2 — Doing/Pass/Done/Watch per item (template)
│   ├── signals.jsonl                    # T2 — append-only (item observations + theme rollups)
│   ├── fetch-errors.jsonl               # T2 — append-only (R11)
│   ├── watermarks.json                  # T2 — {"<source-id>": "<ISO8601>"} (R11)
│   └── archive/.gitkeep                 # T2
├── raw/.gitkeep                         # T1 — populated by ingest at raw/YYYY-MM-DD/<source>.json
├── intermediate/                        # gitignored — populated per synthesis run
└── horizon-base/                        # gitignored reference only — do not modify
```

**`signals.jsonl` dual schema (resolves Section 4.2 / 4.3 inconsistency):**
- Item observation (written by ingestion): `{"date": "YYYY-MM-DD", "item_id": "<sha1>", "source_id": "<id>", "dedup_key": "<str>"}`
- Theme rollup (written by synthesis): `{"date": "YYYY-MM-DD", "theme": "<slug>", "source_count": <int>, "engagement_total": <int>}`

Both record types coexist. Consumers filter by which keys are present. Both append-only → cron-safe.

---

## Phasing

- **v0** (Tasks 1–13) — working end-to-end loop with HN Algolia as single automated source. Operator runs `/radar` manually after pasting links into `inbox.md`. MRR architecture in place from day 1 even though there is only one group.
- **v1** (Tasks 14–22) — 10 automated sources, GitHub Actions cron, pain-point harvester.
- **v2** (Tasks 23–28) — full ~80 source registry, composite fetchers, quarterly compaction, per-section regeneration fallback.

---

# v0 — First Executable Block

## Task 1: Project bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `scripts/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `raw/.gitkeep`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "radar"
version = "0.1.0"
description = "Personal capability and opportunity intelligence system"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",
    "feedparser>=6.0.11",
    "pydantic>=2.9.0",
    "python-dateutil>=2.9.0",
    "pyyaml>=6.0.2",
    "tenacity>=9.0.0",
    "beautifulsoup4>=4.12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["scripts"]

[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-q"
testpaths = ["tests"]
```

- [ ] **Step 2: Write `README.md`**

```markdown
# Radar

Personal capability and opportunity intelligence system. See [docs/specs/2026-05-27-radar-design.md](docs/specs/2026-05-27-radar-design.md) for the full design.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
# Ingest the current source registry into raw/YYYY-MM-DD/
python -m scripts.ingest

# Synthesize a digest (inside Claude Code session, in this repo)
/radar
```

## Layout

- `sources/` — one YAML per source. Drop a file = new source.
- `state/` — operator-editable identity, catalog, trajectory, feedback.
- `raw/YYYY-MM-DD/` — fetcher output per run.
- `state/archive/` — digests committed across runs.
```

- [ ] **Step 3: Create empty package + test scaffolding**

`scripts/__init__.py`:

```python
```

`tests/__init__.py`:

```python
```

`tests/conftest.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Isolated repo root with state/ and raw/ scaffolded for a test run."""
    for sub in ("state", "state/archive", "raw", "intermediate", "sources"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    return tmp_path
```

`raw/.gitkeep`:

```
```

- [ ] **Step 4: Verify install + pytest run**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Expected: `0 passed` (no tests yet, but collection succeeds).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md scripts/__init__.py tests/__init__.py tests/conftest.py raw/.gitkeep
git commit -m "chore: bootstrap radar project scaffold"
```

---

## Task 2: State store templates

**Files:**
- Create: `state/profile.md`
- Create: `state/catalog.md`
- Create: `state/trajectory.md`
- Create: `state/feedback.md`
- Create: `state/signals.jsonl`
- Create: `state/fetch-errors.jsonl`
- Create: `state/watermarks.json`
- Create: `state/archive/.gitkeep`

- [ ] **Step 1: Write `state/profile.md` template** (operator fills, but ship a usable skeleton — see spec Section 4.3)

```markdown
# Operator Profile

> Semi-static. Reviewed quarterly. Edited by operator only — cron never writes this file.

## Identity
- Name:
- Location:
- Current role:
- Audiences served: tech_writer, devs_curious_ai, hardcore_tech
- Voice DNA: cinematic, visceral, confrontational, philosophical
- Voice constraints: no em dashes, no AI transitions, no third-person hypotheticals

## Active Tools
- Claude (Max plan, terminal-first via Claude Code)
- Cursor
- NotebookLM

## Beat (what I write/teach about)
- AI-for-tech-writers craft and workflow
- Claude Code .md-driven development
- AI tool stacks for non-coders
- Tech writer career evolution under AI
- Satire on AI hype

## Topics done / bored of
- Generic "AI will replace writers" takes
- Tool-roundup posts without opinion

## Where I'm going next
- (free-form, edit anytime)
```

- [ ] **Step 2: Write `state/catalog.md` template**

```markdown
# Published Work

> Auto-generated from `_posts/` in the blog repo (manual paste OK for v0). Synthesis must never re-suggest a topic already here.

## Blog Posts (sorted by date)
- (none yet — paste entries here as YYYY-MM-DD | title | url)

## Courses
- (empty — no courses launched yet)

## Talks
- (empty)

## Newsletters / Other
- (empty)
```

- [ ] **Step 3: Write `state/trajectory.md` template**

```markdown
# Trajectory

> Operator-edited. Cron never writes this file.

## Doing (started, in flight)
- (none yet)

## Queued (interested, not started)
- (none yet)

## Passed (explored, decided no)
- (none yet)

## Finished (done and useful)
- (none yet)
```

- [ ] **Step 4: Write `state/feedback.md` template**

```markdown
# Feedback Log

> Operator-edited (or edited in-session by Claude when operator says "mark item-X Doing"). One line per item per past digest.
>
> Format: `YYYY-MM-DD | item-<id> | Doing|Pass|Done|Watch | optional reason`

```

- [ ] **Step 5: Create empty append-only logs and watermarks**

`state/signals.jsonl`:

```
```

`state/fetch-errors.jsonl`:

```
```

`state/watermarks.json`:

```json
{}
```

`state/archive/.gitkeep`:

```
```

- [ ] **Step 6: Commit**

```bash
git add state/
git commit -m "chore: scaffold state store with templates and empty logs"
```

---

## Task 3: `scripts/common.py` — shared utilities

**Files:**
- Create: `scripts/common.py`
- Test: `tests/test_common.py`

- [ ] **Step 1: Write failing tests**

`tests/test_common.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.common import (
    append_jsonl,
    compute_item_id,
    iso_now,
    log_fetch_error,
    today_utc_date,
)


def test_compute_item_id_is_stable_for_same_inputs():
    a = compute_item_id("Hello World", "https://example.com/a")
    b = compute_item_id("Hello World", "https://example.com/a")
    assert a == b
    assert len(a) == 40  # sha1 hex


def test_compute_item_id_differs_for_different_urls():
    a = compute_item_id("Same Title", "https://example.com/a")
    b = compute_item_id("Same Title", "https://example.com/b")
    assert a != b


def test_iso_now_returns_utc_z_suffix():
    s = iso_now()
    assert s.endswith("Z")
    # Parseable as ISO 8601
    datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_today_utc_date_yyyy_mm_dd():
    s = today_utc_date()
    assert len(s) == 10 and s[4] == "-" and s[7] == "-"


def test_append_jsonl_creates_file_and_appends_records(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    append_jsonl(log, {"a": 1})
    append_jsonl(log, {"b": 2})
    lines = log.read_text().splitlines()
    assert [json.loads(l) for l in lines] == [{"a": 1}, {"b": 2}]


def test_append_jsonl_is_append_only_under_repeated_calls(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    for i in range(5):
        append_jsonl(log, {"i": i})
    lines = log.read_text().splitlines()
    assert len(lines) == 5
    assert json.loads(lines[2]) == {"i": 2}


def test_log_fetch_error_writes_structured_record(tmp_path: Path):
    log = tmp_path / "errors.jsonl"
    try:
        raise ValueError("boom")
    except ValueError as exc:
        log_fetch_error(log, source_id="hn-algolia", exc=exc)
    rec = json.loads(log.read_text().splitlines()[0])
    assert rec["source_id"] == "hn-algolia"
    assert rec["exception_class"] == "ValueError"
    assert "boom" in rec["traceback_excerpt"]
    assert rec["timestamp"].endswith("Z")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_common.py -v
```

Expected: ImportError / ModuleNotFoundError on `scripts.common`.

- [ ] **Step 3: Implement `scripts/common.py`**

```python
from __future__ import annotations

import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def compute_item_id(title: str, url: str) -> str:
    """Stable SHA-1 over (title, url). Used as item_id and dedup_key default."""
    h = hashlib.sha1()
    h.update(title.encode("utf-8"))
    h.update(b"\x00")
    h.update(url.encode("utf-8"))
    return h.hexdigest()


def iso_now() -> str:
    """UTC ISO-8601 with trailing Z. Stable format across the codebase."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_utc_date() -> str:
    """YYYY-MM-DD in UTC. Used for raw/ subdirectory and digest filenames."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one JSON record as a single line. Creates parent dirs and file if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.write("\n")


def log_fetch_error(path: Path, *, source_id: str, exc: BaseException) -> None:
    """Log a structured fetch-error record to state/fetch-errors.jsonl (R11)."""
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    excerpt = tb[-1500:] if len(tb) > 1500 else tb
    append_jsonl(
        path,
        {
            "timestamp": iso_now(),
            "source_id": source_id,
            "exception_class": type(exc).__name__,
            "message": str(exc),
            "traceback_excerpt": excerpt,
        },
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_common.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/common.py tests/test_common.py
git commit -m "feat: add common utilities (item_id, jsonl append, fetch-error logging)"
```

---

## Task 4: `scripts/git_preflight.py` — pre-flight rebase guard (R12)

**Files:**
- Create: `scripts/git_preflight.py`
- Test: `tests/test_git_preflight.py`

- [ ] **Step 1: Write failing tests**

`tests/test_git_preflight.py`:

```python
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.git_preflight import PreflightError, preflight_git_pull


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "seed").write_text("x")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=path, check=True)


def test_preflight_succeeds_with_no_remote_and_clean_tree(tmp_path: Path):
    _init_repo(tmp_path)
    # No remote configured — preflight should treat this as a no-op success.
    preflight_git_pull(tmp_path)


def test_preflight_raises_when_not_a_git_repo(tmp_path: Path):
    with pytest.raises(PreflightError):
        preflight_git_pull(tmp_path)


def test_preflight_raises_when_rebase_fails(tmp_path: Path, monkeypatch):
    _init_repo(tmp_path)
    # Force a remote that does not exist so `git pull --rebase` fails.
    subprocess.run(
        ["git", "remote", "add", "origin", "file:///nonexistent/path/.git"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "branch.main.remote", "origin"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "branch.main.merge", "refs/heads/main"],
        cwd=tmp_path,
        check=True,
    )
    with pytest.raises(PreflightError) as excinfo:
        preflight_git_pull(tmp_path)
    assert "rebase" in str(excinfo.value).lower() or "pull" in str(excinfo.value).lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_git_preflight.py -v
```

Expected: ImportError on `scripts.git_preflight`.

- [ ] **Step 3: Implement `scripts/git_preflight.py`**

```python
from __future__ import annotations

import subprocess
from pathlib import Path


class PreflightError(RuntimeError):
    """Raised when the pre-flight git pull --rebase fails. Caller should abort."""


def preflight_git_pull(repo_path: Path) -> None:
    """Run `git pull --rebase` in `repo_path`. Abort the caller on any failure.

    R12: every ingestion and synthesis run starts with this. If the rebase fails
    (operator has un-pushed local edits that conflict), refuse to continue rather
    than corrupting state.

    No-op if no upstream is configured for the current branch (treated as success).
    """
    if not (repo_path / ".git").exists():
        raise PreflightError(f"{repo_path} is not a git repository")

    upstream = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if upstream.returncode != 0:
        # No upstream configured. Local-only setup. Nothing to pull.
        return

    result = subprocess.run(
        ["git", "pull", "--rebase"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PreflightError(
            "git pull --rebase failed. Resolve conflicts or push pending edits "
            "before re-running.\n\nstdout:\n"
            + result.stdout
            + "\nstderr:\n"
            + result.stderr
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_git_preflight.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/git_preflight.py tests/test_git_preflight.py
git commit -m "feat: add git pre-flight rebase guard (R12)"
```

---

## Task 5: `scripts/sources.py` — source YAML loader

**Files:**
- Create: `scripts/sources.py`
- Test: `tests/test_sources.py`

- [ ] **Step 1: Write failing tests**

`tests/test_sources.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sources import (
    FragilityTier,
    SourceConfig,
    load_source,
    load_all_sources,
)


YAML_OK = """
id: hn-algolia
name: Hacker News (Algolia)
type: json_api
config:
  endpoint: https://hn.algolia.com/api/v1/search
  query_params:
    tags: front_page
poll_cadence: daily
signal_type:
  - news
  - capability
audience_tags:
  - hardcore_tech
  - devs_curious_ai
relevance_tags:
  - hn
pre_filter:
  min_engagement: 50
  recency_window_days: 14
  dedup_key: title_url
priority: 1
fragility_tier: stable
staleness_threshold_days: 14
"""


def test_load_source_parses_valid_yaml(tmp_path: Path):
    p = tmp_path / "hn-algolia.yaml"
    p.write_text(YAML_OK)
    cfg = load_source(p)
    assert cfg.id == "hn-algolia"
    assert cfg.type == "json_api"
    assert cfg.signal_type == ["news", "capability"]
    assert cfg.pre_filter.min_engagement == 50
    assert cfg.pre_filter.recency_window_days == 14
    assert cfg.fragility_tier == FragilityTier.stable
    assert cfg.priority == 1


def test_load_source_defaults_fragility_to_stable(tmp_path: Path):
    p = tmp_path / "x.yaml"
    p.write_text(
        """
id: x
name: x
type: rss
config: {url: https://example.com/feed}
poll_cadence: daily
signal_type: [news]
audience_tags: [hardcore_tech]
relevance_tags: []
pre_filter: {min_engagement: 0, recency_window_days: 14, dedup_key: title_url}
priority: 3
"""
    )
    cfg = load_source(p)
    assert cfg.fragility_tier == FragilityTier.stable
    assert cfg.staleness_threshold_days == 14


def test_load_source_rejects_unknown_type(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text(
        """
id: bad
name: bad
type: telepathy
config: {}
poll_cadence: daily
signal_type: [news]
audience_tags: [hardcore_tech]
relevance_tags: []
pre_filter: {min_engagement: 0, recency_window_days: 14, dedup_key: title_url}
priority: 3
"""
    )
    with pytest.raises(Exception):
        load_source(p)


def test_load_all_sources_skips_underscore_prefixed(tmp_path: Path):
    (tmp_path / "_groups.yaml").write_text("groups: {}\n")
    (tmp_path / "hn-algolia.yaml").write_text(YAML_OK)
    sources = load_all_sources(tmp_path)
    assert len(sources) == 1
    assert sources[0].id == "hn-algolia"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_sources.py -v
```

Expected: ImportError on `scripts.sources`.

- [ ] **Step 3: Implement `scripts/sources.py`**

```python
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


class FragilityTier(str, Enum):
    stable = "stable"
    moderate = "moderate"
    fragile = "fragile"


SourceType = Literal[
    "rss",
    "json_api",
    "github_watch",
    "scrape",
    "search_query",
    "investor_signal",
    "skill_velocity",
    "pain_point",
]


class PreFilter(BaseModel):
    min_engagement: int = 0
    recency_window_days: int = 14
    dedup_key: str = "title_url"


class SourceConfig(BaseModel):
    id: str
    name: str
    type: SourceType
    config: dict[str, Any] = Field(default_factory=dict)
    poll_cadence: Literal["hourly", "daily", "weekly"] = "weekly"
    signal_type: list[str]
    audience_tags: list[str]
    relevance_tags: list[str] = Field(default_factory=list)
    pre_filter: PreFilter = Field(default_factory=PreFilter)
    priority: int = 3
    fragility_tier: FragilityTier = FragilityTier.stable
    staleness_threshold_days: int = 14


def load_source(path: Path) -> SourceConfig:
    """Load and validate a single source YAML file."""
    data = yaml.safe_load(path.read_text())
    return SourceConfig.model_validate(data)


def load_all_sources(sources_dir: Path) -> list[SourceConfig]:
    """Load all *.yaml files in `sources_dir`, skipping files prefixed with `_`
    (those are config files such as `_groups.yaml`)."""
    out: list[SourceConfig] = []
    for path in sorted(sources_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        out.append(load_source(path))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_sources.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/sources.py tests/test_sources.py
git commit -m "feat: source YAML loader with pydantic validation"
```

---

## Task 6: `scripts/watermarks.py` — `last_success_at` per source (R11)

**Files:**
- Create: `scripts/watermarks.py`
- Test: `tests/test_watermarks.py`

- [ ] **Step 1: Write failing tests**

`tests/test_watermarks.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.watermarks import (
    days_since,
    load_watermarks,
    save_watermarks,
    stamp_success,
)


def test_load_watermarks_returns_empty_dict_when_missing(tmp_path: Path):
    assert load_watermarks(tmp_path / "missing.json") == {}


def test_save_then_load_roundtrip(tmp_path: Path):
    p = tmp_path / "w.json"
    save_watermarks(p, {"hn-algolia": "2026-05-27T02:14:33Z"})
    assert load_watermarks(p) == {"hn-algolia": "2026-05-27T02:14:33Z"}


def test_stamp_success_updates_single_source(tmp_path: Path):
    p = tmp_path / "w.json"
    save_watermarks(p, {"a": "2026-01-01T00:00:00Z"})
    stamp_success(p, "b")
    data = load_watermarks(p)
    assert data["a"] == "2026-01-01T00:00:00Z"
    assert "b" in data
    assert data["b"].endswith("Z")


def test_days_since_returns_integer_age(tmp_path: Path):
    past = (datetime.now(timezone.utc) - timedelta(days=20)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    age = days_since(past)
    assert 19 <= age <= 21


def test_days_since_none_returns_infinity():
    assert days_since(None) == float("inf")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_watermarks.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/watermarks.py`**

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.common import iso_now


def load_watermarks(path: Path) -> dict[str, str]:
    """Load watermarks dict, returning {} if the file is missing."""
    if not path.exists():
        return {}
    raw = path.read_text().strip()
    if not raw:
        return {}
    return json.loads(raw)


def save_watermarks(path: Path, data: dict[str, str]) -> None:
    """Overwrite watermarks file with `data`. File is small; rewrite is safe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def stamp_success(path: Path, source_id: str) -> None:
    """Record that `source_id` succeeded right now."""
    data = load_watermarks(path)
    data[source_id] = iso_now()
    save_watermarks(path, data)


def days_since(iso_timestamp: str | None) -> float:
    """Return age in days of an ISO-8601 Z timestamp. None / missing → infinity."""
    if not iso_timestamp:
        return float("inf")
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - dt
    return delta.total_seconds() / 86400.0
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_watermarks.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/watermarks.py tests/test_watermarks.py
git commit -m "feat: per-source last_success_at watermarks (R11)"
```

---

## Task 7: `scripts/prefilter.py` — recency / engagement / dedup pipeline

**Files:**
- Create: `scripts/prefilter.py`
- Test: `tests/test_prefilter.py`

- [ ] **Step 1: Write failing tests**

`tests/test_prefilter.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.prefilter import apply_prefilter, load_recent_dedup_keys
from scripts.sources import PreFilter


def _iso(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_apply_prefilter_drops_items_outside_recency_window():
    pre = PreFilter(min_engagement=0, recency_window_days=14, dedup_key="title_url")
    items = [
        {"item_id": "a", "timestamp": _iso(1), "metrics": {"score": 10}, "dedup_key": "a"},
        {"item_id": "b", "timestamp": _iso(30), "metrics": {"score": 10}, "dedup_key": "b"},
    ]
    out = apply_prefilter(items, pre, seen_keys=set())
    assert [x["item_id"] for x in out] == ["a"]


def test_apply_prefilter_drops_items_below_engagement_floor():
    pre = PreFilter(min_engagement=50, recency_window_days=14, dedup_key="title_url")
    items = [
        {"item_id": "a", "timestamp": _iso(1), "metrics": {"score": 100}, "dedup_key": "a"},
        {"item_id": "b", "timestamp": _iso(1), "metrics": {"score": 5}, "dedup_key": "b"},
        {"item_id": "c", "timestamp": _iso(1), "metrics": {}, "dedup_key": "c"},
    ]
    out = apply_prefilter(items, pre, seen_keys=set())
    assert {x["item_id"] for x in out} == {"a"}


def test_apply_prefilter_drops_seen_dedup_keys():
    pre = PreFilter(min_engagement=0, recency_window_days=14, dedup_key="title_url")
    items = [
        {"item_id": "a", "timestamp": _iso(1), "metrics": {"score": 1}, "dedup_key": "k1"},
        {"item_id": "b", "timestamp": _iso(1), "metrics": {"score": 1}, "dedup_key": "k2"},
    ]
    out = apply_prefilter(items, pre, seen_keys={"k1"})
    assert [x["item_id"] for x in out] == ["b"]


def test_load_recent_dedup_keys_reads_signals_jsonl_within_window(tmp_path: Path):
    signals = tmp_path / "signals.jsonl"
    signals.write_text(
        "\n".join(
            [
                json.dumps({"date": _iso(2)[:10], "item_id": "x", "dedup_key": "k1"}),
                json.dumps({"date": _iso(40)[:10], "item_id": "y", "dedup_key": "k2"}),
                json.dumps({"date": _iso(1)[:10], "theme": "trend", "source_count": 3, "engagement_total": 100}),
            ]
        )
        + "\n"
    )
    keys = load_recent_dedup_keys(signals, lookback_days=30)
    assert keys == {"k1"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_prefilter.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/prefilter.py`**

```python
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from scripts.sources import PreFilter


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _engagement_score(item: dict[str, Any]) -> int:
    """Sum of available engagement metrics. Treat missing as 0."""
    metrics = item.get("metrics") or {}
    total = 0
    for k in ("score", "comments", "stars", "upvotes", "replies"):
        v = metrics.get(k)
        if isinstance(v, (int, float)):
            total += int(v)
    return total


def apply_prefilter(
    items: Iterable[dict[str, Any]],
    pre: PreFilter,
    *,
    seen_keys: set[str],
) -> list[dict[str, Any]]:
    """Apply the four-step prefilter from Section 4.2:
    1. Recency window
    2. Engagement floor
    3. Dedup against seen_keys (caller loads from signals.jsonl)
    4. (Audience tag inheritance happens at the fetcher level when it normalizes items.)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=pre.recency_window_days)
    out: list[dict[str, Any]] = []
    for item in items:
        ts = item.get("timestamp")
        if ts and _parse_iso(ts) < cutoff:
            continue
        if _engagement_score(item) < pre.min_engagement:
            continue
        key = item.get("dedup_key") or item.get("item_id")
        if key in seen_keys:
            continue
        out.append(item)
    return out


def load_recent_dedup_keys(signals_path: Path, *, lookback_days: int = 30) -> set[str]:
    """Read state/signals.jsonl and return the set of dedup_keys observed within
    the lookback window. Theme-rollup records (no dedup_key) are ignored."""
    if not signals_path.exists():
        return set()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date()
    keys: set[str] = set()
    for line in signals_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        key = rec.get("dedup_key")
        if not key:
            continue
        date_str = rec.get("date")
        if date_str:
            try:
                if datetime.strptime(date_str, "%Y-%m-%d").date() < cutoff:
                    continue
            except ValueError:
                pass
        keys.add(key)
    return keys
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_prefilter.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/prefilter.py tests/test_prefilter.py
git commit -m "feat: prefilter pipeline (recency, engagement, dedup)"
```

---

## Task 8: `scripts/fetchers/base.py` — isolated fetcher with watermark stamping (R11)

**Files:**
- Create: `scripts/fetchers/__init__.py`
- Create: `scripts/fetchers/base.py`
- Test: `tests/test_base_fetcher.py`

- [ ] **Step 1: Write failing tests**

`tests/test_base_fetcher.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from scripts.fetchers.base import BaseFetcher, FetchOutcome
from scripts.sources import PreFilter, SourceConfig


class _GoodFetcher(BaseFetcher):
    def fetch_items(self):
        return [
            {
                "item_id": "i1",
                "title": "x",
                "url": "https://x",
                "source_id": self.source.id,
                "signal_type": self.source.signal_type,
                "audience_tags": self.source.audience_tags,
                "timestamp": "2026-05-27T00:00:00Z",
                "raw_text": "x",
                "metrics": {"score": 10},
                "relevance_tags": self.source.relevance_tags,
                "fetched_at": "2026-05-27T00:00:00Z",
                "dedup_key": "k1",
            }
        ]


class _BrokenFetcher(BaseFetcher):
    def fetch_items(self):
        raise RuntimeError("network down")


def _src(id_: str, type_: str = "json_api") -> SourceConfig:
    return SourceConfig(
        id=id_,
        name=id_,
        type=type_,
        config={},
        poll_cadence="daily",
        signal_type=["news"],
        audience_tags=["hardcore_tech"],
        relevance_tags=[],
        pre_filter=PreFilter(min_engagement=0, recency_window_days=365, dedup_key="title_url"),
        priority=1,
    )


def test_run_returns_items_and_stamps_watermark_on_success(tmp_path: Path):
    errors = tmp_path / "errors.jsonl"
    watermarks = tmp_path / "watermarks.json"
    fetcher = _GoodFetcher(
        source=_src("hn-algolia"),
        errors_path=errors,
        watermarks_path=watermarks,
    )
    outcome = fetcher.run()
    assert outcome.ok is True
    assert len(outcome.items) == 1
    assert "hn-algolia" in json.loads(watermarks.read_text())
    assert not errors.exists() or errors.read_text() == ""


def test_run_logs_error_and_returns_empty_on_exception(tmp_path: Path):
    errors = tmp_path / "errors.jsonl"
    watermarks = tmp_path / "watermarks.json"
    fetcher = _BrokenFetcher(
        source=_src("flaky"),
        errors_path=errors,
        watermarks_path=watermarks,
    )
    outcome = fetcher.run()
    assert outcome.ok is False
    assert outcome.items == []
    rec = json.loads(errors.read_text().splitlines()[0])
    assert rec["source_id"] == "flaky"
    assert rec["exception_class"] == "RuntimeError"
    # No watermark update on failure.
    assert "flaky" not in json.loads(watermarks.read_text() or "{}")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_base_fetcher.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/__init__.py` (empty) and `scripts/fetchers/base.py`**

`scripts/fetchers/__init__.py`:

```python
```

`scripts/fetchers/base.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.common import log_fetch_error
from scripts.sources import SourceConfig
from scripts.watermarks import stamp_success


@dataclass
class FetchOutcome:
    """Result envelope for one fetcher run. Always returned; never raised."""

    source_id: str
    ok: bool
    items: list[dict[str, Any]] = field(default_factory=list)


class BaseFetcher(ABC):
    """Each subclass implements `fetch_items()`. The framework wraps that call
    in try/except so one broken fetcher cannot crash the cron (R11).

    On success: items are returned, watermark is stamped.
    On exception: error is logged to fetch-errors.jsonl, empty list returned,
    watermark left untouched (R11.2 — staleness aging visible to synthesis).
    """

    def __init__(
        self,
        *,
        source: SourceConfig,
        errors_path: Path,
        watermarks_path: Path,
    ) -> None:
        self.source = source
        self.errors_path = errors_path
        self.watermarks_path = watermarks_path

    @abstractmethod
    def fetch_items(self) -> list[dict[str, Any]]:
        """Concrete subclasses return a list of items in the canonical raw schema
        (see spec Section 4.2). Must populate `dedup_key`."""

    def run(self) -> FetchOutcome:
        try:
            items = self.fetch_items()
        except BaseException as exc:  # noqa: BLE001 — deliberate broad catch (R11)
            log_fetch_error(self.errors_path, source_id=self.source.id, exc=exc)
            return FetchOutcome(source_id=self.source.id, ok=False, items=[])
        stamp_success(self.watermarks_path, self.source.id)
        return FetchOutcome(source_id=self.source.id, ok=True, items=items)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_base_fetcher.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/fetchers/__init__.py scripts/fetchers/base.py tests/test_base_fetcher.py
git commit -m "feat: BaseFetcher with try/except isolation and watermark stamping (R11)"
```

---

## Task 9: `scripts/fetchers/json_api.py` + HN Algolia source YAML

**Files:**
- Create: `scripts/fetchers/json_api.py`
- Create: `sources/hn-algolia.yaml`
- Create: `sources/_groups.yaml`
- Test: `tests/test_json_api.py`

- [ ] **Step 1: Write failing tests**

`tests/test_json_api.py`:

```python
from __future__ import annotations

from pathlib import Path

import httpx

from scripts.fetchers.json_api import HNAlgoliaFetcher
from scripts.sources import PreFilter, SourceConfig


HN_RESPONSE = {
    "hits": [
        {
            "objectID": "1001",
            "title": "Claude 4.7 launches",
            "url": "https://example.com/claude-47",
            "points": 420,
            "num_comments": 88,
            "created_at": "2026-05-26T12:00:00Z",
            "story_text": None,
        },
        {
            "objectID": "1002",
            "title": "Ask HN: Best practices for prompt caching",
            "url": None,
            "points": 75,
            "num_comments": 33,
            "created_at": "2026-05-25T10:00:00Z",
            "story_text": "I have been...",
        },
    ]
}


def _src() -> SourceConfig:
    return SourceConfig(
        id="hn-algolia",
        name="HN Algolia",
        type="json_api",
        config={
            "endpoint": "https://hn.algolia.com/api/v1/search",
            "query_params": {"tags": "front_page"},
        },
        poll_cadence="daily",
        signal_type=["news", "capability"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["hn"],
        pre_filter=PreFilter(min_engagement=50, recency_window_days=14, dedup_key="title_url"),
        priority=1,
    )


def test_hn_algolia_fetcher_normalizes_items(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "hn.algolia.com"
        assert request.url.params["tags"] == "front_page"
        return httpx.Response(200, json=HN_RESPONSE)

    transport = httpx.MockTransport(handler)
    fetcher = HNAlgoliaFetcher(
        source=_src(),
        errors_path=tmp_path / "errors.jsonl",
        watermarks_path=tmp_path / "w.json",
        transport=transport,
    )
    items = fetcher.fetch_items()
    assert len(items) == 2
    a, b = items
    assert a["title"] == "Claude 4.7 launches"
    assert a["url"] == "https://example.com/claude-47"
    assert a["source_id"] == "hn-algolia"
    assert a["signal_type"] == ["news", "capability"]
    assert a["audience_tags"] == ["hardcore_tech", "devs_curious_ai"]
    assert a["metrics"]["score"] == 420
    assert a["metrics"]["comments"] == 88
    assert a["timestamp"] == "2026-05-26T12:00:00Z"
    assert a["item_id"] and len(a["item_id"]) == 40
    assert a["dedup_key"] == a["item_id"]
    # Ask HN with no URL still produces a stable item using the HN permalink fallback.
    assert b["url"].startswith("https://news.ycombinator.com/item?id=")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_json_api.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/json_api.py`**

```python
from __future__ import annotations

from typing import Any

import httpx

from scripts.common import compute_item_id, iso_now
from scripts.fetchers.base import BaseFetcher


class HNAlgoliaFetcher(BaseFetcher):
    """Hacker News via the public Algolia search API.

    Endpoint: https://hn.algolia.com/api/v1/search
    Docs: https://hn.algolia.com/api
    No auth required.
    """

    def __init__(self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport

    def fetch_items(self) -> list[dict[str, Any]]:
        cfg = self.source.config
        endpoint: str = cfg["endpoint"]
        params: dict[str, Any] = dict(cfg.get("query_params") or {})
        with httpx.Client(transport=self._transport, timeout=30.0) as client:
            resp = client.get(endpoint, params=params)
            resp.raise_for_status()
            payload = resp.json()
        hits = payload.get("hits") or []
        fetched_at = iso_now()
        out: list[dict[str, Any]] = []
        for h in hits:
            title = h.get("title") or h.get("story_title") or ""
            url = h.get("url")
            if not url and h.get("objectID"):
                url = f"https://news.ycombinator.com/item?id={h['objectID']}"
            if not title or not url:
                continue
            item_id = compute_item_id(title, url)
            out.append(
                {
                    "item_id": item_id,
                    "title": title,
                    "url": url,
                    "source_id": self.source.id,
                    "signal_type": list(self.source.signal_type),
                    "audience_tags": list(self.source.audience_tags),
                    "timestamp": h.get("created_at"),
                    "raw_text": (h.get("story_text") or "")[:2000],
                    "metrics": {
                        "score": h.get("points") or 0,
                        "comments": h.get("num_comments") or 0,
                        "stars": None,
                    },
                    "relevance_tags": list(self.source.relevance_tags),
                    "fetched_at": fetched_at,
                    "dedup_key": item_id,
                }
            )
        return out
```

- [ ] **Step 4: Write the HN Algolia source YAML**

`sources/hn-algolia.yaml`:

```yaml
id: hn-algolia
name: Hacker News (Algolia, front page)
type: json_api
config:
  endpoint: https://hn.algolia.com/api/v1/search
  query_params:
    tags: front_page
poll_cadence: daily
signal_type:
  - news
  - capability
audience_tags:
  - hardcore_tech
  - devs_curious_ai
relevance_tags:
  - hn
pre_filter:
  min_engagement: 50
  recency_window_days: 14
  dedup_key: title_url
priority: 1
fragility_tier: stable
staleness_threshold_days: 14
```

- [ ] **Step 5: Write v0 source-group config**

`sources/_groups.yaml`:

```yaml
# Source grouping for MRR Map phase (spec Section 4.4.1).
# v0: only one group exists. v1/v2 will fill in the rest.
groups:
  hn_general:
    - hn-algolia
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_json_api.py -v
```

Expected: 1 passed.

- [ ] **Step 7: Commit**

```bash
git add scripts/fetchers/json_api.py sources/hn-algolia.yaml sources/_groups.yaml tests/test_json_api.py
git commit -m "feat: HN Algolia JSON fetcher + first source YAML + groups config"
```

---

## Task 10: `scripts/ingest.py` — orchestrator

**Files:**
- Create: `scripts/ingest.py`
- Test: `tests/test_ingest.py`

- [ ] **Step 1: Write failing tests**

`tests/test_ingest.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from scripts.ingest import IngestPaths, run_ingest
from scripts.sources import PreFilter, SourceConfig


HN_RESPONSE = {
    "hits": [
        {
            "objectID": "1001",
            "title": "Claude 4.7 launches",
            "url": "https://example.com/claude-47",
            "points": 420,
            "num_comments": 88,
            "created_at": "2026-05-26T12:00:00Z",
        },
        {
            "objectID": "1002",
            "title": "Low engagement story",
            "url": "https://example.com/low",
            "points": 5,
            "num_comments": 0,
            "created_at": "2026-05-26T12:00:00Z",
        },
    ]
}


@pytest.fixture
def paths(repo_root: Path) -> IngestPaths:
    (repo_root / "state").mkdir(exist_ok=True)
    return IngestPaths(
        sources_dir=repo_root / "sources",
        raw_dir=repo_root / "raw",
        signals_path=repo_root / "state" / "signals.jsonl",
        errors_path=repo_root / "state" / "fetch-errors.jsonl",
        watermarks_path=repo_root / "state" / "watermarks.json",
    )


def _write_hn_source(paths: IngestPaths) -> None:
    (paths.sources_dir / "hn-algolia.yaml").write_text(
        """
id: hn-algolia
name: HN
type: json_api
config:
  endpoint: https://hn.algolia.com/api/v1/search
  query_params: {tags: front_page}
poll_cadence: daily
signal_type: [news]
audience_tags: [hardcore_tech]
relevance_tags: [hn]
pre_filter: {min_engagement: 50, recency_window_days: 3650, dedup_key: title_url}
priority: 1
"""
    )


def test_run_ingest_writes_raw_and_signal_observations(paths: IngestPaths, monkeypatch):
    _write_hn_source(paths)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=HN_RESPONSE)

    transport = httpx.MockTransport(handler)
    run_ingest(paths, run_date="2026-05-27", http_transport=transport)

    raw_file = paths.raw_dir / "2026-05-27" / "hn-algolia.json"
    assert raw_file.exists()
    data = json.loads(raw_file.read_text())
    # Engagement floor 50 — second item drops.
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Claude 4.7 launches"

    # Signal observation appended for the kept item.
    obs = [json.loads(l) for l in paths.signals_path.read_text().splitlines()]
    assert any(r.get("item_id") and r.get("source_id") == "hn-algolia" for r in obs)

    # Watermark stamped.
    assert "hn-algolia" in json.loads(paths.watermarks_path.read_text())


def test_run_ingest_continues_when_one_source_fails(paths: IngestPaths):
    _write_hn_source(paths)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    transport = httpx.MockTransport(handler)
    run_ingest(paths, run_date="2026-05-27", http_transport=transport)

    err_lines = paths.errors_path.read_text().splitlines()
    assert any("hn-algolia" in l for l in err_lines)
    # Empty raw file is still written so synthesis routing degrades gracefully.
    raw_file = paths.raw_dir / "2026-05-27" / "hn-algolia.json"
    assert raw_file.exists()
    assert json.loads(raw_file.read_text())["items"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ingest.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/ingest.py`**

```python
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from scripts.common import append_jsonl, iso_now, today_utc_date
from scripts.fetchers.base import BaseFetcher, FetchOutcome
from scripts.fetchers.json_api import HNAlgoliaFetcher
from scripts.git_preflight import preflight_git_pull
from scripts.prefilter import apply_prefilter, load_recent_dedup_keys
from scripts.sources import SourceConfig, load_all_sources


@dataclass
class IngestPaths:
    sources_dir: Path
    raw_dir: Path
    signals_path: Path
    errors_path: Path
    watermarks_path: Path


# Type → fetcher class registry. New types add a row.
def _select_fetcher(source: SourceConfig) -> type[BaseFetcher]:
    if source.type == "json_api" and source.id == "hn-algolia":
        return HNAlgoliaFetcher
    # v1 / v2 will extend this. For v0, only HN Algolia is wired.
    raise NotImplementedError(
        f"No fetcher registered for type={source.type} id={source.id}"
    )


def _write_raw(raw_dir: Path, run_date: str, source_id: str, items: list[dict[str, Any]]) -> Path:
    out_dir = raw_dir / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{source_id}.json"
    payload = {
        "source_id": source_id,
        "run_date": run_date,
        "fetched_at": iso_now(),
        "items": items,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return out_path


def _record_observations(signals_path: Path, run_date: str, source_id: str, items: list[dict[str, Any]]) -> None:
    """Append one observation record per kept item (used by future synthesis dedup)."""
    for item in items:
        append_jsonl(
            signals_path,
            {
                "date": run_date,
                "item_id": item["item_id"],
                "source_id": source_id,
                "dedup_key": item.get("dedup_key", item["item_id"]),
            },
        )


def run_ingest(
    paths: IngestPaths,
    *,
    run_date: str | None = None,
    http_transport: httpx.BaseTransport | None = None,
    skip_preflight: bool = False,
) -> None:
    """Load sources, run fetchers in series (parallelization deferred to v1),
    write raw output per source, append observations to signals.jsonl."""
    if run_date is None:
        run_date = today_utc_date()

    if not skip_preflight:
        # R12 — abort on dirty state.
        preflight_git_pull(paths.sources_dir.parent)

    sources = load_all_sources(paths.sources_dir)
    seen_keys = load_recent_dedup_keys(paths.signals_path, lookback_days=30)

    for source in sources:
        FetcherCls = _select_fetcher(source)
        kwargs: dict[str, Any] = {
            "source": source,
            "errors_path": paths.errors_path,
            "watermarks_path": paths.watermarks_path,
        }
        if http_transport is not None and "transport" in FetcherCls.__init__.__code__.co_varnames:
            kwargs["transport"] = http_transport
        fetcher = FetcherCls(**kwargs)
        outcome: FetchOutcome = fetcher.run()

        kept = apply_prefilter(outcome.items, source.pre_filter, seen_keys=seen_keys)
        _write_raw(paths.raw_dir, run_date, source.id, kept)
        _record_observations(paths.signals_path, run_date, source.id, kept)
        # Update local seen_keys so within-run dedup is correct.
        for item in kept:
            seen_keys.add(item.get("dedup_key", item["item_id"]))


def _default_paths(repo_root: Path) -> IngestPaths:
    return IngestPaths(
        sources_dir=repo_root / "sources",
        raw_dir=repo_root / "raw",
        signals_path=repo_root / "state" / "signals.jsonl",
        errors_path=repo_root / "state" / "fetch-errors.jsonl",
        watermarks_path=repo_root / "state" / "watermarks.json",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run radar ingestion")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    run_ingest(_default_paths(args.repo_root), skip_preflight=args.skip_preflight)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ingest.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/ingest.py tests/test_ingest.py
git commit -m "feat: ingestion orchestrator (single source, prefilter pipeline, R12 preflight)"
```

---

## Task 11: `.claude/commands/radar.md` — synthesis slash command (MRR-aware)

**Files:**
- Create: `.claude/commands/radar.md`
- Create: `scripts/persist_signal.py`
- Test: (no unit test — this is a prompt artifact; verified by end-to-end smoke run in Task 13)

This is the load-bearing differentiator. The command instructs Claude to run Map-Route-Reduce synthesis (Section 4.4.1).

- [ ] **Step 1: Write `scripts/persist_signal.py` — small CLI helper used by the slash command to append theme rollups safely**

```python
"""CLI helper: append one signals.jsonl record from a JSON payload on argv or stdin.

Usage:
    python -m scripts.persist_signal '{"date":"2026-05-27","theme":"agentic_eval","source_count":4,"engagement_total":890}'
    echo '<json>' | python -m scripts.persist_signal -

Used by the /radar slash command for theme rollups so the append happens
through a single audited path rather than via ad-hoc file writes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.common import append_jsonl


REPO_ROOT = Path(__file__).resolve().parent.parent
SIGNALS_PATH = REPO_ROOT / "state" / "signals.jsonl"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: persist_signal '<json>' or persist_signal - (stdin)", file=sys.stderr)
        return 2
    raw = sys.stdin.read() if argv[1] == "-" else argv[1]
    record = json.loads(raw)
    required = {"date"}
    if not required.issubset(record):
        print(f"record missing required keys: {required - record.keys()}", file=sys.stderr)
        return 2
    append_jsonl(SIGNALS_PATH, record)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 2: Write `.claude/commands/radar.md`** (full prompt — no placeholders)

````markdown
---
description: Synthesize the fortnightly Radar digest from raw/ + state/ using Map-Route-Reduce.
---

# /radar

You are running the Radar synthesis pipeline for the operator. Read the design spec at `docs/specs/2026-05-27-radar-design.md` if you need to refresh context, but you should not need to — this command is self-contained.

## Critical rules

1. **Pre-flight first.** Run `git pull --rebase` before reading anything. If it fails, stop and ask the operator to resolve. Never proceed on conflicted state. (R12)
2. **Never write `state/profile.md`, `state/catalog.md`, `state/trajectory.md`, or `state/feedback.md`** unless the operator explicitly says "mark item-X Doing" (then update `trajectory.md` and `feedback.md` only). These are operator-edited. (R12)
3. **You may write:** `state/archive/radar-<RUN_DATE>.md` (new file), `intermediate/<group>.md` (per-group slice via subagents), and append to `state/signals.jsonl` via `python -m scripts.persist_signal '<json>'`.
4. **`<RUN_DATE>` is today's UTC date in `YYYY-MM-DD` form.** Compute with `date -u +%Y-%m-%d`.
5. **Graceful degradation.** If a source group has no raw input today, skip it. If a section's input slices are all empty, omit the section silently. Never block the whole digest on one missing piece. (R11 mitigation 3)

## Step 0 — Pre-flight (run, then proceed)

```bash
git pull --rebase
date -u +%Y-%m-%d
```

If the first command fails, stop and report the error.

## Step 1 — Read state into context

Read these files in order. Treat their contents as authoritative for operator identity, beat, prior work, and decisions:

1. `state/profile.md`
2. `state/catalog.md`
3. `state/trajectory.md`
4. `state/feedback.md`
5. `state/signals.jsonl` (full file — used for delta computation in Section 1)
6. `state/watermarks.json` (for stale-fragile-source flagging in Memory Thread)
7. The last 2 files in `state/archive/` (sorted by name desc), if any. Skip if none.

Also list `raw/<RUN_DATE>/` and `intermediate/` to know what is available.

## Step 2 — Map phase (parallel subagents per source group)

Read `sources/_groups.yaml`. For each group that has at least one raw JSON file in `raw/<RUN_DATE>/`, dispatch a subagent **in parallel** (one Task tool call per group, all in the same message — see superpowers:dispatching-parallel-agents).

Subagent prompt template (instantiate per group, with `<GROUP>` and `<SOURCE_IDS>` substituted):

> You are condensing one source group for the Radar digest. The operator's profile, audiences, and beat are in `state/profile.md` — read that first.
>
> Read every `raw/<RUN_DATE>/<source>.json` file for these source IDs: `<SOURCE_IDS>`.
>
> For each item, score relevance against the operator's beat (profile.md) and audience_tags. Drop items that are off-beat or generic AI-hype with no specific angle.
>
> Output a single file at `intermediate/<GROUP>.md`, capped at **500 words total**. Format:
>
> ```markdown
> # <GROUP> — <RUN_DATE>
>
> ## Top items (by relevance)
> - **<title>** (item_id: <id>, source: <source_id>) — 1-2 sentence why-it-matters tied to operator's beat. URL: <url>. Engagement: score=<n>, comments=<n>.
>
> ## Cross-source pattern (if any)
> Single paragraph naming any theme that surfaces in ≥2 sources within this group.
>
> ## Notable absences
> One line if a normally-strong source in this group returned nothing this run.
> ```
>
> No commentary outside that template. No item that fails the relevance bar. If nothing relevant, write a one-line file saying `# <GROUP> — empty for <RUN_DATE>`.

Wait for all subagents to finish before proceeding.

## Step 3 — Route phase (build each digest section)

The digest has Section 0 (Memory Thread) and Sections 1–10. For each section, you read **only the intermediate slices and state files in the routing table below** — do not re-read raw JSON. This is what defeats Lost-in-the-Middle attention drift (R8).

| # | Section | Reads (intermediate slices) | Reads (state) | Quality threshold |
|---|---|---|---|---|
| 0 | Memory Thread | none | trajectory.md, feedback.md, watermarks.json | Always include if any Doing items exist. Also flag any fragile source whose `days_since(last_success_at) > staleness_threshold_days`. |
| 1 | Top 5 trends | all groups | signals.jsonl | Trend needs ≥3 source presence AND non-zero delta vs at least one of last 2 digests. |
| 2 | What people are asking (3–5) | reddit_*, pain_points | catalog.md, profile.md | Skip if substantially covered in catalog. |
| 3 | Bleeding edge to learn (1–2) | capability_*, papers | trajectory.md, profile.md | Must be in beat tags. |
| 4 | Career skill velocity | skill_velocity | profile.md | ≥20% delta over 4 weeks. |
| 5 | Course prep (0–2) | investor, pain_points, skill_velocity, reddit_*, capability_* | catalog.md, profile.md | Must aggregate ≥3 of: investor_flow, pain_points, skill_velocity, question_mining, capability_releases. Otherwise → Watch. |
| 6 | Investor flow | investor | profile.md | ≥2 fundings in same theme. |
| 7 | CFPs and speaking | conferences | profile.md, feedback.md | Audience match required. Closing in ≤30 days. |
| 8 | Capability of the fortnight (1) | capability_claude, capability_cursor, capability_notebooklm | trajectory.md | Must be replicable in ≤30 min. |
| 9 | Pain points harvested (5–10) | pain_points | profile.md | ≥3 upvotes/replies on source comment. |
| 10 | Watch + counter-signal | all groups | signals.jsonl, archive/* | Counter requires negative delta over 4+ weeks. |

Apply these rules:
- **Trajectory boost.** Items in any group that touch an active Doing item get a 2× weight when ranking within a section.
- **Pass-list exclusion.** Items whose item_id appears in `feedback.md` with state Pass are excluded.
- **Counter-signal minimum.** Section 10 must include ≥2 fading-hype items. If the data does not support this honestly, write the section header with a single line saying so — never invent counter-signals.
- **Length cap.** Total digest ≤ 2000 words. Each section ≤ 5 items. Collapse empty sections silently.

## Step 4 — Stitch phase (write the digest)

Compose the final digest into `state/archive/radar-<RUN_DATE>.md` using this template (collapse empty sections silently):

```markdown
# Radar — <RUN_DATE>

## 0 Memory thread
<status check bullets for Doing items + age; flagged stale sources>

## 1 Top 5 trends this fortnight
1. **<name>** ↑/↓/→ — <one-line synthesis>. Sources: <links>.

## 2 What people are asking
- **Q:** <question>. **Where:** <link>. **Angle:** <one-line operator voice cut>. **Why now:** <one-line>.

## 3 Bleeding edge to learn
- **<topic>** — starter resources: <links>. 90-min first-touch plan: <3 bullets>. Continues from: <prior digest item or none>.

## 4 Career skill velocity
**Climbing:** <skill> (<n> jobs, +<n>% over 4 weeks). ...
**Cooling:** <skill> (<n> jobs, -<n>% over 4 weeks).

## 5 Course prep
### <topic>
- **Signals aligned:** <list>
- **Audience cut:** <tech_writer | devs_curious_ai | hardcore_tech>
- **Closest competitor course + gap:** <name + gap>
- **Suggested 5-module outline:** ...

## 6 Investor flow
**<theme>** (<n> raises this fortnight): <notable companies>. **Implication for beat:** <one-line>.

## 7 CFPs and speaking
- **<conference>** — deadline <date>. Talk angle: <one-line>.

## 8 Capability of the fortnight
**<workflow name>** — what it unlocks: <one-line>. Source: <link>. **30-min replication:** <copy-pasteable steps>.

## 9 Pain points harvested
- "<quote excerpt>" — <source link>, audience: <tag>.

## 10 Watch list + counter-signal
**Watch:**
- <theme> →/↑ — <one-line>.
**Counter:**
- <fading item> ↓ — evidence: <one-line>.

---
*Generated by /radar on <RUN_DATE>. Edit `state/feedback.md` or tell me "mark item-<id> Doing" to update trajectory.*
```

## Step 5 — Append signal rollups

For each distinct theme that appeared in Section 1 (Top 5 trends) and Section 10 (Watch), append one record to `state/signals.jsonl` using the helper:

```bash
python -m scripts.persist_signal '{"date":"<RUN_DATE>","theme":"<theme-slug>","source_count":<int>,"engagement_total":<int>}'
```

Theme slug is kebab-case. `source_count` is the number of distinct sources contributing to the theme this digest. `engagement_total` is the sum of all contributing items' `metrics.score + metrics.comments`.

## Step 6 — Report to operator

Print to terminal:

1. Path to the archive file.
2. A 3-bullet summary of the most operator-relevant items (the ones most likely to become Doing).
3. The cheapest invitation: "Mark anything Doing? Tell me the item-id."

Do NOT print the full digest — the operator reads it from the archive file in their editor.

## Operator in-session feedback path

If the operator says "mark item-<id> Doing" (or Pass / Done / Watch), append a line to `state/feedback.md`:

```
<RUN_DATE> | item-<id> | Doing | <optional reason>
```

If marked Doing, also add an entry under `## Doing` in `state/trajectory.md` with format:

```
- <RUN_DATE> | <one-line topic> | item-<id>
```

These are the only edits to operator files /radar is allowed to make, and only in response to an explicit operator instruction.
````

- [ ] **Step 3: Manual sanity-check the slash command file**

```bash
ls .claude/commands/radar.md
wc -w .claude/commands/radar.md
```

Expected: file exists; word count roughly 900–1200 (instruction-dense).

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/radar.md scripts/persist_signal.py
git commit -m "feat: /radar slash command (MRR synthesis) + persist_signal CLI"
```

---

## Task 12: `inbox.md` — manual paste buffer

**Files:**
- Create: `inbox.md`

- [ ] **Step 1: Write the template**

```markdown
# Inbox

> Paste links here as you encounter them during the fortnight. `/radar` reads this file as one of its inputs (treats each line as an additional candidate item).
>
> Format: `<YYYY-MM-DD> | <url> | <one-line why I bookmarked this>`
>
> Example:
> `2026-05-22 | https://www.anthropic.com/news/something | new MCP server pattern, course-shaped?`

```

- [ ] **Step 2: Add inbox.md to the `/radar` Step 1 reading list**

In `.claude/commands/radar.md`, append `inbox.md` to the bullet list under Step 1 ("Read state into context"). The slash command must include inbox items in the Map phase (treat them as a synthetic source group `manual_inbox`).

Find the line in `.claude/commands/radar.md`:

```
7. The last 2 files in `state/archive/` (sorted by name desc), if any. Skip if none.
```

Insert before it:

```
6b. `inbox.md` — manual paste-buffer entries from the operator. Treat as a synthetic group `manual_inbox` in the Map phase.
```

(Renumber as needed.)

- [ ] **Step 3: Commit**

```bash
git add inbox.md .claude/commands/radar.md
git commit -m "feat: add inbox.md and wire into /radar Map phase"
```

---

## Task 13: First end-to-end smoke run

**Files:**
- Modify: `state/profile.md` (operator content, but we capture instructions here)
- Modify: `state/catalog.md`

This task validates v0 end-to-end. No new code.

- [ ] **Step 1: Operator fills `state/profile.md`**

Replace the template content with the operator's actual identity. The operator can either draft from scratch or hand 15–20 recent post URLs to Claude in-session and say "draft my profile.md from these — voice DNA, beat, audiences, tools."

This task should pause for operator input. Mark it complete only after `state/profile.md` reflects the real operator.

- [ ] **Step 2: Operator fills `state/catalog.md`**

If the operator's blog repo has a `_posts/` directory accessible, ask them to paste the title list. Otherwise leave empty (catalog can be backfilled later).

- [ ] **Step 3: Run ingestion**

```bash
source .venv/bin/activate
python -m scripts.ingest --skip-preflight
ls raw/$(date -u +%Y-%m-%d)/
```

Expected: `hn-algolia.json` exists, contains an `items` array.

- [ ] **Step 4: Invoke `/radar` inside Claude Code in this repo**

Open a Claude Code session at the repo root, run `/radar`. Verify:
- Archive file written at `state/archive/radar-<today>.md`.
- The file has Memory Thread + at least Sections 1, 10 populated (others may collapse for v0 since only one source).
- `state/signals.jsonl` has new theme-rollup records appended.
- Word count ≤ 2000.

```bash
ls state/archive/
wc -w state/archive/radar-*.md | tail -1
tail -5 state/signals.jsonl
```

- [ ] **Step 5: Operator review — mark one item Doing or Pass**

In-session: "Mark item-<id> Doing." Verify:
- `state/feedback.md` has the new line.
- `state/trajectory.md` `## Doing` has the new entry.

- [ ] **Step 6: Commit the v0 milestone**

```bash
git add state/profile.md state/catalog.md state/archive/ state/signals.jsonl state/feedback.md state/trajectory.md state/watermarks.json state/fetch-errors.jsonl raw/
git commit -m "v0: first end-to-end /radar run (HN Algolia + inbox)"
```

**v0 acceptance criteria (all must pass):**
- `python -m scripts.ingest` writes `raw/<date>/hn-algolia.json` without crashing.
- `pytest -q` is green.
- `/radar` produces `state/archive/radar-<date>.md` with ≥ Memory Thread + Top 5 trends sections populated.
- `state/signals.jsonl` grows on every run.
- `state/fetch-errors.jsonl` is empty (or contains only honest fetch failures, not framework bugs).
- One broken source (try `--config endpoint=https://nonexistent/`) does not crash ingestion — produces a fetch-error log row, empty raw file, and the rest of the pipeline continues.

---

# v1 — 10 Automated Sources + Cron + Pain-Point Harvester

## Task 14: `scripts/fetchers/rss.py` — RSS/Atom fetcher

**Files:**
- Create: `scripts/fetchers/rss.py`
- Test: `tests/test_rss.py`

- [ ] **Step 1: Write failing tests**

`tests/test_rss.py`:

```python
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.fetchers.rss import RSSFetcher
from scripts.sources import PreFilter, SourceConfig


FAKE_FEED = {
    "entries": [
        {
            "title": "Constitutional AI v2",
            "link": "https://www.anthropic.com/news/constitutional-ai-v2",
            "summary": "We're announcing...",
            "published": "Tue, 26 May 2026 12:00:00 GMT",
            "published_parsed": (2026, 5, 26, 12, 0, 0, 1, 146, 0),
        },
        {
            "title": "",
            "link": "",
            "summary": "",
            "published_parsed": None,
        },
    ]
}


def _src() -> SourceConfig:
    return SourceConfig(
        id="anthropic-blog",
        name="Anthropic Blog",
        type="rss",
        config={"url": "https://www.anthropic.com/news/rss.xml"},
        poll_cadence="daily",
        signal_type=["capability", "news"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["anthropic", "claude"],
        pre_filter=PreFilter(min_engagement=0, recency_window_days=14, dedup_key="title_url"),
        priority=1,
    )


def test_rss_fetcher_normalizes_entries(tmp_path: Path):
    with patch("scripts.fetchers.rss.feedparser.parse", return_value=FAKE_FEED):
        f = RSSFetcher(
            source=_src(),
            errors_path=tmp_path / "e.jsonl",
            watermarks_path=tmp_path / "w.json",
        )
        items = f.fetch_items()
    assert len(items) == 1
    i = items[0]
    assert i["title"] == "Constitutional AI v2"
    assert i["url"].startswith("https://www.anthropic.com")
    assert i["source_id"] == "anthropic-blog"
    assert i["timestamp"] == "2026-05-26T12:00:00Z"
    assert i["metrics"] == {"score": 0, "comments": 0, "stars": None}
    assert i["dedup_key"] == i["item_id"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_rss.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/rss.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser

from scripts.common import compute_item_id, iso_now
from scripts.fetchers.base import BaseFetcher


def _struct_time_to_iso(parsed: Any) -> str | None:
    if not parsed:
        return None
    try:
        y, m, d, hh, mm, ss = parsed[:6]
        return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None


class RSSFetcher(BaseFetcher):
    """Generic RSS/Atom fetcher backed by feedparser.

    Config keys:
      url (required): feed URL
    """

    def fetch_items(self) -> list[dict[str, Any]]:
        url: str = self.source.config["url"]
        feed = feedparser.parse(url)
        fetched_at = iso_now()
        out: list[dict[str, Any]] = []
        for entry in feed.get("entries") or []:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            item_id = compute_item_id(title, link)
            out.append(
                {
                    "item_id": item_id,
                    "title": title,
                    "url": link,
                    "source_id": self.source.id,
                    "signal_type": list(self.source.signal_type),
                    "audience_tags": list(self.source.audience_tags),
                    "timestamp": _struct_time_to_iso(entry.get("published_parsed"))
                    or _struct_time_to_iso(entry.get("updated_parsed")),
                    "raw_text": (entry.get("summary") or "")[:2000],
                    "metrics": {"score": 0, "comments": 0, "stars": None},
                    "relevance_tags": list(self.source.relevance_tags),
                    "fetched_at": fetched_at,
                    "dedup_key": item_id,
                }
            )
        return out
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_rss.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Register RSSFetcher in `scripts/ingest.py` `_select_fetcher`**

Edit `scripts/ingest.py` `_select_fetcher` to handle `type == "rss"`:

```python
def _select_fetcher(source: SourceConfig) -> type[BaseFetcher]:
    from scripts.fetchers.rss import RSSFetcher

    if source.type == "json_api" and source.id == "hn-algolia":
        return HNAlgoliaFetcher
    if source.type == "rss":
        return RSSFetcher
    raise NotImplementedError(
        f"No fetcher registered for type={source.type} id={source.id}"
    )
```

- [ ] **Step 6: Commit**

```bash
git add scripts/fetchers/rss.py tests/test_rss.py scripts/ingest.py
git commit -m "feat: RSS fetcher (feedparser-backed)"
```

---

## Task 15: `scripts/fetchers/github_watch.py` — GitHub repo activity

**Files:**
- Create: `scripts/fetchers/github_watch.py`
- Test: `tests/test_github_watch.py`

- [ ] **Step 1: Write failing tests**

`tests/test_github_watch.py`:

```python
from __future__ import annotations

from pathlib import Path

import httpx

from scripts.fetchers.github_watch import GitHubWatchFetcher
from scripts.sources import PreFilter, SourceConfig


RELEASES = [
    {
        "tag_name": "v1.2.0",
        "name": "v1.2.0 — agentic eval helpers",
        "html_url": "https://github.com/anthropics/anthropic-cookbook/releases/tag/v1.2.0",
        "published_at": "2026-05-25T10:00:00Z",
        "body": "Added eval recipes.",
    }
]

COMMITS = [
    {
        "sha": "abc123",
        "html_url": "https://github.com/anthropics/anthropic-cookbook/commit/abc123",
        "commit": {
            "message": "Add MCP server recipe",
            "author": {"date": "2026-05-26T09:00:00Z"},
        },
        "files": [{"filename": "recipes/mcp_server_recipe.ipynb"}],
    },
    {
        "sha": "def456",
        "html_url": "https://github.com/anthropics/anthropic-cookbook/commit/def456",
        "commit": {
            "message": "Fix typo",
            "author": {"date": "2026-05-24T09:00:00Z"},
        },
        "files": [{"filename": "README.md"}],
    },
]


def _src() -> SourceConfig:
    return SourceConfig(
        id="anthropic-cookbook",
        name="Anthropic Cookbook",
        type="github_watch",
        config={"repo": "anthropics/anthropic-cookbook", "watch_paths": ["recipes/"], "include_releases": True},
        poll_cadence="weekly",
        signal_type=["capability", "workflow"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["claude", "recipes"],
        pre_filter=PreFilter(min_engagement=0, recency_window_days=14, dedup_key="title_url"),
        priority=1,
    )


def test_github_watch_emits_releases_and_path_matching_commits(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/releases"):
            return httpx.Response(200, json=RELEASES)
        if path.endswith("/commits"):
            return httpx.Response(200, json=COMMITS)
        return httpx.Response(404)

    f = GitHubWatchFetcher(
        source=_src(),
        errors_path=tmp_path / "e.jsonl",
        watermarks_path=tmp_path / "w.json",
        transport=httpx.MockTransport(handler),
    )
    items = f.fetch_items()
    titles = {i["title"] for i in items}
    # The release and the recipes commit are included; the README commit is filtered out.
    assert "Release v1.2.0 — agentic eval helpers" in titles
    assert any("recipes/" in i["title"] or "MCP server recipe" in i["title"] for i in items)
    assert not any("Fix typo" in i["title"] for i in items)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_github_watch.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/github_watch.py`**

```python
from __future__ import annotations

import os
from typing import Any

import httpx

from scripts.common import compute_item_id, iso_now
from scripts.fetchers.base import BaseFetcher


GITHUB_API = "https://api.github.com"


class GitHubWatchFetcher(BaseFetcher):
    """Watches a repo for releases and commits that touch configured paths.

    Config keys:
      repo (required): "<owner>/<name>"
      watch_paths: list of path prefixes (e.g. ["recipes/"]). Commits not touching
                   any prefix are dropped. Empty list = include all commits.
      include_releases: bool, default True
    """

    def __init__(self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport

    def _client(self) -> httpx.Client:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return httpx.Client(transport=self._transport, timeout=30.0, headers=headers)

    def fetch_items(self) -> list[dict[str, Any]]:
        cfg = self.source.config
        repo: str = cfg["repo"]
        watch_paths: list[str] = list(cfg.get("watch_paths") or [])
        include_releases: bool = bool(cfg.get("include_releases", True))
        fetched_at = iso_now()
        out: list[dict[str, Any]] = []

        with self._client() as client:
            if include_releases:
                resp = client.get(f"{GITHUB_API}/repos/{repo}/releases", params={"per_page": 10})
                resp.raise_for_status()
                for r in resp.json():
                    title = f"Release {r.get('name') or r.get('tag_name')}"
                    url = r.get("html_url") or ""
                    if not url:
                        continue
                    item_id = compute_item_id(title, url)
                    out.append(
                        {
                            "item_id": item_id,
                            "title": title,
                            "url": url,
                            "source_id": self.source.id,
                            "signal_type": list(self.source.signal_type),
                            "audience_tags": list(self.source.audience_tags),
                            "timestamp": r.get("published_at"),
                            "raw_text": (r.get("body") or "")[:2000],
                            "metrics": {"score": 0, "comments": 0, "stars": None},
                            "relevance_tags": list(self.source.relevance_tags),
                            "fetched_at": fetched_at,
                            "dedup_key": item_id,
                        }
                    )

            resp = client.get(f"{GITHUB_API}/repos/{repo}/commits", params={"per_page": 30})
            resp.raise_for_status()
            for c in resp.json():
                msg = ((c.get("commit") or {}).get("message") or "").splitlines()[0]
                url = c.get("html_url") or ""
                if not msg or not url:
                    continue
                files = [f.get("filename", "") for f in (c.get("files") or [])]
                if watch_paths:
                    if not any(any(fn.startswith(p) for p in watch_paths) for fn in files):
                        continue
                title = f"Commit: {msg}"
                if watch_paths and files:
                    matched = [fn for fn in files if any(fn.startswith(p) for p in watch_paths)]
                    if matched:
                        title = f"Commit ({', '.join(matched[:2])}): {msg}"
                item_id = compute_item_id(title, url)
                out.append(
                    {
                        "item_id": item_id,
                        "title": title,
                        "url": url,
                        "source_id": self.source.id,
                        "signal_type": list(self.source.signal_type),
                        "audience_tags": list(self.source.audience_tags),
                        "timestamp": ((c.get("commit") or {}).get("author") or {}).get("date"),
                        "raw_text": msg[:2000],
                        "metrics": {"score": 0, "comments": 0, "stars": None},
                        "relevance_tags": list(self.source.relevance_tags),
                        "fetched_at": fetched_at,
                        "dedup_key": item_id,
                    }
                )
        return out
```

- [ ] **Step 4: Register in `_select_fetcher`**

```python
if source.type == "github_watch":
    from scripts.fetchers.github_watch import GitHubWatchFetcher
    return GitHubWatchFetcher
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_github_watch.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/fetchers/github_watch.py tests/test_github_watch.py scripts/ingest.py
git commit -m "feat: GitHub watch fetcher (releases + path-filtered commits)"
```

---

## Task 16: `scripts/fetchers/scrape.py` — HTML scrape with BeautifulSoup

**Files:**
- Create: `scripts/fetchers/scrape.py`
- Test: `tests/test_scrape.py`

- [ ] **Step 1: Write failing tests**

`tests/test_scrape.py`:

```python
from __future__ import annotations

from pathlib import Path

import httpx

from scripts.fetchers.scrape import ScrapeFetcher
from scripts.sources import PreFilter, SourceConfig


HTML = """
<html><body>
<ul id="trending">
  <li><a href="/repo/a"><span class="name">repo-a</span><span class="stars">2400</span></a></li>
  <li><a href="/repo/b"><span class="name">repo-b</span><span class="stars">300</span></a></li>
</ul>
</body></html>
"""


def _src() -> SourceConfig:
    return SourceConfig(
        id="github-trending-python",
        name="GitHub Trending — Python",
        type="scrape",
        config={
            "url": "https://github.com/trending/python",
            "item_selector": "#trending li",
            "title_selector": ".name",
            "link_selector": "a",
            "score_selector": ".stars",
            "link_base": "https://github.com",
        },
        poll_cadence="daily",
        signal_type=["trend", "capability"],
        audience_tags=["hardcore_tech"],
        relevance_tags=["github", "python"],
        pre_filter=PreFilter(min_engagement=0, recency_window_days=14, dedup_key="title_url"),
        priority=2,
        fragility_tier="moderate",
    )


def test_scrape_fetcher_extracts_items(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=HTML)

    f = ScrapeFetcher(
        source=_src(),
        errors_path=tmp_path / "e.jsonl",
        watermarks_path=tmp_path / "w.json",
        transport=httpx.MockTransport(handler),
    )
    items = f.fetch_items()
    assert len(items) == 2
    a, b = items
    assert a["title"] == "repo-a"
    assert a["url"] == "https://github.com/repo/a"
    assert a["metrics"]["score"] == 2400
    assert b["metrics"]["score"] == 300
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scrape.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/scrape.py`**

```python
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from scripts.common import compute_item_id, iso_now
from scripts.fetchers.base import BaseFetcher


def _coerce_int(text: str | None) -> int:
    if not text:
        return 0
    cleaned = text.strip().replace(",", "").replace("+", "")
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


class ScrapeFetcher(BaseFetcher):
    """Generic HTML fetcher with CSS selectors.

    Config keys:
      url (required)
      item_selector (required): CSS selector that yields one element per item
      title_selector (required): CSS selector relative to item element
      link_selector (required): CSS selector relative to item element (uses href attr)
      score_selector (optional): for engagement-like metrics
      link_base (optional): prefix for relative hrefs
    """

    def __init__(self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport

    def fetch_items(self) -> list[dict[str, Any]]:
        cfg = self.source.config
        url: str = cfg["url"]
        item_sel: str = cfg["item_selector"]
        title_sel: str = cfg["title_selector"]
        link_sel: str = cfg["link_selector"]
        score_sel: str | None = cfg.get("score_selector")
        link_base: str = cfg.get("link_base", "")
        fetched_at = iso_now()

        with httpx.Client(transport=self._transport, timeout=30.0) as client:
            resp = client.get(url, headers={"User-Agent": "radar/0.1"})
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        out: list[dict[str, Any]] = []
        for el in soup.select(item_sel):
            title_el = el.select_one(title_sel)
            link_el = el.select_one(link_sel)
            if not title_el or not link_el:
                continue
            title = title_el.get_text(strip=True)
            href = link_el.get("href") or ""
            if not title or not href:
                continue
            full_url = urljoin(link_base or url, href)
            score = 0
            if score_sel:
                score_el = el.select_one(score_sel)
                if score_el:
                    score = _coerce_int(score_el.get_text(strip=True))
            item_id = compute_item_id(title, full_url)
            out.append(
                {
                    "item_id": item_id,
                    "title": title,
                    "url": full_url,
                    "source_id": self.source.id,
                    "signal_type": list(self.source.signal_type),
                    "audience_tags": list(self.source.audience_tags),
                    "timestamp": fetched_at,
                    "raw_text": title,
                    "metrics": {"score": score, "comments": 0, "stars": None},
                    "relevance_tags": list(self.source.relevance_tags),
                    "fetched_at": fetched_at,
                    "dedup_key": item_id,
                }
            )
        return out
```

- [ ] **Step 4: Register in `_select_fetcher`**

```python
if source.type == "scrape":
    from scripts.fetchers.scrape import ScrapeFetcher
    return ScrapeFetcher
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_scrape.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/fetchers/scrape.py tests/test_scrape.py scripts/ingest.py
git commit -m "feat: HTML scrape fetcher (BeautifulSoup, generic selectors)"
```

---

## Task 17: Reddit support — extend `json_api.py` with a `RedditJSONFetcher`

**Files:**
- Modify: `scripts/fetchers/json_api.py`
- Test: extend `tests/test_json_api.py`

Reddit exposes `.json` endpoints. Top-of-week for a subreddit lives at `https://www.reddit.com/r/<sub>/top.json?t=week`.

- [ ] **Step 1: Write failing test for Reddit normalization**

Append to `tests/test_json_api.py`:

```python
from scripts.fetchers.json_api import RedditJSONFetcher


REDDIT_RESPONSE = {
    "data": {
        "children": [
            {
                "data": {
                    "id": "abcd1",
                    "title": "Multi-agent workflow with Claude",
                    "url": "https://www.reddit.com/r/ClaudeAI/comments/abcd1/multi_agent",
                    "permalink": "/r/ClaudeAI/comments/abcd1/multi_agent",
                    "score": 412,
                    "num_comments": 78,
                    "created_utc": 1748284800,  # 2025-05-26 in UTC
                    "selftext": "I built...",
                    "subreddit": "ClaudeAI",
                }
            }
        ]
    }
}


def test_reddit_fetcher_normalizes_top_posts(tmp_path: Path):
    src = SourceConfig(
        id="r-claudeai",
        name="r/ClaudeAI top weekly",
        type="json_api",
        config={
            "kind": "reddit",
            "subreddit": "ClaudeAI",
            "timeframe": "week",
        },
        poll_cadence="weekly",
        signal_type=["pattern", "workflow"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["claude", "reddit"],
        pre_filter=PreFilter(min_engagement=10, recency_window_days=14, dedup_key="title_url"),
        priority=1,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/r/ClaudeAI/top.json" in str(request.url)
        assert request.url.params["t"] == "week"
        return httpx.Response(200, json=REDDIT_RESPONSE)

    f = RedditJSONFetcher(
        source=src,
        errors_path=tmp_path / "e.jsonl",
        watermarks_path=tmp_path / "w.json",
        transport=httpx.MockTransport(handler),
    )
    items = f.fetch_items()
    assert len(items) == 1
    i = items[0]
    assert i["title"] == "Multi-agent workflow with Claude"
    assert i["url"] == "https://www.reddit.com/r/ClaudeAI/comments/abcd1/multi_agent"
    assert i["metrics"]["score"] == 412
    assert i["metrics"]["comments"] == 78
    assert i["timestamp"].endswith("Z")
```

- [ ] **Step 2: Add `RedditJSONFetcher` to `scripts/fetchers/json_api.py`**

```python
from datetime import datetime, timezone

# ... append below HNAlgoliaFetcher:

class RedditJSONFetcher(BaseFetcher):
    """Reddit subreddit top posts via the public `.json` endpoint.

    Config keys:
      subreddit (required)
      timeframe: hour | day | week | month | year | all (default: week)
      limit: int (default 25)
    """

    def __init__(self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport

    def fetch_items(self) -> list[dict[str, Any]]:
        cfg = self.source.config
        sub: str = cfg["subreddit"]
        timeframe: str = cfg.get("timeframe", "week")
        limit: int = int(cfg.get("limit", 25))
        url = f"https://www.reddit.com/r/{sub}/top.json"
        with httpx.Client(transport=self._transport, timeout=30.0, headers={"User-Agent": "radar/0.1"}) as client:
            resp = client.get(url, params={"t": timeframe, "limit": str(limit)})
            resp.raise_for_status()
            payload = resp.json()
        fetched_at = iso_now()
        out: list[dict[str, Any]] = []
        for child in (payload.get("data") or {}).get("children") or []:
            d = child.get("data") or {}
            title = (d.get("title") or "").strip()
            url_ = d.get("url") or d.get("permalink")
            if d.get("permalink") and not (url_ or "").startswith("http"):
                url_ = f"https://www.reddit.com{d['permalink']}"
            if not title or not url_:
                continue
            created = d.get("created_utc")
            ts = (
                datetime.fromtimestamp(int(created), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if created
                else None
            )
            item_id = compute_item_id(title, url_)
            out.append(
                {
                    "item_id": item_id,
                    "title": title,
                    "url": url_,
                    "source_id": self.source.id,
                    "signal_type": list(self.source.signal_type),
                    "audience_tags": list(self.source.audience_tags),
                    "timestamp": ts,
                    "raw_text": (d.get("selftext") or "")[:2000],
                    "metrics": {
                        "score": d.get("score") or 0,
                        "comments": d.get("num_comments") or 0,
                        "stars": None,
                    },
                    "relevance_tags": list(self.source.relevance_tags) + [f"r/{sub}"],
                    "fetched_at": fetched_at,
                    "dedup_key": item_id,
                }
            )
        return out
```

- [ ] **Step 3: Update `_select_fetcher` in `scripts/ingest.py`**

```python
if source.type == "json_api":
    if source.id == "hn-algolia":
        return HNAlgoliaFetcher
    if source.config.get("kind") == "reddit":
        from scripts.fetchers.json_api import RedditJSONFetcher
        return RedditJSONFetcher
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_json_api.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/fetchers/json_api.py tests/test_json_api.py scripts/ingest.py
git commit -m "feat: Reddit JSON fetcher (top-of-timeframe per subreddit)"
```

---

## Task 18: Source YAMLs for v1's 9 additional sources

**Files:**
- Create: `sources/r-claudeai.yaml`
- Create: `sources/r-machinelearning.yaml`
- Create: `sources/r-technicalwriting.yaml`
- Create: `sources/anthropic-blog.yaml`
- Create: `sources/anthropic-cookbook.yaml`
- Create: `sources/arxiv-cs-ai.yaml`
- Create: `sources/arxiv-cs-cl.yaml`
- Create: `sources/hf-daily-papers.yaml`
- Create: `sources/github-trending-python.yaml`
- Create: `sources/mintlify-changelog.yaml`

- [ ] **Step 1: Write all 10 YAML files**

`sources/r-claudeai.yaml`:

```yaml
id: r-claudeai
name: r/ClaudeAI top weekly
type: json_api
config:
  kind: reddit
  subreddit: ClaudeAI
  timeframe: week
  limit: 25
poll_cadence: weekly
signal_type: [pattern, workflow, capability]
audience_tags: [hardcore_tech, devs_curious_ai]
relevance_tags: [claude, reddit]
pre_filter: {min_engagement: 50, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: moderate
staleness_threshold_days: 14
```

`sources/r-machinelearning.yaml`:

```yaml
id: r-machinelearning
name: r/MachineLearning top weekly
type: json_api
config: {kind: reddit, subreddit: MachineLearning, timeframe: week, limit: 25}
poll_cadence: weekly
signal_type: [pattern, news]
audience_tags: [hardcore_tech]
relevance_tags: [ml, reddit]
pre_filter: {min_engagement: 100, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: moderate
```

`sources/r-technicalwriting.yaml`:

```yaml
id: r-technicalwriting
name: r/technicalwriting top weekly
type: json_api
config: {kind: reddit, subreddit: technicalwriting, timeframe: week, limit: 25}
poll_cadence: weekly
signal_type: [pain_point, pattern]
audience_tags: [tech_writer]
relevance_tags: [techwriting, reddit]
pre_filter: {min_engagement: 10, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: moderate
```

`sources/anthropic-blog.yaml`:

```yaml
id: anthropic-blog
name: Anthropic Blog
type: rss
config: {url: https://www.anthropic.com/news/rss.xml}
poll_cadence: daily
signal_type: [capability, news]
audience_tags: [hardcore_tech, devs_curious_ai, tech_writer]
relevance_tags: [anthropic, claude]
pre_filter: {min_engagement: 0, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: stable
```

`sources/anthropic-cookbook.yaml`:

```yaml
id: anthropic-cookbook
name: Anthropic Cookbook
type: github_watch
config:
  repo: anthropics/anthropic-cookbook
  watch_paths: [recipes/, skills/]
  include_releases: true
poll_cadence: weekly
signal_type: [capability, workflow]
audience_tags: [hardcore_tech, devs_curious_ai]
relevance_tags: [claude, recipes, agentic]
pre_filter: {min_engagement: 0, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: stable
```

`sources/arxiv-cs-ai.yaml`:

```yaml
id: arxiv-cs-ai
name: arXiv cs.AI
type: rss
config: {url: https://export.arxiv.org/rss/cs.AI}
poll_cadence: daily
signal_type: [pattern]
audience_tags: [hardcore_tech]
relevance_tags: [arxiv, ai]
pre_filter: {min_engagement: 0, recency_window_days: 7, dedup_key: title_url}
priority: 2
fragility_tier: stable
```

`sources/arxiv-cs-cl.yaml`:

```yaml
id: arxiv-cs-cl
name: arXiv cs.CL
type: rss
config: {url: https://export.arxiv.org/rss/cs.CL}
poll_cadence: daily
signal_type: [pattern]
audience_tags: [hardcore_tech]
relevance_tags: [arxiv, nlp]
pre_filter: {min_engagement: 0, recency_window_days: 7, dedup_key: title_url}
priority: 2
fragility_tier: stable
```

`sources/hf-daily-papers.yaml`:

```yaml
id: hf-daily-papers
name: Hugging Face Daily Papers
type: rss
config: {url: https://huggingface.co/papers/rss}
poll_cadence: daily
signal_type: [pattern, capability]
audience_tags: [hardcore_tech, devs_curious_ai]
relevance_tags: [huggingface, papers]
pre_filter: {min_engagement: 0, recency_window_days: 7, dedup_key: title_url}
priority: 2
fragility_tier: moderate
```

`sources/github-trending-python.yaml`:

```yaml
id: github-trending-python
name: GitHub Trending — Python (daily)
type: scrape
config:
  url: https://github.com/trending/python?since=daily
  item_selector: "article.Box-row"
  title_selector: "h2 a"
  link_selector: "h2 a"
  score_selector: "a.Link--muted[href$='/stargazers']"
  link_base: "https://github.com"
poll_cadence: daily
signal_type: [trend, capability]
audience_tags: [hardcore_tech, devs_curious_ai]
relevance_tags: [github, python, trending]
pre_filter: {min_engagement: 100, recency_window_days: 14, dedup_key: title_url}
priority: 2
fragility_tier: fragile
staleness_threshold_days: 14
```

`sources/mintlify-changelog.yaml`:

```yaml
id: mintlify-changelog
name: Mintlify Changelog
type: rss
config: {url: https://mintlify.com/changelog/rss.xml}
poll_cadence: weekly
signal_type: [capability]
audience_tags: [tech_writer]
relevance_tags: [mintlify, docs-tools]
pre_filter: {min_engagement: 0, recency_window_days: 21, dedup_key: title_url}
priority: 2
fragility_tier: moderate
```

> Note: feed URLs and CSS selectors can drift. The fragility_tier value tags how likely each is to break. The staleness watermark surfaces breakage in the next Memory Thread (R11).

- [ ] **Step 2: Validate all YAMLs load**

```bash
python -c "from pathlib import Path; from scripts.sources import load_all_sources; ss = load_all_sources(Path('sources')); print(len(ss), 'sources loaded'); [print(s.id, s.type, s.fragility_tier) for s in ss]"
```

Expected: 10 sources listed.

- [ ] **Step 3: Commit**

```bash
git add sources/*.yaml
git commit -m "feat: v1 source YAMLs (10 sources, mixed types)"
```

---

## Task 19: `scripts/fetchers/pain_point.py` — Reddit/HN deep comment harvester

**Files:**
- Create: `scripts/fetchers/pain_point.py`
- Create: `sources/pain-point-reddit-ai.yaml`
- Test: `tests/test_pain_point.py`

This is the hardest v1 component (R1 in spec). Strategy: per target subreddit, fetch top N threads of the week, then fetch top M comments per thread. Surface comments above an upvote floor. The synthesis layer (subagent in the Map phase for the `pain_points` group) does the "is this a question / expressed pain?" filtering — the fetcher only collects and normalizes.

- [ ] **Step 1: Write failing tests**

`tests/test_pain_point.py`:

```python
from __future__ import annotations

from pathlib import Path

import httpx

from scripts.fetchers.pain_point import RedditCommentHarvester
from scripts.sources import PreFilter, SourceConfig


THREADS = {
    "data": {
        "children": [
            {"data": {"id": "t1", "title": "Eval struggles", "permalink": "/r/ClaudeAI/comments/t1/eval_struggles", "score": 50}},
            {"data": {"id": "t2", "title": "MCP doubts", "permalink": "/r/ClaudeAI/comments/t2/mcp_doubts", "score": 20}},
        ]
    }
}

COMMENTS_T1 = [
    None,
    {
        "data": {
            "children": [
                {"kind": "t1", "data": {"id": "c11", "body": "How do you eval agents reliably?", "score": 25, "permalink": "/r/ClaudeAI/comments/t1/eval_struggles/c11", "created_utc": 1748284800}},
                {"kind": "t1", "data": {"id": "c12", "body": "Anyone else?", "score": 1, "permalink": "/r/ClaudeAI/comments/t1/eval_struggles/c12", "created_utc": 1748284800}},
            ]
        }
    },
]
COMMENTS_T2 = [
    None,
    {
        "data": {
            "children": [
                {"kind": "t1", "data": {"id": "c21", "body": "MCP servers feel half-documented.", "score": 12, "permalink": "/r/ClaudeAI/comments/t2/mcp_doubts/c21", "created_utc": 1748284800}},
            ]
        }
    },
]


def _src() -> SourceConfig:
    return SourceConfig(
        id="pain-point-reddit-claudeai",
        name="Pain points — r/ClaudeAI",
        type="pain_point",
        config={
            "kind": "reddit_comments",
            "subreddit": "ClaudeAI",
            "thread_timeframe": "week",
            "threads_per_run": 5,
            "comments_per_thread": 10,
            "min_comment_score": 3,
        },
        poll_cadence="weekly",
        signal_type=["pain_point"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["claude", "pain_point"],
        pre_filter=PreFilter(min_engagement=0, recency_window_days=14, dedup_key="title_url"),
        priority=1,
        fragility_tier="fragile",
    )


def test_pain_point_harvester_collects_high_score_comments(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        path = str(request.url)
        if "/top.json" in path:
            return httpx.Response(200, json=THREADS)
        if "/comments/t1/" in path:
            return httpx.Response(200, json=COMMENTS_T1)
        if "/comments/t2/" in path:
            return httpx.Response(200, json=COMMENTS_T2)
        return httpx.Response(404)

    f = RedditCommentHarvester(
        source=_src(),
        errors_path=tmp_path / "e.jsonl",
        watermarks_path=tmp_path / "w.json",
        transport=httpx.MockTransport(handler),
    )
    items = f.fetch_items()
    # Comment c12 has score 1, below the floor of 3 — dropped.
    bodies = {i["raw_text"] for i in items}
    assert "How do you eval agents reliably?" in bodies
    assert "MCP servers feel half-documented." in bodies
    assert "Anyone else?" not in bodies
    # Each item is parented to its thread title for synthesis context.
    parent_titles = {i["title"] for i in items}
    assert any("Eval struggles" in t for t in parent_titles)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pain_point.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/pain_point.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from scripts.common import compute_item_id, iso_now
from scripts.fetchers.base import BaseFetcher


class RedditCommentHarvester(BaseFetcher):
    """For each of the top N threads in a subreddit (over a timeframe), pull the
    top M comments and surface those whose score >= min_comment_score.

    The fetcher does NOT do question-form filtering. That happens in the Map-
    phase subagent for the `pain_points` group, which uses Claude to judge each
    item. This separation keeps the fetcher cheap and the LLM-side work co-
    located with the rest of the synthesis.

    Config keys:
      subreddit (required)
      thread_timeframe (default: week)
      threads_per_run (default: 5)
      comments_per_thread (default: 10)
      min_comment_score (default: 3)
    """

    def __init__(self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport

    def fetch_items(self) -> list[dict[str, Any]]:
        cfg = self.source.config
        sub: str = cfg["subreddit"]
        timeframe: str = cfg.get("thread_timeframe", "week")
        threads_n: int = int(cfg.get("threads_per_run", 5))
        comments_n: int = int(cfg.get("comments_per_thread", 10))
        min_score: int = int(cfg.get("min_comment_score", 3))
        fetched_at = iso_now()
        out: list[dict[str, Any]] = []

        with httpx.Client(transport=self._transport, timeout=30.0, headers={"User-Agent": "radar/0.1"}) as client:
            top = client.get(f"https://www.reddit.com/r/{sub}/top.json", params={"t": timeframe, "limit": str(threads_n)})
            top.raise_for_status()
            threads = (top.json().get("data") or {}).get("children") or []
            for child in threads[:threads_n]:
                td = child.get("data") or {}
                thread_id = td.get("id")
                thread_title = (td.get("title") or "").strip()
                thread_permalink = td.get("permalink") or ""
                if not thread_id or not thread_permalink:
                    continue
                comm = client.get(f"https://www.reddit.com{thread_permalink}.json", params={"limit": str(comments_n), "sort": "top"})
                comm.raise_for_status()
                payload = comm.json()
                if not isinstance(payload, list) or len(payload) < 2:
                    continue
                comments = (payload[1].get("data") or {}).get("children") or []
                for c in comments[:comments_n]:
                    cd = c.get("data") or {}
                    body = (cd.get("body") or "").strip()
                    score = int(cd.get("score") or 0)
                    if not body or score < min_score:
                        continue
                    permalink = cd.get("permalink") or ""
                    if not permalink:
                        continue
                    url = f"https://www.reddit.com{permalink}"
                    title = f"{thread_title} — comment"
                    created = cd.get("created_utc")
                    ts = (
                        datetime.fromtimestamp(int(created), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        if created
                        else fetched_at
                    )
                    item_id = compute_item_id(title, url)
                    out.append(
                        {
                            "item_id": item_id,
                            "title": title,
                            "url": url,
                            "source_id": self.source.id,
                            "signal_type": list(self.source.signal_type),
                            "audience_tags": list(self.source.audience_tags),
                            "timestamp": ts,
                            "raw_text": body[:2000],
                            "metrics": {"score": score, "comments": 0, "stars": None},
                            "relevance_tags": list(self.source.relevance_tags) + [f"r/{sub}", "pain_point_raw"],
                            "fetched_at": fetched_at,
                            "dedup_key": item_id,
                        }
                    )
        return out
```

- [ ] **Step 4: Register pain_point in `_select_fetcher`**

```python
if source.type == "pain_point":
    from scripts.fetchers.pain_point import RedditCommentHarvester
    if source.config.get("kind") == "reddit_comments":
        return RedditCommentHarvester
    raise NotImplementedError(f"No pain_point fetcher for kind={source.config.get('kind')}")
```

- [ ] **Step 5: Write the first pain-point source YAML**

`sources/pain-point-reddit-ai.yaml`:

```yaml
id: pain-point-reddit-claudeai
name: Pain points — r/ClaudeAI
type: pain_point
config:
  kind: reddit_comments
  subreddit: ClaudeAI
  thread_timeframe: week
  threads_per_run: 5
  comments_per_thread: 10
  min_comment_score: 3
poll_cadence: weekly
signal_type: [pain_point]
audience_tags: [hardcore_tech, devs_curious_ai]
relevance_tags: [claude, pain_point]
pre_filter: {min_engagement: 0, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: fragile
staleness_threshold_days: 14
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_pain_point.py -v
```

Expected: 1 passed.

- [ ] **Step 7: Commit**

```bash
git add scripts/fetchers/pain_point.py sources/pain-point-reddit-ai.yaml tests/test_pain_point.py scripts/ingest.py
git commit -m "feat: Reddit pain-point harvester (top-thread → top-comment dive)"
```

---

## Task 20: GitHub Actions cron + concurrency safeguards (R12)

**Files:**
- Create: `.github/workflows/ingest.yml`
- Modify: `scripts/ingest.py` (the preflight already exists; make sure it runs in the workflow path too)

- [ ] **Step 1: Write the workflow**

`.github/workflows/ingest.yml`:

```yaml
name: ingest

on:
  schedule:
    # Sunday 02:00 UTC (spec Section 4.2)
    - cron: "0 2 * * 0"
  workflow_dispatch:

# Prevent two runs writing state simultaneously.
concurrency:
  group: radar-ingest
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  ingest:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          # We need the full history to rebase cleanly on every run.
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Configure git identity
        run: |
          git config user.name  "radar-bot"
          git config user.email "radar-bot@users.noreply.github.com"

      - name: Ingest
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # CI runs from a fresh checkout — preflight pull would no-op anyway,
          # but we still call it for parity with the local path. R12.
          python -m scripts.ingest

      - name: Commit raw outputs and state
        run: |
          # R12: cron may only write raw/, state/signals.jsonl, state/fetch-errors.jsonl,
          # state/watermarks.json. Never trajectory.md / feedback.md / profile.md / catalog.md.
          git add raw/ state/signals.jsonl state/fetch-errors.jsonl state/watermarks.json
          if git diff --cached --quiet; then
            echo "no ingestion changes"
          else
            DATE=$(date -u +%Y-%m-%d)
            git commit -m "ingest: $DATE"
            # Rebase guard: pull --rebase then push. If conflicts arise, fail
            # the workflow loudly so the operator notices on Monday.
            git pull --rebase
            git push
          fi
```

- [ ] **Step 2: Add a test that verifies `ingest.py` never writes operator-edited files**

Append to `tests/test_ingest.py`:

```python
def test_run_ingest_does_not_touch_operator_edited_files(paths: IngestPaths):
    _write_hn_source(paths)
    # Seed operator-edited files with known content.
    profile = paths.sources_dir.parent / "state" / "profile.md"
    trajectory = paths.sources_dir.parent / "state" / "trajectory.md"
    profile.write_text("OPERATOR-PROFILE")
    trajectory.write_text("OPERATOR-TRAJECTORY")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=HN_RESPONSE)

    run_ingest(paths, run_date="2026-05-27", http_transport=httpx.MockTransport(handler))

    assert profile.read_text() == "OPERATOR-PROFILE"
    assert trajectory.read_text() == "OPERATOR-TRAJECTORY"
```

Run:

```bash
pytest tests/test_ingest.py -v
```

Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ingest.yml tests/test_ingest.py
git commit -m "feat: GitHub Actions cron (Sun 02:00 UTC) + operator-file write-guard test"
```

---

## Task 21: Update `sources/_groups.yaml` for v1 grouping

**Files:**
- Modify: `sources/_groups.yaml`

- [ ] **Step 1: Rewrite `_groups.yaml` with v1 groups**

```yaml
# MRR Map-phase grouping. One subagent per group.
groups:
  hn_general:
    - hn-algolia
  reddit_ai:
    - r-claudeai
    - r-machinelearning
  reddit_techwriting:
    - r-technicalwriting
  capability_claude:
    - anthropic-blog
    - anthropic-cookbook
  papers:
    - arxiv-cs-ai
    - arxiv-cn-cl    # NOTE: keep spellings in sync with the source YAML id
    - arxiv-cs-cl
    - hf-daily-papers
  trends:
    - github-trending-python
  capability_docs_tools:
    - mintlify-changelog
  pain_points:
    - pain-point-reddit-claudeai
```

Fix the typo before committing: only the valid IDs (`arxiv-cs-ai`, `arxiv-cs-cl`, `hf-daily-papers`) belong under `papers`.

Corrected:

```yaml
groups:
  hn_general:
    - hn-algolia
  reddit_ai:
    - r-claudeai
    - r-machinelearning
  reddit_techwriting:
    - r-technicalwriting
  capability_claude:
    - anthropic-blog
    - anthropic-cookbook
  papers:
    - arxiv-cs-ai
    - arxiv-cs-cl
    - hf-daily-papers
  trends:
    - github-trending-python
  capability_docs_tools:
    - mintlify-changelog
  pain_points:
    - pain-point-reddit-claudeai
```

- [ ] **Step 2: Sanity check — every source ID in the registry appears in exactly one group**

```bash
python <<'PY'
from pathlib import Path
import yaml
from scripts.sources import load_all_sources

sources = {s.id for s in load_all_sources(Path("sources"))}
groups = yaml.safe_load(Path("sources/_groups.yaml").read_text())["groups"]
grouped = {sid for ids in groups.values() for sid in ids}
missing = sources - grouped
extra = grouped - sources
print("sources:", len(sources))
print("grouped:", len(grouped))
print("missing from any group:", missing)
print("referenced but not a source:", extra)
PY
```

Expected: both sets empty.

- [ ] **Step 3: Commit**

```bash
git add sources/_groups.yaml
git commit -m "chore: v1 MRR source groups"
```

---

## Task 22: Run digest 1, evaluate, log feedback

This is a manual evaluation task. No code.

- [ ] **Step 1: Run full v1 ingestion locally to seed raw/**

```bash
python -m scripts.ingest --skip-preflight
ls raw/$(date -u +%Y-%m-%d)/
```

Expected: 10 source JSON files (or 9 + an empty file if one fetcher failed — the cron must continue).

- [ ] **Step 2: Inspect `state/fetch-errors.jsonl`**

```bash
cat state/fetch-errors.jsonl
```

Note any sources that crashed; especially watch the `fragile` tier (github-trending-python, pain-point-reddit-claudeai). These will inform the v2 fragility tuning.

- [ ] **Step 3: Run `/radar` in Claude Code**

Verify (a) Map phase dispatches ~8 subagents in parallel, (b) `intermediate/*.md` files all written, (c) digest under 2000 words, (d) Memory Thread flags any stale fragile source.

- [ ] **Step 4: Operator marks 2–3 items Doing/Pass**

In session: feedback updates trajectory.md and feedback.md. Verify the writes happened.

- [ ] **Step 5: Tag the v1 milestone**

```bash
git tag v1.0
git push --tags
```

(Skip push if no remote.)

**v1 acceptance criteria:**
- 10 sources ingest successfully (or fail with structured errors logged, not crashes).
- GitHub Actions workflow runs end-to-end on demand (`gh workflow run ingest`).
- `/radar` synthesizes a digest with at least 6 of 11 sections populated (sections 0, 1, 2, 3, 7, 9, 10 at minimum).
- Fragility tier flag works — manually edit `state/watermarks.json` to make a fragile source 30 days stale, run `/radar`, confirm Memory Thread flags it.
- Concurrency: edit `state/trajectory.md` locally without pushing, then run cron via `gh workflow run ingest`. Cron must not silently overwrite the local edit (the test in Task 20 covers the ingest side; behavior on push conflict is covered by the workflow's rebase-then-push step).

---

# v2 — Full Source Registry + Composite Fetchers + Maintenance

## Task 23: `scripts/fetchers/investor_signal.py` — composite funding aggregator

**Files:**
- Create: `scripts/fetchers/investor_signal.py`
- Create: `sources/investor-signal.yaml`
- Test: `tests/test_investor_signal.py`

The composite fetcher aggregates 5 sub-feeds (YC Launches, a16z, Sequoia, ProductHunt top of week, Crunchbase free filter). Each sub-feed is wrapped in its own try/except so one outage does not silence the others (R11 within a composite).

- [ ] **Step 1: Write failing tests**

`tests/test_investor_signal.py`:

```python
from __future__ import annotations

from pathlib import Path

import httpx

from scripts.fetchers.investor_signal import InvestorSignalFetcher
from scripts.sources import PreFilter, SourceConfig


YC_RSS = """<?xml version="1.0"?>
<rss><channel>
  <item>
    <title>Launch HN: FooLabs (YC W26) — Agentic eval platform</title>
    <link>https://news.ycombinator.com/item?id=1</link>
    <pubDate>Mon, 26 May 2026 12:00:00 +0000</pubDate>
    <description>Agentic eval...</description>
  </item>
</channel></rss>"""

A16Z_RSS = """<?xml version="1.0"?>
<rss><channel>
  <item>
    <title>The next wave of AI infra</title>
    <link>https://a16z.com/post-1</link>
    <pubDate>Mon, 26 May 2026 12:00:00 +0000</pubDate>
    <description>Investment thesis.</description>
  </item>
</channel></rss>"""


def _src() -> SourceConfig:
    return SourceConfig(
        id="investor-signal",
        name="Investor signal (composite)",
        type="investor_signal",
        config={
            "subfeeds": [
                {"name": "yc-launches", "kind": "rss", "url": "https://example.test/yc.rss"},
                {"name": "a16z", "kind": "rss", "url": "https://example.test/a16z.rss"},
                {"name": "broken", "kind": "rss", "url": "https://example.test/500.rss"},
            ]
        },
        poll_cadence="weekly",
        signal_type=["investor"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["investor", "funding"],
        pre_filter=PreFilter(min_engagement=0, recency_window_days=14, dedup_key="title_url"),
        priority=2,
        fragility_tier="moderate",
    )


def test_investor_signal_aggregates_and_isolates_subfeed_failures(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "yc.rss" in url:
            return httpx.Response(200, text=YC_RSS)
        if "a16z.rss" in url:
            return httpx.Response(200, text=A16Z_RSS)
        if "500.rss" in url:
            return httpx.Response(500, text="boom")
        return httpx.Response(404)

    f = InvestorSignalFetcher(
        source=_src(),
        errors_path=tmp_path / "e.jsonl",
        watermarks_path=tmp_path / "w.json",
        transport=httpx.MockTransport(handler),
    )
    items = f.fetch_items()
    titles = {i["title"] for i in items}
    assert any("FooLabs" in t for t in titles)
    assert any("next wave of AI infra" in t for t in titles)
    # The broken subfeed contributes nothing but does not crash the composite.
    # Each item carries the subfeed name in relevance_tags for downstream attribution.
    subfeeds = {tag for i in items for tag in i["relevance_tags"]}
    assert "subfeed:yc-launches" in subfeeds
    assert "subfeed:a16z" in subfeeds
    # Composite-level error log entries for the broken subfeed (R11 intra-composite).
    err_lines = (tmp_path / "e.jsonl").read_text().splitlines()
    assert any("broken" in l for l in err_lines)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_investor_signal.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/investor_signal.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from scripts.common import (
    compute_item_id,
    iso_now,
    log_fetch_error,
)
from scripts.fetchers.base import BaseFetcher


def _struct_time_to_iso(parsed: Any) -> str | None:
    if not parsed:
        return None
    try:
        y, m, d, hh, mm, ss = parsed[:6]
        return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None


class InvestorSignalFetcher(BaseFetcher):
    """Composite fetcher that aggregates multiple investor-related sub-feeds.

    Config keys:
      subfeeds (required): list of {name, kind, url, ...} dicts. Supported kinds:
        - rss
        - json_api  (with `endpoint` and optional `query_params`)
      Each sub-feed runs in its own try/except so one outage does not block the
      rest (R11, applied intra-composite).
    """

    def __init__(self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport

    def fetch_items(self) -> list[dict[str, Any]]:
        cfg = self.source.config
        subfeeds: list[dict[str, Any]] = cfg.get("subfeeds") or []
        fetched_at = iso_now()
        out: list[dict[str, Any]] = []

        with httpx.Client(transport=self._transport, timeout=30.0, headers={"User-Agent": "radar/0.1"}) as client:
            for sf in subfeeds:
                name = sf.get("name", "unknown")
                try:
                    items = self._fetch_subfeed(client, sf, fetched_at, name)
                    out.extend(items)
                except BaseException as exc:  # noqa: BLE001
                    log_fetch_error(
                        self.errors_path,
                        source_id=f"{self.source.id}:{name}",
                        exc=exc,
                    )
        return out

    def _fetch_subfeed(
        self,
        client: httpx.Client,
        sf: dict[str, Any],
        fetched_at: str,
        name: str,
    ) -> list[dict[str, Any]]:
        kind = sf.get("kind")
        out: list[dict[str, Any]] = []
        if kind == "rss":
            url: str = sf["url"]
            resp = client.get(url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for entry in feed.get("entries") or []:
                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()
                if not title or not link:
                    continue
                item_id = compute_item_id(title, link)
                out.append(
                    {
                        "item_id": item_id,
                        "title": title,
                        "url": link,
                        "source_id": self.source.id,
                        "signal_type": list(self.source.signal_type),
                        "audience_tags": list(self.source.audience_tags),
                        "timestamp": _struct_time_to_iso(entry.get("published_parsed")),
                        "raw_text": (entry.get("summary") or "")[:2000],
                        "metrics": {"score": 0, "comments": 0, "stars": None},
                        "relevance_tags": list(self.source.relevance_tags) + [f"subfeed:{name}"],
                        "fetched_at": fetched_at,
                        "dedup_key": item_id,
                    }
                )
        elif kind == "json_api":
            endpoint: str = sf["endpoint"]
            params: dict[str, Any] = dict(sf.get("query_params") or {})
            resp = client.get(endpoint, params=params)
            resp.raise_for_status()
            payload = resp.json()
            # Subfeeds may have wildly different JSON shapes. The pattern below
            # handles ProductHunt-style and Crunchbase-style with explicit
            # `title_path` / `url_path` selectors.
            items_path: str = sf.get("items_path", "items")
            items = payload
            for part in items_path.split("."):
                if not part:
                    continue
                items = (items or {}).get(part) or []
            for item in items:
                title = (item.get(sf.get("title_field", "title")) or "").strip()
                url = (item.get(sf.get("url_field", "url")) or "").strip()
                if not title or not url:
                    continue
                item_id = compute_item_id(title, url)
                out.append(
                    {
                        "item_id": item_id,
                        "title": title,
                        "url": url,
                        "source_id": self.source.id,
                        "signal_type": list(self.source.signal_type),
                        "audience_tags": list(self.source.audience_tags),
                        "timestamp": item.get(sf.get("timestamp_field", "created_at")),
                        "raw_text": (item.get(sf.get("text_field", "description")) or "")[:2000],
                        "metrics": {"score": int(item.get(sf.get("score_field", "votes_count")) or 0), "comments": 0, "stars": None},
                        "relevance_tags": list(self.source.relevance_tags) + [f"subfeed:{name}"],
                        "fetched_at": fetched_at,
                        "dedup_key": item_id,
                    }
                )
        else:
            raise ValueError(f"unknown subfeed kind: {kind!r}")
        return out
```

- [ ] **Step 4: Write `sources/investor-signal.yaml`**

```yaml
id: investor-signal
name: Investor signal (composite)
type: investor_signal
config:
  subfeeds:
    - {name: yc-launches, kind: rss, url: https://news.ycombinator.com/launches.rss}
    - {name: a16z,        kind: rss, url: https://a16z.com/feed/}
    - {name: sequoia,     kind: rss, url: https://www.sequoiacap.com/feed/}
    - name: producthunt
      kind: json_api
      endpoint: https://www.producthunt.com/frontend/graphql
      query_params: {}
      items_path: data.posts.edges
      title_field: node
      url_field: node
    - {name: betalist,    kind: rss, url: https://betalist.com/feed}
poll_cadence: weekly
signal_type: [investor]
audience_tags: [hardcore_tech, devs_curious_ai]
relevance_tags: [investor, funding]
pre_filter: {min_engagement: 0, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: moderate
staleness_threshold_days: 21
```

> The ProductHunt subfeed config above is a placeholder shape — the real endpoint requires a developer token. Add a `token_env: PRODUCTHUNT_TOKEN` field plus an auth header when the operator decides to wire it. Until then, ProductHunt subfeed will fail-soft and the composite still emits YC + a16z + Sequoia + BetaList.

- [ ] **Step 5: Register in `_select_fetcher`**

```python
if source.type == "investor_signal":
    from scripts.fetchers.investor_signal import InvestorSignalFetcher
    return InvestorSignalFetcher
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_investor_signal.py -v
```

Expected: 1 passed.

- [ ] **Step 7: Commit**

```bash
git add scripts/fetchers/investor_signal.py sources/investor-signal.yaml tests/test_investor_signal.py scripts/ingest.py
git commit -m "feat: investor_signal composite fetcher (YC + a16z + Sequoia + PH + BetaList)"
```

---

## Task 24: `scripts/fetchers/skill_velocity.py` — composite jobs/salary signal

**Files:**
- Create: `scripts/fetchers/skill_velocity.py`
- Create: `sources/skill-velocity.yaml`
- Test: `tests/test_skill_velocity.py`

Strategy: ingest three sub-sources — HN "Who's Hiring" monthly thread text, Layoffs.fyi RSS, and a configurable keyword scraper. The fetcher computes per-keyword frequency for the current run and writes a structured row per keyword. Synthesis Section 4 compares the current row against prior runs via `signals.jsonl` for delta calculation.

- [ ] **Step 1: Write failing tests**

`tests/test_skill_velocity.py`:

```python
from __future__ import annotations

from pathlib import Path

import httpx

from scripts.fetchers.skill_velocity import SkillVelocityFetcher
from scripts.sources import PreFilter, SourceConfig


WHO_IS_HIRING = {
    "data": {
        "children": [
            {"data": {"id": "wh1", "title": "Ask HN: Who is hiring? (May 2026)", "permalink": "/r/hn/comments/wh1", "score": 200}}
        ]
    }
}

WHO_IS_HIRING_COMMENTS = [
    None,
    {
        "data": {
            "children": [
                {"data": {"id": "c1", "body": "Hiring Claude prompt engineer, technical writer, devrel", "score": 10, "permalink": "/c1", "created_utc": 1748284800}},
                {"data": {"id": "c2", "body": "Looking for prompt engineer with claude experience", "score": 6, "permalink": "/c2", "created_utc": 1748284800}},
            ]
        }
    },
]


def _src() -> SourceConfig:
    return SourceConfig(
        id="skill-velocity",
        name="Skill velocity (composite)",
        type="skill_velocity",
        config={
            "keywords": ["claude", "prompt engineer", "technical writer", "devrel"],
            "subfeeds": [
                {
                    "name": "hn-whoshiring",
                    "kind": "hn_whoshiring",
                    "thread_search_url": "https://hn.algolia.com/api/v1/search",
                    "thread_query": "Ask HN: Who is hiring",
                },
            ],
        },
        poll_cadence="weekly",
        signal_type=["skill_velocity"],
        audience_tags=["hardcore_tech", "devs_curious_ai"],
        relevance_tags=["skill", "jobs"],
        pre_filter=PreFilter(min_engagement=0, recency_window_days=60, dedup_key="title_url"),
        priority=1,
        fragility_tier="moderate",
    )


def test_skill_velocity_counts_keyword_mentions(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "hn.algolia.com" in url:
            return httpx.Response(200, json={"hits": [{"objectID": "wh1", "title": "Ask HN: Who is hiring? (May 2026)"}]})
        if "/wh1.json" in url or "/wh1/" in url:
            return httpx.Response(200, json=WHO_IS_HIRING_COMMENTS)
        if "wh1" in url:
            return httpx.Response(200, json=WHO_IS_HIRING)
        return httpx.Response(404)

    f = SkillVelocityFetcher(
        source=_src(),
        errors_path=tmp_path / "e.jsonl",
        watermarks_path=tmp_path / "w.json",
        transport=httpx.MockTransport(handler),
    )
    items = f.fetch_items()
    by_kw = {i["title"]: i for i in items}
    # One synthetic "item" per keyword, carrying the count in metrics.score.
    assert "skill-velocity: claude" in by_kw
    assert by_kw["skill-velocity: claude"]["metrics"]["score"] == 2
    assert by_kw["skill-velocity: prompt engineer"]["metrics"]["score"] == 2
    assert by_kw["skill-velocity: technical writer"]["metrics"]["score"] == 1
    assert by_kw["skill-velocity: devrel"]["metrics"]["score"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_skill_velocity.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/fetchers/skill_velocity.py`**

```python
from __future__ import annotations

import re
from typing import Any

import httpx

from scripts.common import compute_item_id, iso_now, log_fetch_error
from scripts.fetchers.base import BaseFetcher


class SkillVelocityFetcher(BaseFetcher):
    """Composite fetcher that counts keyword mentions across job-flavored corpora.

    Config keys:
      keywords (required): list of strings; case-insensitive substring match
      subfeeds (required): each subfeed contributes raw text. Supported kinds:
        - hn_whoshiring: find the latest "Ask HN: Who is hiring?" thread via
          HN Algolia, then pull its comments and count keyword mentions.
        - rss: pull RSS items and count keyword mentions in titles+descriptions.

    Output: one synthetic item per keyword, with metrics.score = mention count
    over the run. Section 4 (skill velocity) compares the current run's score
    against the same source/keyword in prior signals.jsonl observations for
    delta computation.
    """

    def __init__(self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport

    def fetch_items(self) -> list[dict[str, Any]]:
        cfg = self.source.config
        keywords: list[str] = list(cfg.get("keywords") or [])
        subfeeds: list[dict[str, Any]] = list(cfg.get("subfeeds") or [])
        if not keywords:
            return []

        corpus: list[str] = []
        with httpx.Client(transport=self._transport, timeout=30.0, headers={"User-Agent": "radar/0.1"}) as client:
            for sf in subfeeds:
                name = sf.get("name", "unknown")
                try:
                    corpus.extend(self._collect_text(client, sf))
                except BaseException as exc:  # noqa: BLE001
                    log_fetch_error(
                        self.errors_path,
                        source_id=f"{self.source.id}:{name}",
                        exc=exc,
                    )

        joined = "\n".join(corpus).lower()
        fetched_at = iso_now()
        out: list[dict[str, Any]] = []
        for kw in keywords:
            count = len(re.findall(re.escape(kw.lower()), joined))
            title = f"skill-velocity: {kw}"
            url = f"radar://skill-velocity/{re.sub(r'[^a-z0-9]+', '-', kw.lower()).strip('-')}"
            item_id = compute_item_id(title, url)
            out.append(
                {
                    "item_id": item_id,
                    "title": title,
                    "url": url,
                    "source_id": self.source.id,
                    "signal_type": list(self.source.signal_type),
                    "audience_tags": list(self.source.audience_tags),
                    "timestamp": fetched_at,
                    "raw_text": f"keyword={kw} mentions={count}",
                    "metrics": {"score": count, "comments": 0, "stars": None},
                    "relevance_tags": list(self.source.relevance_tags) + [f"keyword:{kw}"],
                    "fetched_at": fetched_at,
                    "dedup_key": f"skill-velocity::{kw.lower()}::{fetched_at[:10]}",
                }
            )
        return out

    def _collect_text(self, client: httpx.Client, sf: dict[str, Any]) -> list[str]:
        kind = sf.get("kind")
        if kind == "hn_whoshiring":
            search = client.get(sf["thread_search_url"], params={"query": sf["thread_query"], "tags": "story", "hitsPerPage": "1"})
            search.raise_for_status()
            hits = (search.json().get("hits") or [])
            if not hits:
                return []
            object_id = hits[0]["objectID"]
            item = client.get(f"https://hn.algolia.com/api/v1/items/{object_id}")
            item.raise_for_status()
            # HN Algolia /items/<id> returns a tree of children comments.
            return list(_walk_hn_tree(item.json()))
        if kind == "rss":
            import feedparser
            resp = client.get(sf["url"])
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            out: list[str] = []
            for entry in feed.get("entries") or []:
                out.append(entry.get("title") or "")
                out.append(entry.get("summary") or "")
            return out
        raise ValueError(f"unknown subfeed kind: {kind!r}")


def _walk_hn_tree(node: dict[str, Any]):
    text = node.get("text") or ""
    if text:
        yield text
    for child in node.get("children") or []:
        yield from _walk_hn_tree(child)
```

- [ ] **Step 4: Write `sources/skill-velocity.yaml`**

```yaml
id: skill-velocity
name: Skill velocity (composite)
type: skill_velocity
config:
  keywords:
    - claude
    - prompt engineer
    - technical writer
    - developer experience
    - devrel
    - mcp
    - agentic
    - retrieval
  subfeeds:
    - name: hn-whoshiring
      kind: hn_whoshiring
      thread_search_url: https://hn.algolia.com/api/v1/search
      thread_query: "Ask HN: Who is hiring"
    - name: layoffs-fyi
      kind: rss
      url: https://layoffs.fyi/rss
poll_cadence: weekly
signal_type: [skill_velocity]
audience_tags: [hardcore_tech, devs_curious_ai, tech_writer]
relevance_tags: [skill, jobs]
pre_filter: {min_engagement: 0, recency_window_days: 60, dedup_key: title_url}
priority: 1
fragility_tier: moderate
staleness_threshold_days: 21
```

> LinkedIn jobs scraping is intentionally omitted — the spec mentions it but LinkedIn aggressively blocks scrapers. Treat as a known gap; if the operator finds a legal scrape vector later, add it as another subfeed with `fragility_tier: fragile`.

- [ ] **Step 5: Register in `_select_fetcher`**

```python
if source.type == "skill_velocity":
    from scripts.fetchers.skill_velocity import SkillVelocityFetcher
    return SkillVelocityFetcher
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_skill_velocity.py -v
```

Expected: 1 passed.

- [ ] **Step 7: Commit**

```bash
git add scripts/fetchers/skill_velocity.py sources/skill-velocity.yaml tests/test_skill_velocity.py scripts/ingest.py
git commit -m "feat: skill_velocity composite fetcher (HN Who's Hiring + Layoffs.fyi)"
```

---

## Task 25: Expand source registry to full ~80 sources

This is mostly YAML authoring. Each source is one file; no code changes needed. Group additions into commits by source category for reviewability.

**Files:**
- Create: ~70 new `sources/*.yaml` files spanning the categories in spec Section 6.

The spec catalogs them; the work is mechanical translation. Walk through each category in spec Section 6 and create one YAML per source.

- [ ] **Step 1: AI lab blogs (10 RSS sources)**

For each of: openai-blog, deepmind-blog, google-research-blog, meta-ai-blog, microsoft-research-blog, mistral-blog, cohere-blog, huggingface-blog, xai-blog, replicate-blog.

Pattern (`sources/openai-blog.yaml`):

```yaml
id: openai-blog
name: OpenAI Blog
type: rss
config: {url: https://openai.com/blog/rss.xml}
poll_cadence: daily
signal_type: [capability, news, investor]
audience_tags: [hardcore_tech, devs_curious_ai]
relevance_tags: [openai, ai-labs]
pre_filter: {min_engagement: 0, recency_window_days: 14, dedup_key: title_url}
priority: 1
fragility_tier: stable
```

Repeat with each lab's feed URL substituted. URLs change; verify with `curl -sI <url>` before committing.

- [ ] **Step 2: Newsletters (10 RSS sources)**

import-ai, last-week-ai, the-batch, interconnects, stratechery, platformer, bens-bites, tldr-ai, pragmatic-engineer, latent-space. Same pattern as above with `signal_type: [pattern, news]`.

- [ ] **Step 3: Reddit + community (15+ subreddits as `json_api` kind:reddit)**

r-localllama, r-openai, r-devrel, r-programming, r-python, r-javascript, r-rust, r-golang, r-sideproject, r-saas. Use the pattern from Task 18.

- [ ] **Step 4: GitHub watchers (10 repos)**

claude-code, awesome-claude-code, awesome-claude-prompts, awesome-mcp-servers, awesome-claude-skills, langchain, llamaindex, pydantic-ai, crewai, autogen. Use the pattern from Task 18 with `github_watch` and `watch_paths` set per repo.

- [ ] **Step 5: Tech writing community (6 sources)**

write-the-docs-blog, idratherbewriting, content-wrangler-newsletter, cherryleaf, docops-community, api-the-docs.

- [ ] **Step 6: Trend signals (3 sources)**

google-trends (via pytrends — script-shaped, scheduled separately if needed), exploding-topics (scrape), npmtrends (json_api).

- [ ] **Step 7: Conferences and CFPs (5–10 aggregator sources)**

sessionize-cfp, papercall-cfp, write-the-docs-cfp, pycon-us-cfp, neurips-cfp. Use `scrape` type — these are HTML pages.

- [ ] **Step 8: AI dev tool changelogs (10 sources)**

cursor-changelog, windsurf-changelog, zed-ai-changelog, aider-releases (github_watch), continue-dev-releases (github_watch), v0-changelog, bolt-new-changelog, lovable-changelog, vercel-ai-sdk-releases (github_watch), langgraph-releases (github_watch).

- [ ] **Step 9: AI-for-docs tools (6 sources)**

mintlify-changelog (already in v1), readme-io-changelog, document360-changelog, scribehow-changelog, fern-changelog, gitbook-changelog.

- [ ] **Step 10: Regulatory/policy (4 sources)**

eu-ai-act-news, nist-ai-rmf, white-house-ai-eo, india-meity. Most have RSS or scrape-able news pages.

- [ ] **Step 11: Update `sources/_groups.yaml` to cover every new source**

Re-run the grouping audit from Task 21 Step 2 after each batch of additions.

- [ ] **Step 12: After each batch, ingest locally and inspect**

```bash
python -m scripts.ingest --skip-preflight
cat state/fetch-errors.jsonl
```

Triage: any source that fails on first try gets either a `fragility_tier: fragile` upgrade or a config fix. Sources that fail repeatedly get pruned (per Section 8 source ROI metric).

- [ ] **Step 13: Commit per category**

```bash
git add sources/<batch> sources/_groups.yaml
git commit -m "feat: v2 source registry — <category>"
```

**v2 source registry acceptance:**
- `load_all_sources(Path("sources"))` returns ≥75 sources.
- The audit script from Task 21 Step 2 reports no missing-from-group and no extras.
- `python -m scripts.ingest --skip-preflight` completes in under 15 minutes on the operator's machine (Section 4.2 runtime target — for the cron this means parallelizing fetcher runs; see Step 14 below if the single-threaded version exceeds budget).

- [ ] **Step 14: If single-threaded runtime exceeds 15 minutes, parallelize**

Refactor `run_ingest` in `scripts/ingest.py` to use a `concurrent.futures.ThreadPoolExecutor` with `max_workers=8` over the sources list. Each fetcher already returns a `FetchOutcome`; the orchestrator collects them, then runs the prefilter and writes serially (preserves the within-run dedup invariant).

Add a test that proves outputs are identical between threaded and serial modes (run the orchestrator twice on the same fixture and assert raw/ files match).

```bash
git add scripts/ingest.py tests/test_ingest.py
git commit -m "perf: parallelize ingestion across sources (ThreadPoolExecutor)"
```

---

## Task 26: `scripts/maintenance.py` — quarterly memory compaction (R3)

**Files:**
- Create: `scripts/maintenance.py`
- Test: `tests/test_maintenance.py`

Compaction triggers automatically on digest counter (#6, #12, #18, ...) per Q5. Implementation: a `scripts/maintenance.py` callable that the `/radar` slash command invokes when the archive directory contains a multiple-of-6 number of digests.

- [ ] **Step 1: Write failing tests**

`tests/test_maintenance.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.maintenance import (
    archive_old_signals,
    compact_feedback_log,
    digest_count,
    should_compact,
)


def test_digest_count_counts_archive_files(tmp_path: Path):
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "radar-2026-01-01.md").write_text("x")
    (tmp_path / "archive" / "radar-2026-01-15.md").write_text("x")
    assert digest_count(tmp_path / "archive") == 2


def test_should_compact_on_every_sixth_digest(tmp_path: Path):
    arc = tmp_path / "archive"
    arc.mkdir()
    for i in range(6):
        (arc / f"radar-2026-01-{i+1:02d}.md").write_text("x")
    assert should_compact(arc) is True
    (arc / "radar-2026-01-07.md").write_text("x")
    assert should_compact(arc) is False


def test_archive_old_signals_splits_at_180_days(tmp_path: Path):
    signals = tmp_path / "signals.jsonl"
    old_date = (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%Y-%m-%d")
    new_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    signals.write_text(
        "\n".join(
            [
                json.dumps({"date": old_date, "theme": "old-theme", "source_count": 3, "engagement_total": 100}),
                json.dumps({"date": new_date, "theme": "new-theme", "source_count": 5, "engagement_total": 200}),
            ]
        )
        + "\n"
    )
    archive_old_signals(signals, archive_dir=tmp_path / "signal-archive", cutoff_days=180)
    remaining = [json.loads(l) for l in signals.read_text().splitlines() if l.strip()]
    archived = list((tmp_path / "signal-archive").glob("*.jsonl"))
    assert len(remaining) == 1
    assert remaining[0]["theme"] == "new-theme"
    assert len(archived) == 1


def test_compact_feedback_log_drops_pass_lines_older_than_cutoff(tmp_path: Path):
    feedback = tmp_path / "feedback.md"
    old = (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%Y-%m-%d")
    new = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    feedback.write_text(
        "# Feedback Log\n\n"
        f"{old} | item-old1 | Pass | covered\n"
        f"{old} | item-old2 | Doing | still active\n"
        f"{new} | item-new1 | Pass | covered\n"
    )
    compact_feedback_log(feedback, cutoff_days=180)
    text = feedback.read_text()
    assert "item-old1" not in text  # Pass + old → dropped
    assert "item-old2" in text       # Doing → kept regardless of age
    assert "item-new1" in text       # Pass + recent → kept
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_maintenance.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/maintenance.py`**

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.common import iso_now


COMPACT_EVERY_N_DIGESTS = 6
SIGNALS_CUTOFF_DAYS = 180
FEEDBACK_CUTOFF_DAYS = 180


def digest_count(archive_dir: Path) -> int:
    """Number of digest files in state/archive/."""
    if not archive_dir.exists():
        return 0
    return len(list(archive_dir.glob("radar-*.md")))


def should_compact(archive_dir: Path) -> bool:
    """True iff the digest count is a non-zero multiple of COMPACT_EVERY_N_DIGESTS."""
    n = digest_count(archive_dir)
    return n > 0 and n % COMPACT_EVERY_N_DIGESTS == 0


def archive_old_signals(
    signals_path: Path,
    *,
    archive_dir: Path,
    cutoff_days: int = SIGNALS_CUTOFF_DAYS,
) -> None:
    """Split signals.jsonl: records older than cutoff_days go to a dated archive
    file in archive_dir; recent records stay in signals.jsonl."""
    if not signals_path.exists():
        return
    cutoff = datetime.now(timezone.utc).date()
    cutoff_str = (cutoff.fromordinal(cutoff.toordinal() - cutoff_days)).strftime("%Y-%m-%d")
    old: list[str] = []
    new: list[str] = []
    for line in signals_path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        date_str = rec.get("date")
        if date_str and date_str < cutoff_str:
            old.append(line)
        else:
            new.append(line)
    if not old:
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = iso_now().replace(":", "").replace("-", "")[:15]
    (archive_dir / f"signals-archived-{stamp}.jsonl").write_text("\n".join(old) + "\n")
    signals_path.write_text("\n".join(new) + ("\n" if new else ""))


def compact_feedback_log(feedback_path: Path, *, cutoff_days: int = FEEDBACK_CUTOFF_DAYS) -> None:
    """Drop `Pass` lines older than cutoff_days. Keep `Doing`, `Done`, `Watch`
    regardless of age — those carry forward operator context."""
    if not feedback_path.exists():
        return
    lines = feedback_path.read_text().splitlines()
    today = datetime.now(timezone.utc).date()
    cutoff = today.fromordinal(today.toordinal() - cutoff_days)
    kept: list[str] = []
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[2] == "Pass":
            try:
                d = datetime.strptime(parts[0], "%Y-%m-%d").date()
                if d < cutoff:
                    continue
            except ValueError:
                pass
        kept.append(line)
    feedback_path.write_text("\n".join(kept) + ("\n" if kept and not kept[-1] == "" else ""))
```

- [ ] **Step 4: Wire maintenance into `/radar`**

Append to `.claude/commands/radar.md` Step 4 (Stitch phase), after writing the archive file:

```markdown
## Step 4b — Quarterly compaction check (Q5)

After writing the archive file, run:

```bash
python -c "from pathlib import Path; from scripts.maintenance import should_compact, archive_old_signals, compact_feedback_log; arc = Path('state/archive'); \
  print('compact?', should_compact(arc)); \
  ( (archive_old_signals(Path('state/signals.jsonl'), archive_dir=Path('state/signal-archive')) or compact_feedback_log(Path('state/feedback.md'))) if should_compact(arc) else None)"
```

If compaction ran, also add a short "Memory compaction performed today" note to the digest's Memory Thread section. If profile drift review is warranted (digest #12, #24, ...), include a Memory Thread line asking the operator to review `state/profile.md` this week.
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_maintenance.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/maintenance.py tests/test_maintenance.py .claude/commands/radar.md
git commit -m "feat: quarterly memory compaction (digest #6, #12, ...)"
```

---

## Task 27: Per-section regeneration fallback (`/radar-section`)

**Files:**
- Create: `.claude/commands/radar-section.md`

Per Section 4.4.1: "Fallback if MRR strains limits in v2 (full 80 sources): per-section slash commands so the operator can regenerate weak sections without redoing the whole digest."

- [ ] **Step 1: Write the slash command**

`.claude/commands/radar-section.md`:

````markdown
---
description: Regenerate a single section of the most recent digest. Argument is the section name.
argument-hint: <section-key>
---

# /radar-section $ARGUMENTS

Regenerate one section of the most recent digest in place.

Valid section keys:
- `memory` (Section 0)
- `trends` (1)
- `asking` (2)
- `bleeding-edge` (3)
- `skill-velocity` (4)
- `course-prep` (5)
- `investor` (6)
- `cfps` (7)
- `capability` (8)
- `pain-points` (9)
- `watch` (10)

## Pre-flight

1. `git pull --rebase`. Abort on failure.
2. Find the latest `state/archive/radar-*.md`. If none exists, ask the operator to run `/radar` first.
3. Find the run date the latest archive belongs to (the date in the filename). All Map-phase intermediates for that date must exist in `intermediate/`. If they don't (because `intermediate/` is gitignored and a different machine produced the digest), re-run the Map phase for the relevant groups only.

## Routing

Use the same routing table as `/radar` Step 3, but for only the requested section. Read only the intermediate slices and state files that section needs.

## Write

Edit the latest archive file in place: replace the existing section (located by `## <N>` heading) with the regenerated content. Leave every other section untouched.

Append a footnote at the bottom of the archive file:

```
*Section <key> regenerated on <YYYY-MM-DD>.*
```

## Append signal rollups

If the regenerated section is `trends` or `watch`, also append fresh theme rollups to `state/signals.jsonl` via `python -m scripts.persist_signal '<json>'`, replacing prior rollups for the same `(date, theme)` pair only if those were appended in the same digest. (Older rollups are immutable history.)
````

- [ ] **Step 2: Manual smoke check**

In Claude Code session: `/radar-section trends`. Verify:
- The Top-5-trends section in the latest archive is rewritten.
- The footnote is appended.
- No other section is touched.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/radar-section.md
git commit -m "feat: /radar-section per-section regeneration fallback"
```

---

## Task 28: Synthesis prompt tuning playbook (digests 4–6)

**Files:**
- Modify: `.claude/commands/radar.md` iteratively across digests 4–6.

R2 in spec: course suggestions will be weak in digests 1–3. Expect prompt tuning across digests 4–6.

This is a procedural task that runs over time, not a single coding session.

- [ ] **Step 1: After digest 3, audit weak sections**

Open digests 1, 2, 3 side by side. For each section, score on a 1–5 scale:

- Relevance: are surfaced items in operator's beat?
- Actionability: does the operator know what to do with this?
- Voice match: does the digest sound like the operator's beat?
- Memory accuracy: were any topics repeated from catalog or trajectory? (Should be zero.)

Write the audit to `docs/plans/2026-XX-XX-digest-audit.md` (operator and Claude collaboratively).

- [ ] **Step 2: Identify the lowest-scoring section**

Most likely candidate: Section 5 (Course prep). The spec's prediction (R2) is that course detection is the weakest synthesis step early on.

- [ ] **Step 3: Edit `.claude/commands/radar.md` Section 5 rubric**

Add more concrete language in the slash command — for example:

- Specify what "multi-signal" means: "≥3 distinct signal types ON THE SAME TOPIC, not just 3 active signals overall."
- Add a worked example of what counts and what doesn't.
- Require the digest to explicitly list which signals aligned, so the operator can audit the reasoning.

- [ ] **Step 4: Iterate**

Run digest 4 with the new prompt, compare. Re-audit. Tune.

By digest 6, the rubric should produce ≥1 plausible course suggestion per quarter (the Section 8 metric). If not, the rubric is still too generic — keep tuning.

- [ ] **Step 5: Commit each tuning change with a descriptive message**

```bash
git add .claude/commands/radar.md
git commit -m "tune: course-prep rubric — require explicit signal alignment listing (digest 4 audit)"
```

**v2 acceptance criteria:**
- ≥75 sources in the registry.
- Cron run completes in under 15 minutes (parallelized if needed).
- `state/signals.jsonl` is automatically compacted on digests #6, #12, ... — verify by inspecting `state/signal-archive/`.
- `/radar-section` regenerates a single section without disturbing the rest.
- All `pytest -q` tests pass.
- One digest in the post-tuning window (digest 4–6) surfaces at least one course suggestion the operator considers worth building (Section 8 metric).

---

# Plan Self-Review

Run through this checklist with fresh eyes before handing off.

**Spec coverage:**

| Spec section / requirement | Implementing task(s) |
|---|---|
| §3 Architecture: five components | T1 (bootstrap), T2 (state), T8/T10 (ingestion), T11 (synthesis), T20 (delivery via Actions) |
| §4.1 Source Registry schema | T5 (SourceConfig pydantic model + load_source) |
| §4.2 Ingestion fetcher types: rss | T14 |
| §4.2 Ingestion fetcher types: json_api | T9 (HN), T17 (Reddit) |
| §4.2 Ingestion fetcher types: github_watch | T15 |
| §4.2 Ingestion fetcher types: scrape | T16 |
| §4.2 Ingestion fetcher types: search_query | (folded into json_api / scrape; not a distinct fetcher) — note for v2: revisit if a true cross-source-search type emerges |
| §4.2 Ingestion fetcher types: investor_signal | T23 |
| §4.2 Ingestion pain_point fetcher | T19 |
| §4.2 Ingestion skill_velocity composite | T24 |
| §4.2 Raw output schema | T9 (set in HNAlgoliaFetcher), enforced by every fetcher's normalization |
| §4.2 Pre-filter pipeline | T7 |
| §4.2 Runtime target ≤15 min | T25 Step 14 (parallelization if needed) |
| §4.2 R11 per-fetcher isolation | T8 (BaseFetcher try/except) |
| §4.2 R11 fragility tiers + watermarks | T6 (watermarks.py), T18 (`fragility_tier` in YAML), T11 (Memory Thread flags stale) |
| §4.2 R12 pre-flight git rebase | T4 (git_preflight.py), T10 (wired into ingest), T11 (wired into /radar Step 0), T20 (workflow rebase-then-push) |
| §4.2 Append-only state log | signals.jsonl design (file structure section) + T3 (append_jsonl) |
| §4.2 Graceful synthesis degradation | T11 ("If a section's input slices are all empty, omit silently") |
| §4.3 State store: profile.md, catalog.md, trajectory.md, feedback.md, signals.jsonl, fetch-errors.jsonl, archive/ | T2 |
| §4.3 watermarks.json (R11 support file) | T2, T6 |
| §4.4 Synthesis inputs in order | T11 Step 1 |
| §4.4 Synthesis outputs (archive + signals append + optional trajectory edit) | T11 Step 4, 5, and operator-feedback path |
| §4.4 Synthesis rubric: memory check, trend ≥3 sources + delta, catalog filter, course multi-signal ≥3 types, trajectory boost, pass exclusion, counter ≥2, length cap | T11 (all encoded in slash command) |
| §4.4.1 MRR Map-Route-Reduce | T11 (Steps 2, 3, 4) + T9/T21/T25 (group config) |
| §4.4.1 Fallback per-section regeneration | T27 |
| §4.5 Terminal output + git commit | T11 Step 6 (terminal report) + T20 (cron commit) |
| §4.5 Feedback paths (in-session + between sessions) | T11 (in-session edit path) + T13 (operator-edited template) |
| §5 Digest structure (Memory + 10 sections) | T11 Step 4 (template) + T11 Step 3 (routing table) |
| §6 Source catalog (~80 sources) | T9 (1), T18 (10), T25 (~70 more) |
| §7 v0 / v1 / v2 phasing | T1-T13 (v0), T14-T22 (v1), T23-T28 (v2) |
| §8 Quality metrics | Surfaced in v2 acceptance + Task 25 Step 13 (source ROI pruning) |
| §9 R1 pain-point harvesting | T19 (focused harvester) + T11 (subagent does question-form filter in Map phase) |
| §9 R2 multi-signal course | T11 rubric (3+ signal types required) + T28 (tuning playbook) |
| §9 R3 memory rot | T26 (quarterly compaction) |
| §9 R4 investor data fragmentation | T23 (free sources only, intra-composite fail-soft) |
| §9 R5 overwhelm | T11 (length cap, item cap, silent collapse) |
| §9 R6 generic AI hype | T11 (trend requires ≥3 sources + non-zero delta) |
| §9 R7 profile/catalog seeding | T13 (operator content step) |
| §9 R8 Lost in the Middle | T11 MRR three-phase design |
| §9 R9 bi-weekly cadence | Out of scope for this plan (v3, per spec) |
| §9 R10 Horizon abandonment | N/A — we don't depend on Horizon at runtime (reference-only clone) |
| §9 R11 scraping fragility | T8 (isolation), T6 (watermarks), T18/T21 (fragility tiers), T11 (Memory Thread flagging), T25 (ROI pruning) |
| §9 R12 state concurrency | T4 (preflight), T20 (workflow rebase-then-push), T10 (operator-file write-guard test), T11 (rules in slash command) |
| §10 Q1 private GitHub repo | Out of scope for this plan (repo creation is operator action; the code is repo-agnostic) |
| §10 Q2 email delivery off in v0 | T11 (no email path), T1 (no SMTP deps in pyproject) |
| §10 Q3 profile from posts | T13 Step 1 (drafting instruction) |
| §10 Q4 unified digest with audience tags | T11 (digest template carries audience_tags per item where relevant) |
| §10 Q5 automatic compaction | T26 (digest-counter trigger) |

**Placeholder scan:** All code blocks contain executable code, every step has concrete commands and expected outputs, no "TBD" / "TODO" / "fill in later" markers remain. Task 25 Step 1-10 itemize the YAML additions but each step gives a concrete pattern and one full example; this is the appropriate level of detail for mechanical YAML authoring across ~70 nearly identical files.

**Type / symbol consistency:**
- `compute_item_id`, `iso_now`, `today_utc_date`, `append_jsonl`, `log_fetch_error` — defined in T3, referenced by T4–T28.
- `SourceConfig`, `PreFilter`, `FragilityTier`, `load_source`, `load_all_sources` — defined in T5, referenced by T8–T28.
- `stamp_success`, `load_watermarks`, `save_watermarks`, `days_since` — defined in T6, referenced by T8, T11.
- `apply_prefilter`, `load_recent_dedup_keys` — defined in T7, referenced by T10.
- `BaseFetcher`, `FetchOutcome` — defined in T8, subclassed by T9, T14, T15, T16, T17, T19, T23, T24.
- `IngestPaths`, `run_ingest`, `_select_fetcher` — defined in T10, extended by T14, T15, T16, T17, T19, T23, T24.
- `HNAlgoliaFetcher`, `RedditJSONFetcher` — defined in T9, T17, both inside `scripts/fetchers/json_api.py`.
- `RSSFetcher`, `GitHubWatchFetcher`, `ScrapeFetcher`, `RedditCommentHarvester`, `InvestorSignalFetcher`, `SkillVelocityFetcher` — defined in T14, T15, T16, T19, T23, T24.
- `digest_count`, `should_compact`, `archive_old_signals`, `compact_feedback_log` — defined in T26, invoked from T11 Step 4b.
- `persist_signal` CLI — defined in T11, invoked from T11 Step 5 and T27.

No naming drift detected.

**Spec gaps consciously deferred:**
- §6 mentions YouTube channels and podcasts. Transcript ingestion is genuinely hard; deferred to v3 (a YouTube-RSS subscription feed is a passable v2 substitute for the channel-tracking case but is not wired in this plan). Add a `youtube-channel-uploads.yaml` pattern in v2 if the operator finds it valuable.
- §6 mentions Bluesky / Mastodon. Spec §7 v3 puts these on the deferred list; not in this plan.
- §6 mentions LinkedIn Jobs scraping. Deliberately omitted from T24 — anti-bot blockers make this fragile-of-fragile. Marked as known gap in T24 commentary.
- §5 Section 4 "Skill velocity" requires absolute job counts. T24 reports keyword *mention* counts (a proxy). The synthesis in T11 must phrase it accordingly ("mentions in tracked corpora") rather than claiming "jobs."

These deferrals are deliberate; the plan does not silently skip them.

---

# Execution Handoff

Plan complete and saved to [docs/plans/2026-05-27-radar-implementation.md](docs/plans/2026-05-27-radar-implementation.md). Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Best fit here because v0 has clean task boundaries with explicit TDD and the plan is dense enough that a fresh context per task helps.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Faster turnaround on simple tasks but risks context bloat by the time you reach v1.

Which approach?



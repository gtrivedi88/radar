# CLAUDE.md — Radar Personal Intelligence System

## What This Is

**Radar** is Gaurav Trivedi's personal intelligence system. Python fetches 300+ items from 30 sources in 2 seconds. Claude reads everything, triages into ACT NOW / WATCH / BANK, and accumulates signals across cycles so emerging trends surface automatically.

**Architecture: Python fetches. Claude thinks. The registry resolves identity. The signal bank remembers.**

> Claude *judges* which theme an item belongs to (matching by meaning against the registry), then a small tested Python layer (`radar_memory/`) does every deterministic write — resolving theme identity, updating the registry, appending to the signal bank, logging ACT NOW predictions, and writing the audit trail. Claude proposes; Python commits.

## How It Works

```
python -m radar-engine run          # Fetch 300+ items from 30 sources (2 sec)
/radar                              # Claude reads all, triages, accumulates signals
```

### The Intelligence Loop

```
30 sources → raw/YYYY-MM-DD/*.json → Claude reads ALL items
                                          ↓
                                    Triage every theme:
                                    ┌─────────────────────────────┐
                                    │ ACT NOW (3+ sources, action │──→ Digest (top 3)
                                    │          ready, timely)     │
                                    ├─────────────────────────────┤
                                    │ WATCH   (2 sources, or      │──→ Digest (watch list)
                                    │          accumulating)      │    + signal-bank.jsonl
                                    ├─────────────────────────────┤
                                    │ BANK    (everything else)   │──→ signal-bank.jsonl only
                                    └─────────────────────────────┘
                                          ↓
                                    Next cycle: Claude reads signal bank
                                    Banked themes that reappear → promoted
                                    3 cycles banked → evaluated for ACT NOW
```

**Key insight:** Nothing is forgotten. A theme banked in cycle 1, seen again in cycle 3, and confirmed in cycle 5 automatically surfaces as an emerging trend. Claude accumulates, Python doesn't.

## State Files

| File | Purpose | Who writes |
|------|---------|------------|
| `state/theme-registry.jsonl` | **Canonical theme identity** — `theme_id`, canonical name, aliases, cycle_count. The system of record. | Python (`radar_memory`) |
| `state/signal-bank.jsonl` | Every theme observed, keyed by `theme_id`, with cycle count and status | Python (`radar_memory`) |
| `state/act-now-predictions.jsonl` | One row per ACT NOW call, graded later by the eval scorecard | Python (`radar_memory`) |
| `state/theme-resolution-log.jsonl` | Audit trail: every match/mint decision the resolver made | Python (`radar_memory`) |
| `state/theme-resolutions.jsonl` | **Transient** proposals Claude writes each cycle; consumed and cleared by `resolve` (gitignored) | Claude → consumed by Python |
| `state/signals.jsonl` | Only surfaced themes (ACT NOW + TRENDS) | Claude (/radar) |
| `state/profile.md` | Beat, audiences, voice | Operator |
| `state/catalog.md` | Published work (never re-suggest) | Operator |
| `state/trajectory.md` | Active/queued/passed/done | Operator + Claude |
| `state/feedback.md` | Digest feedback (Doing/Pass) | Operator |
| `state/archive/` | Past digests | Claude (/radar) |

### Signal Bank Schema

```jsonl
{"date": "YYYY-MM-DD", "theme_id": "stable_id", "theme": "snake_case_name", "source_count": N, "sources": ["id1", "id2"], "engagement_total": N, "status": "banked|watching|surfaced", "cycle_count": N, "first_seen": "YYYY-MM-DD", "evidence": "one sentence"}
```

- `theme_id`: the **stable join key** across cycles, assigned by the registry. Accumulation is keyed on this, NOT on the human-readable `theme` string. Claude no longer has to reproduce exact theme strings from memory — it matches by *meaning* against `theme-registry.jsonl` and Python resolves the id.
- `theme`: the human-readable label for this observation (free to vary cycle to cycle).
- `cycle_count`: increments each time the theme reappears (tracked in the registry).
- `status`: "banked" (stored only), "watching" (in watch list), "surfaced" (in ACT NOW or TRENDS)
- Promotion: cycle_count >= 3 and never surfaced → evaluate for ACT NOW

### Memory Layer (`radar_memory/`)

A small, fully-tested, stdlib-only Python package that owns theme identity and every deterministic write. Claude proposes; Python commits. CLI:

```bash
python -m radar_memory resolve      # consume Claude's proposals → registry + bank + predictions + audit log
python -m radar_memory eval         # ACT NOW scorecard (outcome-first: shipped/acted, not just trend persistence)
python -m radar_memory lineage      # engagement chain per theme: 664 (2026-06-11) → 1333 (2026-06-18)
python -m radar_memory contrarian   # "expected but quiet": strong-prior themes with ZERO items this cycle
```

- **Resolver seam** (`resolver.py`): Claude proposes a `theme_id` or `NEW`; Python validates with a deterministic exact/alias backstop that overrides a wrong "NEW", then mints a fresh id if genuinely new. Identity is never left to fuzzy string reuse.
- **Outcome-first eval** (`evalgrade.py`): a prediction counts as a win only when it ships (in `catalog.md`) or is acted on (in `feedback.md`). Trend persistence alone is a separate, weaker `sustained` label — momentum ≠ correctness.
- **Grounded contrarian** (`contrarian.py`): the "dogs that didn't bark" are computed deterministically from the registry, never speculated.
- **Migration**: `python -m radar_memory.migrate` bootstraps the registry and rekeys the bank to `theme_id` (already run once on 2026-06-26).

Run `make test` (38 tests) after touching this package.

### Signals Log Schema (surfaced themes only)

```jsonl
{"date": "YYYY-MM-DD", "theme": "snake_case_name", "source_count": N, "engagement_total": N, "signal_type": "TYPE", "cross_source": BOOL}
```

## Source System

30 sources across 7 categories. Drop a YAML file in `sources/` to add more.

| Category | Sources | Signal type |
|----------|---------|-------------|
| **AI Practitioner Elite** | Simon Willison, Ethan Mollick, Jack Clark, Last Week in AI | What the best minds are thinking |
| **Technical Writing** | Tom Johnson, Dev.to writing, Dev.to tutorial | tech_writer audience |
| **Engineering Leadership** | Pragmatic Engineer, Platformer, Lenny's Newsletter | Hiring, policy, product |
| **Developer Community** | HN (front page, beat, show, hiring), Dev.to (6 tags), Lobsters AI | Community signal, pain points |
| **Industry/Funding** | TechCrunch, Crunchbase, Product Hunt | Money flows, launches |
| **Tech Press** | Verge AI, Ars Technica, MIT Tech Review, InfoWorld, Wired | Mainstream coverage |
| **Developer Tooling** | GitHub Blog, Changelog, Julia Evans | Platform shifts, craft |

## Repository Layout

```
radar/
├── radar-engine/              # Python — dumb fetcher
│   ├── main.py                # CLI: python -m radar-engine run
│   ├── core/base.py           # IntelligenceItem dataclass
│   └── fetchers/enhanced.py   # Fetch, dedup, save JSON (per-source max_items)
├── radar_memory/              # Python — theme identity + deterministic writes
│   ├── registry.py            # Canonical id store (atomic writes)
│   ├── resolver.py            # Match-by-meaning seam + deterministic backstop
│   ├── lineage.py             # Engagement chain per theme
│   ├── contrarian.py          # Grounded "expected but quiet"
│   ├── evalgrade.py           # Outcome-first ACT NOW scorecard
│   ├── migrate.py             # One-time bank → theme_id migration
│   └── __main__.py            # CLI: resolve / eval / contrarian / lineage
├── sources/                   # 30 YAML configs (drop file = add source)
├── state/                     # Memory
│   ├── theme-registry.jsonl   # Canonical theme identity (system of record)
│   ├── signal-bank.jsonl      # ALL themes across cycles, keyed by theme_id
│   ├── act-now-predictions.jsonl  # ACT NOW calls, graded by eval
│   ├── theme-resolution-log.jsonl # Resolver audit trail
│   ├── signals.jsonl          # Surfaced themes only
│   ├── profile.md / catalog.md / trajectory.md / feedback.md
│   └── archive/               # Past digests
├── raw/                       # Fetched JSON (gitignored)
├── tests/                     # 38 tests (run with make test)
├── .claude/
│   ├── commands/radar.md      # /radar — the intelligence engine
│   └── skills/                # Calibration skills
├── Makefile
└── requirements.txt
```

## Beat Territory

Three audiences:
- **tech_writer** — Technical writers adapting to AI
- **devs_curious_ai** — Developers exploring AI tooling
- **hardcore_tech** — Deep technical practitioners

Beat: AI tooling for technical writers, Claude Code workflows, developer experience, technical writing career evolution, AI integration patterns for non-coders.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock pytest
make test                            # 38 tests
python -m radar-engine run           # Fetch from 30 sources
/radar                               # Claude synthesizes
```

### Operational Notes

- **Weekly cron is currently PAUSED.** `.claude/scheduled_tasks.json` has no tasks — the weekly "contrarian signal hunt" (`23 9 * * 1`) was removed before the 2026-06-26 memory-layer migration to stop a background agent from racing the live state. **TODO: re-enable when ready** (it was `prompt`-driven; restore the task entry or recreate via the schedule tooling). Until then `/radar` is run manually.
- **Git remote is HTTPS** (`https://github.com/gtrivedi88/radar.git`), pushed as `gtrivedi88` via the `gh` credential helper. The machine's SSH key authenticates as `gautriv`, which is *denied* push access — do not switch `origin` back to SSH.

## Why This Architecture

Python, two layers, both deterministic — no judgment:
- `radar-engine/`: HTTP requests, JSON, file I/O, dedup. The dumb fetcher.
- `radar_memory/`: theme identity resolution, registry/bank/prediction/audit writes. Deterministic bookkeeping that Claude must not be trusted to do by hand (string drift, double-counting). Fully unit-tested.

Claude (/radar command): reads 300+ items, judges relevance, detects cross-source themes, extracts pain points, identifies course opportunities, tracks trend direction, proposes theme identity by meaning, triages into ACT NOW / WATCH / BANK. Claude proposes; Python commits.

The signal bank is what makes this unbeatable: no personal intelligence system on the internet accumulates weak signals across cycles and promotes them when they reach critical mass. Most systems show you today's top items and forget the rest. Radar remembers everything.

# CLAUDE.md — Radar Personal Intelligence System

## What This Is

**Radar** is Gaurav Trivedi's personal intelligence system. Python fetches 300+ items from 30 sources in 2 seconds. Claude reads everything, triages into ACT NOW / WATCH / BANK, and accumulates signals across cycles so emerging trends surface automatically.

**Architecture: Python fetches. Claude thinks. The signal bank remembers.**

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
| `state/signal-bank.jsonl` | Every theme observed, with cycle count and status | Claude (/radar) |
| `state/signals.jsonl` | Only surfaced themes (ACT NOW + TRENDS) | Claude (/radar) |
| `state/profile.md` | Beat, audiences, voice | Operator |
| `state/catalog.md` | Published work (never re-suggest) | Operator |
| `state/trajectory.md` | Active/queued/passed/done | Operator + Claude |
| `state/feedback.md` | Digest feedback (Doing/Pass) | Operator |
| `state/archive/` | Past digests | Claude (/radar) |

### Signal Bank Schema

```jsonl
{"date": "YYYY-MM-DD", "theme": "snake_case_name", "source_count": N, "sources": ["id1", "id2"], "engagement_total": N, "status": "banked|watching|surfaced", "cycle_count": N, "first_seen": "YYYY-MM-DD", "evidence": "one sentence"}
```

- `theme`: reuse exact names across cycles for accumulation
- `cycle_count`: increments each time the theme reappears
- `status`: "banked" (stored only), "watching" (in watch list), "surfaced" (in ACT NOW or TRENDS)
- Promotion: cycle_count >= 3 and never surfaced → evaluate for ACT NOW

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
├── radar-engine/              # Python — dumb fetcher (348 lines total)
│   ├── main.py                # CLI: python -m radar-engine run
│   ├── core/base.py           # IntelligenceItem dataclass
│   └── fetchers/enhanced.py   # Fetch, dedup, save JSON
├── sources/                   # 30 YAML configs (drop file = add source)
├── state/                     # Memory
│   ├── signal-bank.jsonl      # ALL themes across cycles (accumulator)
│   ├── signals.jsonl          # Surfaced themes only
│   ├── profile.md / catalog.md / trajectory.md / feedback.md
│   └── archive/               # Past digests
├── raw/                       # Fetched JSON (gitignored)
├── tests/                     # 18 tests
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
pip install -r requirements.lock     # Install deps
make test                            # 18 tests
python -m radar-engine run           # Fetch from 30 sources
/radar                               # Claude synthesizes
```

## Why This Architecture

Python (348 lines): HTTP requests, JSON, file I/O, dedup. Nothing smart.

Claude (/radar command): reads 300+ items, judges relevance, detects cross-source themes, extracts pain points, identifies course opportunities, tracks trend direction, accumulates signals across cycles, triages into ACT NOW / WATCH / BANK.

The signal bank is what makes this unbeatable: no personal intelligence system on the internet accumulates weak signals across cycles and promotes them when they reach critical mass. Most systems show you today's top items and forget the rest. Radar remembers everything.

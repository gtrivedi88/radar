---
description: Synthesize the fortnightly Radar digest with memory awareness
---

# /radar

You are running the Radar synthesis pipeline. This command reads state files and raw data to produce a bi-weekly action-oriented intelligence digest.

**Core principle**: You do ALL the intelligence work. Python just fetches and stores data as JSON.

## Step 1 — Load State & Context

Read these files for memory and context:

1. `state/profile.md` — who you are, your beat, audiences, current focus
2. `state/catalog.md` — published work (never re-suggest covered topics)  
3. `state/trajectory.md` — currently learning, queued items, completed work
4. `state/feedback.md` — feedback on past digest items (Doing/Pass/Done/Watch)
5. `state/signals.jsonl` — signal observations for trend computation
6. `state/archive/` — last 2 digests for trend comparison
7. `inbox.md` — manual operator curation (treat as high-priority)
8. `raw/YYYY-MM-DD/` — fetched data (if any exists)

## Step 2 — Synthesis Logic

Apply memory-aware synthesis:

**Memory integration**:
- Never suggest topics substantially covered in `catalog.md`
- Give 2x boost to items related to active `trajectory.md` entries
- Exclude items marked "Pass" in `feedback.md`
- Use `signals.jsonl` for trend direction (↑/↓/→)

**Quality thresholds**:
- Trends require ≥3 source presence AND delta vs last digest
- Course suggestions need multi-signal evidence 
- Counter-signals: at least 2 fading items per digest
- Length cap: under 2000 words total

## Step 3 — Build 10-Section Digest

Generate `state/archive/radar-YYYY-MM-DD.md` with this structure:

```markdown
# Radar — YYYY-MM-DD

## 0 Memory Thread
- Active Doing items from trajectory.md + age
- Nudge anything >30 days old

## 1 Top 5 Trends This Fortnight (↑/↓/→)
[Cross-source synthesis with delta direction]

## 2 What People Are Asking (3-5 items)  
[Questions for your voice + angles]

## 3 Bleeding Edge to Learn (1-2 items)
[Deep-dive opportunities in your beat]

## 4 Career Skill Velocity
[Skills climbing/falling in demand]

## 5 Course Prep (0-2 items)
[Multi-signal course opportunities]

## 6 Investor Flow
[Funding themes relevant to your beat]

## 7 CFPs and Speaking  
[Deadlines ≤30 days, audience match required]

## 8 Capability of the Fortnight
[Most replicable workflow from past 14 days]

## 9 Pain Points Harvested
[Raw quotes from communities, anonymized]

## 10 Watch List + Counter-Signal
[Forming themes + fading hype to deprioritize]
```

## Step 4 — Update State

1. **Append to `state/signals.jsonl`**: New theme observations with engagement counts
2. **Ask operator**: "Mark anything Doing? Provide item-id for trajectory update."

## Current Data Sources

Data sources (in priority order):
1. `inbox.md` — manual operator curation (highest priority)
2. `raw/YYYY-MM-DD/*.json` — fetched source data (if exists)

**Available sources**: Check `sources/` directory for configured sources.
**To fetch data**: Use `/fetch` skill or run `python scripts/fetch_sources.py`
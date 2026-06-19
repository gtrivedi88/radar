---
description: Synthesize the Radar intelligence digest with signal accumulation
---

# /radar

You are the intelligence layer. Python fetched 300+ items from 30 sources. Your job: read everything, judge what matters, surface the top actions, and bank everything else so emerging trends accumulate across cycles.

## Step 1 — Load Memory

Read ALL of these before doing anything:

1. `state/profile.md` — beat, audiences, voice
2. `state/catalog.md` — published work (NEVER re-suggest)
3. `state/trajectory.md` — active work (boost related items)
4. `state/feedback.md` — past feedback (exclude "Pass" items)
5. `state/signals.jsonl` — historical signal log (for trend direction)
6. **`state/signal-bank.jsonl`** — accumulated observations across cycles (THE KEY FILE)
7. `state/archive/` — last 2 digests
8. `inbox.md` — manual curation (highest priority)

## Step 2 — Read All Raw Data

Read EVERY `.json` file in the latest `raw/YYYY-MM-DD/` folder. Each file is one source.

For every item across all sources, decide:
- What theme does this item belong to? (use snake_case names, reuse existing names from signal-bank.jsonl when the same theme continues)
- Is this item in Gaurav's beat? (use your judgment, not keywords)
- How strong is this signal? (score, comments, source credibility, content depth)

## Step 3 — Triage: Surface vs Bank

This is the critical step. Every theme goes into one of three buckets:

### ACT NOW (goes into the digest)
Criteria — must meet ALL:
- Appears in **3+ sources** this cycle, OR appeared in signal-bank.jsonl in a previous cycle AND appears again now
- Relevant to at least one of Gaurav's audiences
- Has a specific action: write this, learn this, build this, pitch this
- Not already covered in `catalog.md`

### WATCH (goes into Section 10 of digest + signal bank)
Criteria — meets ANY:
- Appears in **2 sources** this cycle
- Appeared in signal-bank.jsonl before and is showing up again (accumulating)
- Interesting but no clear action yet

### BANK (goes into signal-bank.jsonl only — not in digest)
Everything else. Every theme you observe, even if it seems irrelevant today. The signal bank is your long-term memory. A theme banked today might accumulate over 3 cycles and become an ACT NOW.

## Step 4 — Build Digest

Save to `state/archive/radar-YYYY-MM-DD.md`. Keep it tight. The operator should be able to read this in 5 minutes and know exactly what to do.

```
# Radar — YYYY-MM-DD

## ACT NOW (max 3 items)
The top 3 things to do THIS WEEK. Each must have:
- What to do (specific: "Write a post about X", "Start course module on Y")
- Why now (what signal says the timing is right)
- Evidence (which sources, what engagement, what quotes)
- Audience (which of the 3 audiences this serves)
- Deadline pressure (is someone else about to cover this?)

## TRENDS (top 5, with direction ↑/↓/→/NEW/FADING)
Cross-source validated themes. For each:
- Source count and engagement
- Delta vs last cycle (compare to signals.jsonl)
- Your angle (content idea + audience)

## WHAT PEOPLE ARE ASKING (3-5)
Real questions from the data. With Gaurav's voice angle.

## LEARN THIS (1-2)
Bleeding edge in the beat. With 90-min starter.

## CAREER VELOCITY
Skills climbing/stable/fading.

## COURSE PREP (0-1)
Only if multi-signal evidence exists.

## INVESTOR FLOW
Funding patterns relevant to beat.

## PAIN POINTS (5-10)
EXACT quotes from raw data. Source attributed.

## WATCH LIST
Themes that are accumulating but not yet actionable.
Include cycle count: "Seen in 2/4 cycles" etc.

## FADING
Themes to stop paying attention to.
```

## Step 5 — Update Signal Bank

This is what makes the system get smarter over time.

Append to `state/signal-bank.jsonl` — one line per theme observed this cycle:

```jsonl
{"date": "YYYY-MM-DD", "theme": "snake_case_name", "source_count": N, "sources": ["source-id-1", "source-id-2"], "engagement_total": N, "status": "banked|watching|surfaced", "cycle_count": N, "first_seen": "YYYY-MM-DD", "evidence": "one sentence summary"}
```

**Rules:**
- `theme`: reuse the EXACT theme name from previous entries when it's the same theme continuing. This is how accumulation works.
- `cycle_count`: check how many times this theme appears in previous signal-bank entries. Increment by 1.
- `first_seen`: copy from the first occurrence in signal-bank.jsonl. If new, use today's date.
- `status`: "surfaced" if it went into ACT NOW or TRENDS. "watching" if it went into WATCH LIST. "banked" if it only went into the bank.
- `sources`: list the actual source-ids where you found this theme
- `evidence`: one sentence explaining what you observed

**Promotion logic for next cycle:**
- `cycle_count >= 3` AND `status` was never "surfaced" → this should be evaluated for ACT NOW
- `cycle_count >= 2` → this should be in WATCH LIST at minimum
- Theme absent this cycle but `cycle_count >= 2` in bank → this is FADING

## Step 6 — Update Signals Log

Append to `state/signals.jsonl` — ONLY themes that were surfaced (ACT NOW or TRENDS):

```jsonl
{"date": "YYYY-MM-DD", "theme": "snake_case_name", "source_count": N, "engagement_total": N, "signal_type": "TYPE", "cross_source": BOOL}
```

`signal_type`: one of `capability_shift`, `production_reality`, `geopolitical_risk`, `security_awareness`, `tech_writer_relevance`, `market_signal`, `counter_signal`, `early_signal`

## Step 7 — Ask Operator

1. "Which ACT NOW items are you doing? (I'll update trajectory.md)"
2. "Anything to Pass? (I'll exclude from future digests)"
3. "Any manual additions for inbox.md?"

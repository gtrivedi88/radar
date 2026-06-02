# Radar — Personal Capability & Opportunity Intelligence System

**Owner:** Gaurav Trivedi
**Status:** Reviewed, decisions locked, ready for implementation plan
**Date:** 2026-05-27
**Audiences served:** Technical writers, devs-curious-about-AI, hardcore technical
**Revision:** 2026-05-27 incorporated operator review: MRR synthesis architecture (Section 4.4.1), R11 scraping resilience, R12 state concurrency, Q1-Q5 decisions locked

---

## TL;DR

A terminal-native, memory-aware personal intelligence system. Bi-weekly cadence, run on demand by the operator. Ingests ~80 sources across AI, dev, technical writing, investor flow, jobs, conferences, and creator economy. Synthesizes via Claude Code (using the operator's existing Max plan) into a memory-anchored 10-section action-pathed digest. State persists across runs so the assistant knows the operator's beat, what they are learning, what they have already covered, and what is forming. Zero incremental dollar cost.

Differentiator: no existing OSS produces action paths (Blog now / Course prep / CFP / Upskill) or maintains trajectory memory across runs. Closest analogs (Horizon, auto-news) stop at "summarize and deliver." Radar synthesizes for decision-making and remembers across digests.

---

## 1. Mission & Philosophy

The Radar exists to make the operator the most informed person in their three audiences (technical writers, devs-curious-about-AI, hardcore technical) by surfacing what is bleeding edge, what is being asked, what is worth learning, and what others miss.

Money is a lagging indicator of capability plus audience plus craft. The Radar optimizes for being early and useful, not for direct revenue per item. Investor flows are tracked as a source of bleeding-edge signal (where smart money is going equals forming category), not as a ranking dimension for actions.

Tyler Cowen frames information consumption as "the daily self-assembly of synthetic experiences." Radar is the operator's self-assembly machine, tuned to their beat and trajectory.

---

## 2. Differentiation vs Prior Art

| Prior art | What it does | Limitation | How Radar differs |
|---|---|---|---|
| Horizon (4.8k★, MIT) | Multi-source aggregation, scoring, briefings | No memory across runs, no action paths, no course/CFP framing | Fork for ingestion; add state and synthesis and actions |
| auto-news (882★, MIT) | Multi-source plus LLM filter plus TODO generation | Heavy Airflow stack, no course opportunity detection, no profile-driven synthesis | Lighter stack, profile-driven, course-aware |
| Feedly Leo (commercial) | AI feed filter and trend detection | Consumer product, generic, no memory | Personal, memory-aware, action-pathed |
| Particle (commercial) | Multi-source news with Q&A | Consumer news, no beat tuning | Beat-tuned, trajectory-aware |
| a16z Big Ideas (publication) | Pattern detection via expert input | Annual, theirs not yours | Fortnightly, yours, three audiences |
| Stratechery (publication) | Strategic synthesis | One-to-many, not personal | Personal, one-to-one |
| ArxivDigest (OSS) | Personalized paper recs | Single source, single channel | 80+ sources, action-pathed |

**Strategic conclusion:** Fork Horizon for the ingestion base. Replace Horizon's briefing generation with Radar's 10-section action-pathed digest. Add state and memory layer. Add investor-flow, pain-point, and capability source types Horizon does not have.

---

## 3. Architecture Overview

Five components.

```
┌──────────────────────────────────────────────────────────────────┐
│                      Source Registry                              │
│              sources/*.yaml (one file per source)                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              Ingestion Layer (forked from Horizon)                │
│   GitHub Actions cron, Sunday 02:00 UTC, parallel fetchers       │
│   → raw/YYYY-MM-DD/<source-id>.json                              │
│   → appends to state/signals.jsonl                                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       State Store                                 │
│   state/{profile,catalog,trajectory,feedback}.md                  │
│   state/signals.jsonl, state/archive/radar-*.md                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│           Synthesis Layer  (Claude Code slash command)            │
│   /radar reads raw + state, writes archive/radar-YYYY-MM-DD.md   │
│   Updates state/signals.jsonl, optionally state/trajectory.md     │
│   Uses Max plan allowance, zero incremental cost                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Delivery & Feedback                            │
│   Terminal output + git commit to archive                         │
│   Optional: email digest via local SMTP or SendGrid free tier     │
│   Feedback path: edit state/feedback.md or update in-session      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Specifications

### 4.1 Source Registry (`sources/*.yaml`)

Each source is a YAML config. Drop a file equals new source. No code changes.

**Schema:**

```yaml
id: anthropic-cookbook              # unique kebab-case id
name: Anthropic Cookbook            # human-readable
type: github_watch                  # one of: rss, json_api, github_watch, scrape, search_query, investor_signal
config:
  repo: anthropics/anthropic-cookbook
  watch:
    - new_files_in: /recipes
    - releases: true
poll_cadence: weekly                # hourly | daily | weekly
signal_type:                        # multi-valued
  - capability
  - workflow
audience_tags:                      # multi-valued
  - hardcore_tech
  - devs_curious_ai
relevance_tags:                     # free-form
  - claude
  - recipes
  - agentic
pre_filter:
  min_engagement: 0                 # source-dependent floor (stars, score, replies)
  recency_window_days: 14           # ignore items older than this
  dedup_key: title_url              # hash basis for dedup
priority: 1                         # 1 (always include) to 5 (nice-to-have)
```

**Six source types map to six fetcher adapters:**

| Type | What it fetches | Examples |
|---|---|---|
| `rss` | RSS/Atom feeds | Anthropic blog, ArXiv categories, Substack newsletters, Mintlify changelog |
| `json_api` | JSON endpoints | HN Algolia, Reddit `.json`, GitHub API, ProductHunt API |
| `github_watch` | Repo activity | New files in `/recipes`, releases on tracked repos, awesome-list commits |
| `scrape` | HTML with selectors | PyCon site, conference schedules, layoffs.fyi, LinkedIn jobs |
| `search_query` | Recurring search | Crunchbase free filtered, Google Trends, Stack Overflow tag velocity |
| `investor_signal` | Composite funding aggregator | YC Launches + a16z portfolio + Sequoia + Crunchbase free + The Information headlines |

**Nine `signal_type` values** used by synthesis ranking:

| signal_type | Meaning | Synthesis priority |
|---|---|---|
| `news` | Something happened | Low |
| `capability` | Something operator can DO now (new tool, recipe, MCP server, feature) | High |
| `workflow` | Demonstrated how (community post, tutorial, demo) | High |
| `pattern` | Technique/approach (paper, post arguing for X) | Medium |
| `opportunity` | CFP, deadline, course-shaped gap | High |
| `trend` | Delta over time (search, downloads, jobs) | Medium |
| `investor` | Funding event = bleeding-edge marker | Medium |
| `pain_point` | Expressed struggle (course-material seed) | High |
| `skill_velocity` | Skill climbing in demand (jobs, salaries, mentions) | Medium |

### 4.2 Ingestion Layer (forked from Horizon)

GitHub Actions cron runs every Sunday 02:00 UTC. Local manual run via `python ingest.py` for ad-hoc refresh.

**Borrowed from Horizon:**
- Fetcher base classes (RSS, JSON, scrape, GitHub)
- Scorer and deduplicator
- Parallel fetch orchestration
- LLM-agnostic enrichment hooks

**Added to Horizon's base:**
- `investor_signal` composite fetcher (aggregates YC, a16z, Sequoia, Crunchbase free, ProductHunt)
- `pain_point` fetcher (pulls top N comments per top M weekly threads from configured subreddits and HN threads, normalizes to question form via Claude filter)
- `skill_velocity` composite fetcher (LinkedIn job keyword scrape + HN "Who's Hiring" monthly thread text mining + Pay Tech Writers + Layoffs.fyi)
- Output to `raw/YYYY-MM-DD/<source-id>.json` instead of Horizon's briefing format
- Append observations to `state/signals.jsonl` for delta computation

**Output schema (per item in raw JSON):**

```json
{
  "item_id": "sha1-hash",
  "title": "string",
  "url": "string",
  "source_id": "anthropic-cookbook",
  "signal_type": ["capability"],
  "audience_tags": ["hardcore_tech"],
  "timestamp": "ISO8601",
  "raw_text": "string (summary or first N chars)",
  "metrics": {
    "score": 142,
    "comments": 23,
    "stars": null
  },
  "relevance_tags": ["claude", "agentic"],
  "fetched_at": "ISO8601"
}
```

**Pre-filter pipeline (per source):**
1. Recency window (drop items older than `pre_filter.recency_window_days`)
2. Engagement floor (drop items below `pre_filter.min_engagement`)
3. Dedup against prior 30 days of `signals.jsonl` by `dedup_key`
4. Audience tag inheritance from source

Result: bounded set of items per source per run. Synthesis input stays predictable.

**Runtime target:** under 15 minutes for full registry (parallelized).

**Resilience (covers R11 and R12):**

1. **Pre-flight git rebase.** Every ingestion run starts with `git pull --rebase`. If rebase fails (operator has un-pushed local edits to state), the script aborts with a clear error rather than corrupting state. Operator pushes, then re-runs.
2. **Per-fetcher isolation.** Each fetcher runs in its own try/except scope. Failures are logged to `state/fetch-errors.jsonl` (timestamp, source_id, exception class, traceback excerpt). One broken fetcher cannot crash the cron.
3. **Fragility tiers.** Each source YAML carries `fragility_tier: stable | moderate | fragile`. Fragile sources (LinkedIn jobs scrape, comment harvesters) get a `last_success_at` watermark. When the watermark exceeds `staleness_threshold_days`, the next digest's Memory Thread flags the stale source for review.
4. **Append-only state log.** `state/signals.jsonl` is append-only. Concurrent cron and operator edits never produce write-write conflicts. Operator-edited files (`trajectory.md`, `feedback.md`) are never written by cron.
5. **Graceful synthesis degradation.** Synthesis routing tolerates missing intermediate slices. A failed group simply produces empty content in its routed sections rather than crashing the digest.

### 4.3 State Store (`state/`)

The component that makes Radar feel like a personal assistant, not a feed reader.

```
state/
  profile.md         # who you are, beats, audiences, voice, tools, persona
  catalog.md         # blog posts published, courses launched, talks given
  trajectory.md      # currently learning, queued, passed, finished
  feedback.md        # Doing | Pass | Done | Watch per item-id from past digests
  signals.jsonl      # structured signal log, one line per observation
  archive/
    radar-2026-05-27.md
    radar-2026-06-10.md
    ...
```

**`profile.md` (semi-static, drafted once, reviewed quarterly):**

```markdown
# Operator Profile

## Identity
- Name, location, current role
- Audiences served (3): tech_writer, devs_curious_ai, hardcore_tech
- Voice DNA: cinematic, visceral, confrontational, philosophical
- Voice constraints: no em dashes, no AI transitions, no third-person hypotheticals

## Active Tools
- Claude (Max plan, terminal-first via Claude Code)
- Cursor
- NotebookLM
- ...

## Beat (what I write/teach about)
- AI-for-tech-writers craft and workflow
- Claude Code .md-driven development
- AI tool stacks for non-coders
- Tech writer career evolution under AI
- Satire on AI hype

## Topics done / bored of
- Generic "AI will replace writers" takes
- Tool-roundup posts without opinion
- ...

## Where I'm going next
- (free-form, edit anytime)
```

**`catalog.md` (auto-generated from `_posts/`, never re-suggest topics in here):**

```markdown
# Published Work

## Blog Posts (sorted by date)
- 2025-03-20 | Cursor AI for API docs | /cursor-ai-api-doc/
- 2025-04-12 | 365-day AI architect journey | /365-day-ai-architect-journey/
- ...

## Courses
- (empty — no courses launched yet)

## Talks
- (empty)

## Newsletters / Other
- ...
```

**`trajectory.md` (operator-edited, radar reads + nudges):**

```markdown
# Trajectory

## Doing (started, in flight)
- 2026-05-15 | Agentic eval patterns (deep dive) | item-id-from-digest

## Queued (interested, not started)
- AI for localization workflows

## Passed (explored, decided no)
- 2026-04-10 | LangGraph deep dive | reason: too far from beat

## Finished (done and useful)
- 2026-02-01 | Claude Code hooks pattern | result: blog post published
```

**`feedback.md` (one line per item per past digest):**

```markdown
# Feedback Log

2026-05-27 | item-a3f9c1 | Doing
2026-05-27 | item-b8e2d4 | Pass | reason: covered in 2025-03-20 post
2026-05-13 | item-7c4d8f | Done | result: blog draft started
```

**`signals.jsonl` (machine-written by ingestion + synthesis, used for delta computation):**

```jsonl
{"date":"2026-05-27","theme":"agentic_eval","source_count":4,"engagement_total":890}
{"date":"2026-05-13","theme":"agentic_eval","source_count":2,"engagement_total":340}
{"date":"2026-04-29","theme":"agentic_eval","source_count":1,"engagement_total":120}
```

This is how synthesis answers "is this trend climbing or cooling?"

**`archive/radar-YYYY-MM-DD.md`:** the digest itself, committed. Fully queryable later by opening Claude Code in the repo and asking, "what did we see on agentic eval in the last 3 months?"

### 4.4 Synthesis Layer (`.claude/commands/radar.md`)

Claude Code slash command. The load-bearing differentiator.

**Inputs (read in order):**
1. `state/profile.md`
2. `state/catalog.md`
3. `state/trajectory.md`
4. `state/feedback.md`
5. `state/archive/*.md` (last 2 digests only)
6. `state/signals.jsonl`
7. `raw/YYYY-MM-DD/*.json` (current run and previous run for delta context)

**Output:**
- `state/archive/radar-YYYY-MM-DD.md` (the 10-section digest)
- Appended entries to `state/signals.jsonl` (new observations)
- Optionally: edits to `state/trajectory.md` based on user's in-session "mark Doing" feedback

**Synthesis rubric (encoded in slash command):**

1. **Memory check first.** Open the digest with active "Doing" items from `trajectory.md` and their age. Nudge any Doing item aging past 30 days.
2. **Trend computation must use `signals.jsonl`.** A trend requires ≥3 source presence AND non-zero delta vs at least one of the last 2 digests.
3. **Blog topics filter against `catalog.md`.** Never suggest a topic substantially covered in a published post.
4. **Course prep requires multi-signal.** A course suggestion must aggregate ≥3 of: investor_flow signals, pain_points, skill_velocity, question_mining, capability_releases. Otherwise it stays in Watch list, not Course prep.
5. **Trajectory boost.** Items related to active Doing trajectory get a 2x relevance boost.
6. **Pass-list exclusion.** Items the operator marked Pass in `feedback.md` are excluded.
7. **Counter-signal minimum.** At least 2 fading-hype items per digest, to keep the system honest.
8. **Length cap.** Total digest under 2000 words. Each section under 5 items. Sections silently collapse if empty.

**Cost model:** synthesis uses Claude Code Max plan allowance. Zero incremental dollar cost.

#### 4.4.1 Two-Phase Synthesis: Map-Route-Reduce (MRR)

A naive single-prompt synthesis that dumps 14 days of raw JSON from ~80 sources into context will trigger the "Lost in the Middle" phenomenon: even with a 200k context window, attention degrades on middle content and the model silently skips parts of the rubric. To prevent this, synthesis runs in three phases.

**Phase 1 — Map (parallel via Claude Code subagents).**

Roughly 12-15 subagent invocations, one per source *group* (not per source). Groups are configured in `sources/_groups.yaml`:

```yaml
groups:
  rss_ai_labs: [anthropic-blog, openai-blog, deepmind-blog, ...]
  reddit_ai: [r-claudeai, r-localllama, r-machinelearning, ...]
  reddit_dev: [r-programming, r-python, r-javascript, ...]
  reddit_techwriting: [r-technicalwriting, r-devrel]
  github_watches: [anthropic-cookbook, claude-code, awesome-mcp, ...]
  papers: [arxiv-csai, arxiv-cscl, hf-daily-papers]
  conferences: [pycon-us, write-the-docs, neurips, ...]
  investor: [yc-launches, a16z, sequoia, producthunt, crunchbase-free]
  pain_points: [reddit-comment-harvest, hn-comment-harvest, so-questions]
  skill_velocity: [linkedin-jobs, hn-whoshiring, layoffs-fyi]
  capability_claude: [anthropic-cookbook, claude-code-releases]
  capability_cursor: [cursor-changelog, cursor-forum]
  capability_notebooklm: [notebooklm-updates]
  newsletters: [import-ai, last-week-ai, batch, interconnects, ...]
  trends: [google-trends, exploding-topics, npmtrends]
```

Each subagent:
- Reads only its slice of `raw/YYYY-MM-DD/`
- Scores items against `profile.md` and `audience_tags`
- Outputs `intermediate/<group>.md`, capped at ≤500 words

Total intermediate state: ~15 groups × 500 words = ~7,500 words. Comfortably inside the attention sweet spot.

**Phase 2 — Route (main thread).**

For each of the 11 digest sections (Memory thread + 10 numbered), the synthesis prompt reads only the intermediate slices and state files relevant to that section. Routing table:

| Section | Reads (intermediate slices) | Reads (state) |
|---|---|---|
| 0 Memory thread | none | trajectory.md, feedback.md |
| 1 Top 5 trends | all groups | signals.jsonl |
| 2 What people are asking | reddit_*, pain_points | catalog.md, profile.md |
| 3 Bleeding edge to learn | capability_*, papers | trajectory.md, profile.md |
| 4 Skill velocity | skill_velocity | profile.md |
| 5 Course prep | investor, pain_points, skill_velocity, reddit_*, capability_* | catalog.md, profile.md |
| 6 Investor flow | investor | profile.md |
| 7 CFPs | conferences | profile.md, feedback.md |
| 8 Capability of the fortnight | capability_claude, capability_cursor, capability_notebooklm | trajectory.md |
| 9 Pain points | pain_points | profile.md |
| 10 Watch + counter | all groups | signals.jsonl, archive/* |

Each section's prompt sees a focused payload, not the haystack.

**Phase 3 — Stitch (main thread).**

Single pass to verify cross-section consistency (no contradictions, trajectory alignment), enforce counter-signal minimum, apply length cap, write final `archive/radar-YYYY-MM-DD.md`, append observations to `signals.jsonl`.

**Fallback if MRR strains limits in v2 (full 80 sources):** per-section slash commands (`/radar-section trends`, `/radar-section course`, etc.) so the operator can regenerate weak sections without redoing the whole digest.

### 4.5 Delivery & Feedback

**Primary delivery:** terminal output when `/radar` runs. Operator reads in Claude Code session.

**Persistent delivery:** GitHub Actions commits `state/archive/radar-YYYY-MM-DD.md` to the private repo. Queryable later.

**Optional email:** thin `deliver.py` script that reads the latest archive file and sends via local SMTP or SendGrid free tier. Only if operator wants a push notification.

**Feedback paths:**
- During session: tell Claude "mark item-a3f9c1 Doing" and it edits `state/feedback.md` and `state/trajectory.md`
- Between sessions: edit `state/feedback.md` or `state/trajectory.md` directly and commit. Next `/radar` reads it.

---

## 5. Digest Structure: Memory Thread + 10 Sections (full specification)

The digest opens with a Memory Thread (section 0) that grounds the operator in their prior commitments, followed by 10 numbered sections each serving a distinct decision surface. Sections collapse silently when empty.

| # | Section | Input sources | Synthesis logic | Output format | Quality threshold to surface |
|---|---|---|---|---|---|
| 0 | **Memory thread** | trajectory.md, feedback.md | List active Doing items + age, nudge anything >30 days | "Status check on N items from past digests:" + bullet list | Always present if any Doing items exist |
| 1 | **Top 5 trends this fortnight** | signals.jsonl deltas across all sources | Cross-source synthesis, weighted by source count + engagement + delta | 5 themes, each with: name, 1-line synthesis, delta direction (↑/↓/→), 2-3 source links | Each trend must show ≥3 source presence AND non-zero delta |
| 2 | **What people are asking** (3-5) | pain_point sources (Reddit/HN comments, SO questions, Bluesky) | Mine questions in audience segments, normalize to question form, dedup | Per item: question, where asked, angle for operator's voice, why now | Skip if substantially covered in catalog.md |
| 3 | **Bleeding edge to learn** (1-2) | capability + pattern signals, biased to recent + high-engagement | Pick deep-dive items. Cross-reference trajectory.md for continuity. | Per item: topic, starter resources, 90-min first-touch plan, "continues from X" if applicable | Must be in operator's beat tags |
| 4 | **Career skill velocity** | skill_velocity composite (jobs, salaries, mentions) | Compute delta in skill keyword frequency over 4 weeks | Top 3 climbing skills + 1 cooling skill, with absolute numbers and delta | ≥20% delta over 4 weeks to surface |
| 5 | **Course prep** (0-2) | Cross-source pattern detection | Detect multi-signal patterns (≥3 signal types align on a topic) | Per course: topic, why now (signals listed), audience cut, closest competitor course + gap, suggested 5-module outline | Must aggregate ≥3 of: investor_flow, pain_points, skill_velocity, question_mining, capability_releases |
| 6 | **Investor flow** | investor_signal composite | Group fundings by theme, surface notable raises | Top 3-5 themes this fortnight + count + notable companies, implication for operator's beat | At least 2 fundings in same theme to surface that theme |
| 7 | **CFPs and speaking** | conference + CFP sources | Filter to closing in ≤30 days, rank by fit (audience match) + authority (conference tier) | Per CFP: name, deadline, talk angle suggestion | Audience match required |
| 8 | **Capability of the fortnight** (1) | capability signals tagged Claude/Cursor/NotebookLM/active tool stack | Pick most replicable workflow from past 14 days | Workflow name, what it unlocks, copy-pasteable starter (30-min replication), source link | Must be replicable in ≤30 min |
| 9 | **Pain points harvested** (5-10) | pain_point fetcher output | Surface raw quotes (anonymized), tag by audience segment | Per quote: text excerpt, source link, audience tag | At least 3 upvotes/replies on source comment |
| 10 | **Watch list + counter-signal** | trend signals not yet ready + fading hype | Track forming signals across digests; surface fading hype to deprioritize | Watch: 3-5 forming themes with delta direction. Counter: 2+ fading items with evidence | Counter requires negative delta over 4+ weeks |

---

## 6. Source Catalog (initial seed for v2)

~80 sources across 14 categories. Each becomes a YAML file in `sources/`.

**Conferences and CFPs**
- Tech writing: Write the Docs (PDX, Prague, AU), API the Docs, STC Summit, LavaCon, TC Camp, DevRelCon, Tekom
- Dev: PyCon US/India/EU/AU/UK/JP, DjangoCon, RubyConf, RailsConf, JSConf, React Conf, GopherCon, RustConf, KubeCon, DockerCon, HashiConf, FOSDEM, All Things Open, DevOps Days
- Cloud/enterprise: AWS re:Invent, Google Cloud Next, Microsoft Build, Red Hat Summit
- Security: DEF CON, Black Hat, BSides, USENIX Security, Nullcon
- AI academic: NeurIPS, ICML, ICLR, ACL, EMNLP, CVPR, AAAI
- AI industry: AI Engineer Summit, AI Engineer World's Fair, LangChain Interrupt, Ray Summit, ODSC, OpenAI DevDay, Anthropic events
- Aggregators: Sessionize, Papercall, Confbuddy

**Tech writing community**
- Write the Docs Slack public channels
- Tom Johnson's "I'd Rather Be Writing" RSS
- The Content Wrangler newsletter
- Cherryleaf blog + podcast
- DocOps community
- API the Docs YouTube + newsletter

**Reddit (specific subs)**
- r/MachineLearning, r/LocalLLaMA, r/ClaudeAI, r/OpenAI
- r/technicalwriting, r/devrel
- r/programming, r/python, r/javascript, r/rust, r/golang
- r/sideproject, r/SaaS

**HN + Lobsters + DEV.to + Hashnode** (front-page + trending tags)

**AI lab blogs (RSS)**
- Anthropic, OpenAI, Google DeepMind, Google Research, Meta AI, Microsoft Research, Mistral, Cohere, Hugging Face, xAI, Together, Replicate

**Newsletters (Substack/Beehiiv RSS)**
- Import AI, Last Week in AI, The Batch, Interconnects, Stratechery, Platformer, Bens Bites, TLDR AI, The Pragmatic Engineer, Latent Space

**Podcasts (RSS for transcripts/show notes)**
- Latent Space, Hard Fork, ChinaTalk, Practical AI, The Pragmatic Engineer, a16z, Lex Fridman

**YouTube channels (curated)**
- AI Explained, Two Minute Papers, Sam Witteveen, Matthew Berman, Bycloud, Cole Medin, Theo, Primeagen, Fireship
- Official: PyCon channel, NeurIPS, KubeCon

**Research**
- ArXiv cs.AI/cs.CL/cs.LG, Papers with Code trending, Hugging Face Daily Papers, AlphaXiv

**GitHub watchers**
- anthropics/anthropic-cookbook (new files in /recipes, releases)
- anthropics/claude-code (releases, examples folder)
- awesome-claude-code, awesome-claude-prompts, awesome-mcp-servers, awesome-claude-skills (commits)
- GitHub Trending overall + per-language
- Star velocity for tracked repos: LangChain, LlamaIndex, Pydantic AI, CrewAI, AutoGen

**AI dev tools (changelogs)**
- Cursor, Windsurf, Zed AI, Aider, Continue.dev
- v0.dev, Bolt.new, Lovable
- LangChain, LangGraph, LlamaIndex
- Vercel AI SDK

**AI-for-docs tools (changelogs)**
- Mintlify, ReadMe.io, Document360, Scribehow, Fern, GitBook, Notion AI

**Microblogging post-X**
- Bluesky (open AT Protocol API)
- Mastodon instance feeds

**Trend signals**
- Google Trends (pytrends), Exploding Topics, npmtrends, Stack Overflow tag velocity

**Job board signals**
- LinkedIn Jobs keyword frequency (Claude, prompt engineer, technical writer + AI, developer experience)
- HN monthly Who's Hiring thread (text mining)
- Layoffs.fyi (filtered for content/docs/DX/AI roles)

**Investor flow**
- a16z portfolio + Big Ideas + public posts
- Sequoia portfolio + thought pieces
- YC batch lineups + Launches
- ProductHunt top of week
- Crunchbase free tier
- BetaList
- HN "Show HN" with first-week traction filter

**Regulatory/policy**
- EU AI Act news, NIST AI RMF, White House AI EO, India MeitY

---

## 7. Phased Rollout

### v0 — Week 1 (1-2 hours of operator time, 4-6 hours of build time)

Goal: working radar with manual inbox plus 1 auto source, end-to-end. Run today, get value today.

**Build:**
- Init `radar/` project (new repo or subdir of this one, operator decides)
- Scaffold directory structure (`sources/`, `state/`, `raw/`, `archive/`, `scripts/`)
- Write `.claude/commands/radar.md` (the synthesis prompt)
- Wire 1 automated source: HN Algolia API (zero auth, 30 lines of Python). Writes to `raw/YYYY-MM-DD/hn-algolia.json`.
- Add `inbox.md` for manual paste-as-you-go links during the fortnight

**Operator inputs (15 minutes):**
- Review `profile.md` draft (I generate from last 15-20 posts + CLAUDE.md), correct
- Confirm `catalog.md` (auto-generated from `_posts/` listing + frontmatter)
- Initialize empty `trajectory.md` and `feedback.md`

**Outcome:** operator runs `/radar` after pasting 5-10 links into inbox, gets the first 10-section digest.

### v1 — Weeks 2-3 (half-day of build time)

Goal: 10 high-value automated sources running on cron. Manual inbox supplements.

**Build:**
- Fork Horizon, strip what we do not need (briefing generator, Telegram delivery)
- Wire 10 fetchers using Horizon's adapter base:
  1. HN Algolia (already in v0)
  2. r/ClaudeAI top weekly (`json_api`)
  3. r/MachineLearning top weekly (`json_api`)
  4. r/technicalwriting top weekly (`json_api`)
  5. Anthropic blog RSS (`rss`)
  6. anthropics/anthropic-cookbook (`github_watch`, new files in /recipes + releases)
  7. ArXiv cs.AI + cs.CL daily (`rss`)
  8. Hugging Face Daily Papers (`rss` or `scrape`)
  9. GitHub Trending Python + JS daily (`scrape`)
  10. Mintlify changelog (`rss` or `scrape`)
- GitHub Actions cron, Sunday 02:00 UTC, commits raw output to repo
- Pain-point harvester v1: top 10 comments from top 5 weekly threads in 5 tracked subreddits, Claude-filtered for question form, output to `raw/YYYY-MM-DD/pain-points.json`

**Outcome:** 70% of high-signal coverage. Operator's manual inbox becomes supplement, not primary.

### v2 — Month 2 onward

Goal: full source registry. Investor flow live. Skill velocity live. Synthesis prompt tuned.

**Build:**
- Expand to full ~80 source registry (one YAML at a time, no code changes)
- Add `investor_signal` composite fetcher (YC + a16z + Sequoia + ProductHunt + Crunchbase free + BetaList)
- Add `skill_velocity` composite fetcher (LinkedIn jobs keyword scrape + HN Who's Hiring text mining + Layoffs.fyi)
- Tune synthesis prompt across digests 4-6 (rubric refinement based on what surfaced well vs poorly)
- Add quarterly memory compaction (digest #6, #12, #18, ...): archive signals older than 180 days, review profile for drift, garbage-collect feedback log

### v3 — Optional later phases

- Daily ping channel with hard-coded triggers (new Claude/Cursor model, Anthropic Cookbook major release, top-tier CFP closing in <48h)
- Web dashboard for archive search (only if needed; Claude Code in repo handles ad-hoc queries today)
- Multi-channel delivery (email + Telegram + Slack)
- Bluesky / Mastodon sources once their APIs harden
- X/Twitter source if it becomes cost-effective

---

## 8. Quality Metrics

How we know it is working.

| Metric | Definition | Target | Review cadence |
|---|---|---|---|
| Acted-on rate | % of items per digest that get a Doing tag within 14 days | ≥30% | Per digest |
| Source ROI | Sources whose items never get Doing/Watch tag in 90 days | Prune at 0 | Quarterly |
| Course prediction precision | Course suggestions where operator would consider building | ≥1 of every 4 | Month 6 |
| Memory accuracy | Repeated topics from `catalog.md` (should be 0) | 0 errors | Per digest |
| Signal-to-hype ratio | Counter-signal items per digest | ≥2 | Per digest |
| Time to digest | Operator time from "/radar invoked" to "I've read it" | ≤15 min | Per digest |
| Source coverage gap | High-signal stories operator finds elsewhere but Radar missed | ≤2 per fortnight | Per digest |

---

## 9. Risk Register & Self-Critique

Ranked by likelihood times impact.

**R1. Pain-point harvesting is the hardest component.**
Pulling meaningful quotes from Reddit/HN/SO comment threads (not headlines) requires careful filtering. Cheap implementation produces "people are confused about prompts" output.
*Mitigation:* focused approach. Pull top 10 comments from top 5 weekly threads in 10 tracked subreddits. Claude filters for "expressed pain/struggle/question," normalizes to question form. Costs zero because synthesis runs through Claude Code Max.

**R2. Multi-signal course pattern detection requires real reasoning.**
"These 4 signals suggest a course on Y" is the hardest synthesis step. Digests 1-3 will produce weak suggestions.
*Mitigation:* explicit rubric in synthesis prompt. Course suggestion requires ≥3 distinct signal types aligned on a topic. Otherwise it stays in Watch list. Quality threshold over volume. Expect prompt tuning across digests 4-6.

**R3. Memory rot.**
`signals.jsonl` grows forever. `catalog.md` drifts. Feedback log accumulates.
*Mitigation:* quarterly garbage-collection in digests 6, 12, 18 ... Archive signals older than 180 days. Profile drift review. Feedback log compaction.

**R4. Investor-flow data is fragmented and partly paywalled.**
Crunchbase real-time costs money. The Information is paywalled.
*Mitigation:* use free first (YC, ProductHunt, HN Show, a16z + Sequoia public, BetaList, Crunchbase free tier). The Information is scrape-able for headlines, borderline ethically; default off. Free sources suffice for fortnightly cadence.

**R5. 10 sections may overwhelm.**
Bi-weekly digest of 10 sections is dense.
*Mitigation:* each section caps at 3-5 items. Total digest under 2000 words. Sections collapse silently if empty. Structured for skim then deep-read on tagged items.

**R6. "Top 5 trends" risks generic AI-hype output.**
A "trend" must be computed from operator's source pool with delta vs operator's own history, not "everyone says AI agents are big."
*Mitigation:* synthesis prompt enforces "trend must show across ≥3 of operator's tracked sources AND have non-zero delta vs last 2 digests."

**R7. Profile and catalog seeding is load-bearing.**
Without these, every section reads generic.
*Mitigation:* v0 includes drafting `profile.md` from operator's last 15-20 posts + CLAUDE.md, plus auto-generating `catalog.md` from `_posts/` directory. Operator corrects in 15 minutes. Then everything downstream is sharp.

**R8. Context window saturation and attention degradation ("Lost in the Middle").**
The acute risk is not Max plan rate limits, it is attention drift. Dumping 14 days of JSON from ~80 sources alongside state files into a single prompt will trigger the documented "Lost in the Middle" phenomenon (Liu et al., 2024): even with 200k context, attention degrades on middle content and the model silently skips parts of the 11-section rubric. Symptoms: missing sections, weak synthesis, contradictions across sections.
*Mitigation:* Map-Route-Reduce architecture (Section 4.4.1) is the primary mitigation. Phase 1 parallel subagents condense raw input per source group to ≤500 words each (~7,500 words intermediate state total, well inside the attention sweet spot). Phase 2 routing ensures each section reads only its relevant slices. Phase 3 stitch enforces cross-section consistency. Aggressive pre-filtering at ingestion (recency, min engagement, dedup) further bounds input. If MRR still strains at v2 scale, per-section slash commands provide a per-section regeneration path.

**R9. Bi-weekly is too slow for genuine capability drops.**
Anthropic ships features faster than every 14 days. Capability could arrive on day 3 of cycle, operator reads about it 11 days later from elsewhere.
*Mitigation:* daily ping channel deferred to v3, with hard-coded triggers (new Claude/Cursor model, Cookbook major release, top-tier CFP closing in <48h). Daily check, only fires on triggers. Separate from digest cadence.

**R10. Horizon may change direction or get abandoned.**
Forking an upstream creates an upstream-dependency risk.
*Mitigation:* once forked, treat it as our own codebase. No expectation of merging back. Watch upstream for security fixes; ignore feature drift.

**R11. Scraping fragility.**
RSS and stable JSON APIs (HN Algolia, Reddit `.json`, GitHub API) are reliable. LinkedIn jobs scraping, Reddit/HN comment harvesting at depth, and conference site schedule parsing are notoriously brittle. Anti-bot measures break fetchers frequently. A single broken fetcher cannot crash the full Sunday cron run.
*Mitigation:*
1. Each fetcher runs in its own try/except scope. Failures are logged to `state/fetch-errors.jsonl` with timestamp, source_id, exception class, traceback excerpt. The cron continues to the next source.
2. Each source YAML carries a `fragility_tier` field (`stable`, `moderate`, `fragile`). Fragile sources get a `last_success_at` watermark. If watermark age exceeds `staleness_threshold_days` (default 14), the next digest's Memory Thread flags "source X has not returned data in N days, consider review."
3. Synthesis is tolerant of missing source files: routing table degrades gracefully when a group's intermediate is missing or empty.
4. Quarterly source ROI review (Section 8 metric) prunes consistently-failing sources.

**R12. State concurrency between cron and local edits.**
GitHub Actions cron commits to `state/signals.jsonl` Sunday 02:00 UTC. If the operator was editing `trajectory.md` or `feedback.md` locally without pushing, the next pull triggers merge conflicts. Worse, a partial state can be read mid-write by `/radar`.
*Mitigation:*
1. `ingest.py` (and `/radar` slash command's startup hook) runs a mandatory pre-flight: `git pull --rebase` before any read. If rebase fails, the script aborts with a clear error rather than continuing on stale or conflicted state.
2. `state/signals.jsonl` is append-only with line-based concurrency: cron always appends, never rewrites. Merge conflicts on append-only logs auto-resolve cleanly.
3. `state/trajectory.md` and `state/feedback.md` are operator-edited. Cron never writes these. Eliminates the write-write conflict class entirely.
4. `/radar` writes only `state/archive/radar-YYYY-MM-DD.md` (new file, never conflicts) and appends to `state/signals.jsonl`.

---

## 10. Decisions (formerly open questions)

All decided as of 2026-05-27.

**Q1. Where does the Radar repo live?** → **Decided: private GitHub repo `gautriv/radar`.**
State files contain personal trajectory and strategic context. Isolating from the public Jekyll blog repo prevents accidental exposure. GitHub Actions cron runs on free tier. The Jekyll blog repo is unaffected.

**Q2. Email delivery in v0?** → **Decided: off.**
Terminal output and git history are sufficient while proving the core synthesis loop. Eliminates networking, auth, and SMTP overhead from v0. Email can be added in v1 if push notification becomes desirable.

**Q3. Profile draft: from posts or cold?** → **Decided: from posts.**
Drafting `profile.md` from the operator's last 15-20 posts plus CLAUDE.md is faster and gives the operator a flawed-but-concrete draft to correct, which is easier than facing a blank page. Confronting and editing an LLM's inference of voice is a higher-leverage operator task than cold writing.

**Q4. Audience-segmented digest or unified?** → **Decided: unified, with audience tags visible.**
Splitting by audience would dilute cross-pollination (e.g., a hardcore-tech workflow that simplifies into a tech-writer-friendly tutorial). Unified digest preserves these crossover seeds. Each item carries `audience_tags` so operator can skim by audience when scanning.

**Q5. Quarterly memory compaction: automatic or manual?** → **Decided: automatic.**
Manual janitorial work gets deferred until the repo bloats and synthesis slows. Automated compaction on digest counter (digests #6, #12, #18, ...) archives signals older than 180 days, reviews profile for drift, and compacts the feedback log.

---

## 11. Implementation Sequence (preview)

The implementation plan will be written separately via the writing-plans skill. The expected sequence:

1. Init repo and directory structure
2. Generate `profile.md` (from posts + CLAUDE.md)
3. Auto-generate `catalog.md` (from `_posts/`)
4. Write `.claude/commands/radar.md` synthesis prompt
5. Implement HN Algolia fetcher (v0 single source)
6. First end-to-end `/radar` test run
7. Fork Horizon, prepare local copy
8. Wire v1's 10 source fetchers using Horizon's adapter base
9. Set up GitHub Actions cron
10. Implement pain-point harvester v1
11. Run digests 1-3 with manual evaluation
12. Tune synthesis prompt based on results
13. Expand to full source registry (v2)
14. Add investor_signal composite fetcher
15. Add skill_velocity composite fetcher
16. Add quarterly memory compaction
17. Document everything for future operator self-modification

---

## 12. Glossary

- **Action path** — a category of decision the digest surfaces (Blog now, Course prep, CFP, Upskill, Watch). Not a flat list.
- **Beat** — the operator's defined area of focus (tech writers, devs-curious-about-AI, hardcore tech).
- **Capability** — something the operator can DO now that they could not before (new tool, new recipe, new workflow).
- **Counter-signal** — an item indicating something is fading. Surfaced to prevent investing in dying tools/topics.
- **Delta** — change in a signal's strength compared to prior digests. Computed from `signals.jsonl`.
- **Doing / Pass / Done / Watch** — feedback states on past digest items. Updates `feedback.md`.
- **Item-id** — SHA-1 hash unique per item. Used in feedback log and trajectory.
- **Pain point** — an expressed struggle or question from a real user, harvested from comment threads. Course material seed.
- **Signal type** — classification of an item (news, capability, workflow, pattern, opportunity, trend, investor, pain_point, skill_velocity).
- **Source registry** — `sources/*.yaml` directory. Adding a source equals adding a YAML file.
- **Synthesis** — the Claude Code slash command that turns raw + state into a digest.
- **Trajectory** — what the operator is currently learning, queued, passed, finished. Persists across runs.

---

**End of design spec. Awaiting operator review before implementation plan.**

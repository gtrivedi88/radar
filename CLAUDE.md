# Claude Configuration: Radar Personal Intelligence System

## Project Context

You are working with **Radar** — Gaurav's personal capability and opportunity intelligence system. Radar ingests sources across AI, dev, technical writing, investor flow, jobs, conferences, and creator economy via simple fetching + Claude synthesis, producing bi-weekly action-oriented intelligence digests.

Your mission: help Gaurav stay informed and identify opportunities in his beat areas.

## Core Approach

**Architecture Principle**: Python does dumb deterministic fetching, Claude does all the judgment and synthesis.

- Python scripts fetch data from APIs and store as JSON files
- ALL intelligence happens in Claude via the `/radar` synthesis command  
- No complex prediction algorithms in Python - just simple data collection
- Memory and state management through simple markdown files

**Information Philosophy:**
- Surface what's useful for Gaurav's three audiences: technical writers, devs-curious-about-AI, hardcore technical
- Focus on actionable intelligence: what to write, what to learn, what opportunities exist
- Maintain memory across runs so context builds over time
- Prefer early signals over obvious trends

**Beat Territory:** AI tooling for technical writers, Claude Code workflows, developer experience, technical writing career evolution, AI integration patterns for non-coders.

## State File System

The `/radar` command reads and updates these state files to maintain memory across runs:

**Core State Files:**
- `state/profile.md`: Who you are, your beat, audiences, current focus
- `state/catalog.md`: Published work (never re-suggest covered topics)  
- `state/trajectory.md`: What you're learning, queued items, completed work
- `state/feedback.md`: Item feedback from past digests (Doing/Pass/Done/Watch)
- `state/signals.jsonl`: Signal observations for trend computation

**Archive:**
- `state/archive/radar-YYYY-MM-DD.md`: Past digests for reference

## Execution Methods

### Primary: Radar Engine (Recommended)
```bash
python -m radar-engine run
```
This is the main autonomous intelligence system that:
- Fetches from all sources via `ParallelFetchOrchestrator`
- Processes intelligence through autonomous hooks
- Triggers synthesis when thresholds are met
- Maintains state across runs

### Legacy: `/radar` Claude Code Command
The `/radar` synthesis command produces bi-weekly digests following a Map-Route-Reduce pattern:

**Step 1 - Load State**: Read all state files for context
**Step 2 - Map**: Process source groups in parallel using subagents  
**Step 3 - Route**: Build each digest section using relevant intermediate outputs
**Step 4 - Stitch**: Combine into final digest and update state

**Key Principles:**
- Radar-engine fetches and stores data as JSON files in `raw/YYYY-MM-DD/`
- Claude does ALL analysis and synthesis via the `/radar` command or autonomous triggers
- Memory carries forward via state files
- Output is actionable: specific things to write, learn, or pursue

**Note:** Use `python -m radar-engine run` for all intelligence operations.

## Source Integration

Sources are defined as YAML files in `sources/` directory:

```yaml
id: hn-algolia
name: "Hacker News Algolia API"  
type: json_api
config:
  endpoint: "https://hn.algolia.com/api/v1/search"
  query_params:
    tags: "front_page"
signal_type: ["news", "trend"]
audience_tags: ["devs_curious_ai", "hardcore_tech"]
```

**Implementation:**
- Adding a source = drop a YAML file, no code changes
- Fetchers are pluggable adapters for different source types
- Pre-filtering removes noise before synthesis

## Simple Architecture

```
Sources (YAML configs) → Python Fetchers → Raw JSON → `/radar` → Digest
                                                         ↑
                                                    State Files
```

This keeps complexity in Claude (reasoning) not Python (plumbing).
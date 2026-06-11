---
name: fetch
description: Fetch data using the autonomous radar-engine system
---

# Fetch Sources

Run the autonomous intelligence engine to collect data from all enabled sources and perform intelligent analysis.

## What This Does

1. Reads all `*.yaml` files from `sources/` directory
2. Fetches data from enabled sources (HN, Anthropic blog, etc.)
3. Processes through autonomous hooks and thresholds
4. Saves normalized data to `raw/YYYY-MM-DD/<source-id>.json`
5. Updates autonomous state and triggers strategic alerts

## Usage

```bash
# Install dependencies (first time)
pip install -r requirements.lock

# Single intelligence cycle
python -m radar-engine run

# Set up autonomous loops
python -m radar-engine setup-loops

# Continuous autonomous monitoring
python -m radar-engine continuous
```

## Output

- Creates `raw/YYYY-MM-DD/` directory with normalized JSON
- Updates autonomous state in `state/autonomous-loops.json`
- Logs threshold alerts to `state/threshold_alerts.jsonl`
- Detects course opportunities and strategic signals

Example output format:
```json
{
  "source": "hn-algolia", 
  "fetched_at": "2026-06-11T10:30:00Z",
  "items": [
    {
      "title": "Article Title",
      "url": "https://example.com", 
      "score": 42,
      "comments": 15,
      "timestamp": "2026-06-11T09:00:00Z",
      "source_id": "hn-algolia"
    }
  ]
}
```

## Autonomous Features

- **Threshold Monitoring**: Automatically detects high-engagement items (>1000 points)
- **Course Opportunities**: Multi-signal analysis for course development opportunities
- **Strategic Hooks**: Real-time alerts for positioning opportunities
- **Memory Integration**: Builds context across multiple intelligence cycles

## Next Steps

After autonomous fetching:
1. Check `state/threshold_alerts.jsonl` for strategic opportunities
2. Run `/radar` to synthesize intelligence digest
3. Review course opportunities if any were detected
4. Monitor autonomous loops for ongoing intelligence
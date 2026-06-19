---
name: fetch
description: Fetch data from all configured sources
---

# Fetch Intelligence Data

```bash
python -m radar-engine run
```

This fetches from all enabled sources in `sources/`, deduplicates, and saves raw JSON to `raw/YYYY-MM-DD/`. Takes ~1 second.

After fetching, run `/radar` to synthesize the data into actionable intelligence.

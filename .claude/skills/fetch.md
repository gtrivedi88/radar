---
name: fetch
description: Fetch data from all configured sources using the modular YAML system
---

# Fetch Sources

Run the source fetcher to collect data from all enabled sources defined in `sources/`.

## What This Does

1. Reads all `*.yaml` files from `sources/` directory
2. Fetches data from enabled sources (HN, Anthropic blog, etc.)
3. Normalizes data format
4. Saves to `raw/YYYY-MM-DD/<source-id>.json`

## Usage

```bash
# Install dependencies (first time)
pip install -r requirements.txt

# Fetch from all enabled sources
python scripts/fetch_sources.py
```

## Output

- Creates `raw/YYYY-MM-DD/` directory
- One JSON file per source with normalized format:

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

## Next Steps

After fetching, run `/radar` to synthesize the intelligence digest.
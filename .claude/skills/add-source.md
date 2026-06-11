---
name: add-source
description: Add a new source to the modular YAML configuration system
---

# Add Source

Add a new data source to the Radar system by creating a YAML configuration.

## Source Types Supported

1. **json_api** - REST APIs that return JSON
2. **rss** - RSS/Atom feeds  
3. **github_watch** - GitHub repository monitoring (future)
4. **scrape** - Web scraping (future)

## YAML Template

Create a new file in `sources/<source-id>.yaml`:

```yaml
id: unique-source-id
name: "Human Readable Name"
description: "What this source provides"
type: json_api|rss|github_watch|scrape
enabled: true

config:
  endpoint: "https://api.example.com/endpoint"
  method: "GET"  # Usually GET
  query_params:
    key: value
  headers:
    User-Agent: "Radar/1.0"
  auth_env: "API_KEY_ENV_VAR"  # Optional

# Signal classification
signal_type: ["news", "capability", "trend", "investor"]
audience_tags: ["tech_writer", "devs_curious_ai", "hardcore_tech"]
relevance_tags: ["ai", "programming", "documentation"]

# Pre-filtering
pre_filter:
  min_engagement: 5
  recency_window_hours: 72
  dedup_key: "url"

# Metadata
priority: 1  # 1=highest, 5=lowest
poll_cadence: "daily"
auth_required: false
```

## Examples

**Reddit Subreddit:**
```yaml
id: r-programming
name: "r/programming"
type: json_api
config:
  endpoint: "https://www.reddit.com/r/programming/hot.json"
  query_params:
    limit: 25
```

**Company Blog:**
```yaml
id: openai-blog
name: "OpenAI Blog"
type: rss
config:
  endpoint: "https://openai.com/blog/rss.xml"
```

## Test New Source

```bash
# Add source YAML file
# Then test fetch
python scripts/fetch_sources.py
```
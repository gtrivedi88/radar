---
name: add-source
description: Add a new intelligence source
---

# Add a Source

Drop a YAML file in `sources/`. No code changes needed.

## Template

```yaml
id: new-source
name: "Source Name"
type: json_api    # or rss
enabled: true

config:
  endpoint: "https://api.example.com/articles"
  method: "GET"
  query_params:
    limit: 20
  headers:
    User-Agent: "Radar/1.0"
  results_key: "items"         # optional: key containing array
  field_map:                   # optional: map fields
    title: ["title"]
    url: ["url", "link"]
    score: ["points", "score", "reactions_count"]
    comments: ["comments_count", "num_comments"]
    timestamp: ["created_at", "published_at"]
    content: ["description", "summary"]

signal_type: ["trend", "news"]
audience_tags: ["devs_curious_ai"]

pre_filter:
  min_engagement: 5
  recency_window_hours: 168
  dedup_key: "url"

priority: 2
```

## Test

```bash
python -m radar-engine run
```

Verify the source appears in output and raw JSON is saved.

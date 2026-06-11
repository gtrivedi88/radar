# Adding Intelligence Sources

Radar uses YAML configuration files to define intelligence sources. Adding a new source is as simple as dropping a YAML file in the `sources/` directory.

## Source Types

### JSON API Sources

For REST APIs that return JSON data:

```yaml
id: example-api
name: "Example API Source"
type: json_api
config:
  endpoint: "https://api.example.com/v1/trending"
  query_params:
    limit: 20
    category: "tech"
  headers:
    Authorization: "Bearer ${API_KEY}"
signal_type: ["news", "trend"]
audience_tags: ["devs_curious_ai", "hardcore_tech"]
update_frequency: "6h"
```

### RSS/Atom Feeds

For RSS or Atom feeds:

```yaml
id: tech-blog
name: "Tech Blog RSS"
type: rss
config:
  endpoint: "https://blog.example.com/feed.xml"
signal_type: ["opinion", "trend"]
audience_tags: ["tech_writer"]
update_frequency: "12h"
```

### Web Scraping

For structured web scraping:

```yaml
id: forum-trends
name: "Forum Trending Topics"
type: scrape
config:
  endpoint: "https://forum.example.com/trending"
  selectors:
    title: "h2.post-title a"
    url: "h2.post-title a[href]"
    score: ".vote-count"
    comments: ".comment-count"
signal_type: ["behavioral"]
audience_tags: ["hardcore_tech"]
update_frequency: "4h"
```

## Configuration Fields

### Required Fields

- **`id`**: Unique identifier for this source
- **`name`**: Human-readable name
- **`type`**: Source type (`json_api`, `rss`, `scrape`)
- **`config`**: Type-specific configuration

### Optional Fields

- **`signal_type`**: Array of signal types this source provides
  - `"news"`: Breaking news and announcements
  - `"trend"`: Trending topics and discussions  
  - `"opinion"`: Expert opinions and analysis
  - `"behavioral"`: Community behavior signals
  - `"economic"`: Funding, acquisition, market data

- **`audience_tags`**: Target audiences for this content
  - `"tech_writer"`: Technical writers and documentarians
  - `"devs_curious_ai"`: Developers interested in AI
  - `"hardcore_tech"`: Deep technical audience

- **`update_frequency`**: How often to fetch this source
  - Format: `"4h"`, `"12h"`, `"1d"`, etc.

## Environment Variables

Use environment variables for sensitive data like API keys:

```yaml
config:
  headers:
    Authorization: "Bearer ${HACKERNEWS_API_KEY}"
```

Set the variable in your environment:
```bash
export HACKERNEWS_API_KEY="your-api-key-here"
```

## Testing New Sources

1. **Create the YAML file** in `sources/`
2. **Test the configuration**:
   ```bash
   python scripts/test_source.py sources/your-source.yaml
   ```
3. **Run a fetch**:
   ```bash
   python scripts/fetch_sources.py --source your-source-id
   ```
4. **Check the output**:
   ```bash
   ls raw/$(date +%Y-%m-%d)/
   ```

## Source Examples

Check the `sources/` directory for working examples:
- `sources/hn-algolia.yaml` - Hacker News API
- `sources/anthropic-blog.yaml` - RSS feed example

## Rate Limiting

Sources should be configured with appropriate rate limiting:

```yaml
config:
  rate_limit:
    requests_per_minute: 60
    retry_after: 300  # seconds to wait after rate limit
```

The fetching system automatically respects rate limits and implements exponential backoff.

## Quality Filters

Add quality filters to reduce noise:

```yaml
config:
  quality_filters:
    min_score: 50        # Minimum engagement score
    min_comments: 5      # Minimum comment count
    exclude_patterns:    # Regex patterns to exclude
      - "\\[meta\\]"
      - "hiring"
```

## Signal Processing

Configure how signals are processed:

```yaml
signal_processing:
  engagement_threshold: 100    # Minimum engagement for trend detection
  trend_window_hours: 168      # 7 days for trend calculation
  duplicate_detection: true    # Remove duplicate content
```

## Troubleshooting

### Common Issues

1. **Invalid YAML syntax**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('sources/your-source.yaml'))"
   ```

2. **API authentication failures**:
   - Check environment variables are set
   - Verify API key permissions
   - Test endpoint manually with curl

3. **No data returned**:
   - Check API endpoint URL
   - Verify query parameters
   - Look for rate limiting responses

### Debug Mode

Run fetching in debug mode to see detailed logs:

```bash
python scripts/fetch_sources.py --debug --source your-source-id
```

## Advanced Configuration

For complex sources, you can add custom processing logic:

```yaml
config:
  custom_processing:
    extract_metadata: true
    normalize_scores: true
    filter_duplicates: true
  webhooks:
    on_high_engagement: "https://hooks.example.com/radar"
```

See the source code in `radar/adapters/fetchers/` for implementation details.
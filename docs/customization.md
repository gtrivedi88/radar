# Customization

Radar is designed to be adapted to your specific beat, voice, and decision-making style. This guide covers how to customize the system for different domains and personalities.

## Beat Customization

### Defining Your Beat

Edit `state/profile.md` to define your expertise areas:

```markdown
## Beat (what I write/teach about)
- AI-for-tech-writers craft and workflow
- Claude Code .md-driven development  
- AI tool stacks for non-coders
- Tech writer career evolution under AI
- Predictive intelligence for technical creators
- Elite productivity systems
```

### Beat-Specific Sources

Add sources that match your domain in the `sources/` directory. Examples:

**For DevOps/Infrastructure:**
```yaml
id: devops-weekly
name: "DevOps Weekly Newsletter"
type: rss
config:
  endpoint: "https://www.devopsweekly.com/rss.xml"
audience_tags: ["devops", "infrastructure"]
```

**For AI/ML Research:**
```yaml
id: arxiv-ai
name: "ArXiv AI Papers"
type: json_api
config:
  endpoint: "http://export.arxiv.org/api/query"
  query_params:
    search_query: "cat:cs.AI"
    max_results: 50
audience_tags: ["ai_research", "hardcore_tech"]
```

**For Product Management:**
```yaml
id: product-hunt
name: "Product Hunt API"
type: json_api
config:
  endpoint: "https://api.producthunt.com/v2/posts"
  headers:
    Authorization: "Bearer ${PRODUCT_HUNT_TOKEN}"
audience_tags: ["product", "startup"]
```

## Voice Customization

### Voice DNA

Define your communication style in `state/profile.md`:

```markdown
## Voice DNA
- cinematic, visceral, confrontational, philosophical  # Gaurav's style
- analytical, data-driven, cautious, systematic       # Alternative style
- conversational, practical, example-heavy, beginner-friendly  # Teaching style
```

### Voice Constraints

Set specific writing rules:

```markdown
## Voice constraints
- no em dashes, no AI transitions, no third-person hypotheticals  # Gaurav's rules
- oxford commas required, active voice preferred, max 20 words/sentence  # Editorial style
- always include code examples, avoid marketing speak, cite sources  # Technical style
```

## Psychology Calibration

### Decision-Making Style

Customize threshold detection to match how you make decisions:

**For Conservative Decision-Makers:**
```python
# In .claude/hooks/strategic_threshold_monitor.py
# Raise thresholds for more confident signals
if score > 2000:  # Higher threshold
    high_engagement.append(item)

# Require more evidence for framework discussions
if any(keyword in title for keyword in framework_keywords) and score > 1000:  # Higher bar
    framework_discussions.append(item)
```

**For Aggressive Early Adopters:**
```python
# Lower thresholds for faster signal detection
if score > 500:  # Lower threshold
    high_engagement.append(item)

# React to smaller signals
if any(keyword in title for keyword in framework_keywords) and score > 200:
    framework_discussions.append(item)
```

### Risk Tolerance

Adjust effort estimates and timelines:

**High Risk Tolerance (move fast):**
```python
def trigger_deep_research(item):
    return {
        "action": "deep_research",
        "timeline": "Ship by tomorrow",  # Aggressive timeline
        "effort": "2 hours",  # Quick turnaround
        "confidence": "medium"  # Accept uncertainty
    }
```

**Low Risk Tolerance (careful validation):**
```python
def trigger_deep_research(item):
    return {
        "action": "deep_research", 
        "timeline": "Research for 2 weeks, then decide",  # Extended timeline
        "effort": "8 hours over 3 sessions",  # Thorough research
        "confidence": "high"  # Require high confidence
    }
```

## Audience Customization

### Audience Definitions

Define your target audiences and tailor content accordingly:

```markdown
## Audiences served
- tech_writer: Technical writers and documentarians
- devs_curious_ai: Developers interested in AI tools
- hardcore_tech: Deep technical audience (systems, architecture)
- product_managers: PM audience for tool/process content
- startup_founders: Entrepreneur audience for business applications
```

### Audience-Specific Filtering

Customize source filtering by audience:

```yaml
# In source configurations
audience_tags: ["tech_writer", "devs_curious_ai"]  # Target specific audiences

# Advanced filtering
audience_filters:
  tech_writer:
    keywords: ["documentation", "technical writing", "docs", "markdown"]
    exclude_keywords: ["enterprise sales", "marketing"]
  hardcore_tech:
    keywords: ["architecture", "performance", "systems", "infrastructure"]  
    min_technical_depth: 8
```

## Synthesis Customization

### Digest Structure

Modify the digest sections in the `/radar` skill to match your needs:

**For Technical Audiences:**
```markdown
## 1 Technical Trends (↑/↓/→)
## 2 Architecture Patterns to Watch
## 3 Performance/Security Signals  
## 4 Tool Ecosystem Changes
## 5 Open Source Project Activity
```

**For Business/Product Audiences:**
```markdown
## 1 Market Movements (↑/↓/→)
## 2 User Behavior Shifts
## 3 Competitive Intelligence
## 4 Product Launch Patterns
## 5 Revenue/Growth Signals
```

### Quality Thresholds

Adjust quality gates to match your standards:

```python
# In synthesis logic
QUALITY_THRESHOLDS = {
    "min_source_count": 3,        # Require multiple sources
    "min_engagement": 100,        # Minimum engagement threshold
    "trend_confidence": 0.7,      # Confidence level for trend detection
    "max_digest_length": 2000     # Word count cap
}
```

## Autonomous Feature Customization

### Loop Frequency

Adjust autonomous loop timing based on your workflow:

**High-Frequency Monitoring (Day Trader Style):**
```javascript
CronCreate({
  cron: "0 */2 * * *",  // Every 2 hours
  prompt: "Quick signal check for urgent opportunities...",
})
```

**Low-Frequency Deep Analysis (Warren Buffett Style):**
```javascript  
CronCreate({
  cron: "0 9 * * 1",  // Weekly Monday morning
  prompt: "Weekly deep strategic analysis...",
})
```

### Custom Threshold Types

Add domain-specific thresholds:

**For Security/DevOps Beat:**
```python
def check_security_alerts(items):
    security_keywords = ["vulnerability", "CVE", "security", "breach"]
    critical_items = []
    
    for item in items:
        if any(keyword in item.title.lower() for keyword in security_keywords):
            if item.score > 300:  # Lower threshold for security
                critical_items.append(item)
    
    return critical_items
```

**For Startup/Business Beat:**
```python  
def check_funding_signals(items):
    funding_keywords = ["funding", "series A", "acquisition", "IPO", "valuation"]
    
    for item in items:
        if any(keyword in item.title.lower() for keyword in funding_keywords):
            if item.score > 200:
                return analyze_funding_trend(item)
```

## Intelligence Depth Customization

### Surface-Level Monitoring
```python
ANALYSIS_DEPTH = {
    "trend_analysis": "basic",      # Simple up/down/flat
    "prediction_horizon": "1week",  # Short-term focus  
    "research_depth": "headlines",  # Quick overview only
    "synthesis_complexity": "low"   # Simple summaries
}
```

### Deep Strategic Intelligence
```python
ANALYSIS_DEPTH = {
    "trend_analysis": "comprehensive",  # Multi-factor analysis
    "prediction_horizon": "6months",   # Long-term strategic  
    "research_depth": "full_context",  # Deep investigation
    "synthesis_complexity": "high"     # Complex correlations
}
```

## Domain-Specific Examples

### For Technical Writers

```yaml
# Custom source for writing-specific signals
id: technical-writing-today
name: "Technical Writing Today"
type: rss
config:
  endpoint: "https://technicalwritingtoday.com/feed"
signal_processing:
  boost_keywords: ["documentation", "API docs", "developer experience"]
  audience_tags: ["tech_writer"]
```

### For AI Researchers  

```yaml
# Papers and research signals
id: ai-research-trends
name: "AI Research Trends"  
type: json_api
config:
  endpoint: "https://api.semanticscholar.org/graph/v1/paper/search"
  query_params:
    query: "artificial intelligence"
    fields: "title,authors,venue,year,citationCount"
signal_processing:
  min_citation_count: 50
  audience_tags: ["ai_research", "hardcore_tech"]
```

### For Product Managers

```yaml
# Product management community signals
id: product-management-signals
name: "Product Management Community"
type: scrape
config:
  endpoint: "https://www.productmanagementhq.com/trending"
  selectors:
    title: "h2.post-title"
    engagement: ".vote-count"
signal_processing:
  boost_keywords: ["user research", "product strategy", "roadmap"]
  audience_tags: ["product_managers"]
```

## Testing Customizations

### Source Testing
```bash
python scripts/test_source.py sources/your-custom-source.yaml
```

### Threshold Testing  
```bash
python .claude/hooks/strategic_threshold_monitor.py
```

### End-to-End Testing
```bash
# Fetch data
python scripts/fetch_sources.py

# Test synthesis
claude --exec "/radar"
```

This customization system allows Radar to adapt to any beat, voice, or decision-making style while maintaining the core intelligence capabilities.
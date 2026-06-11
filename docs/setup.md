# Setup Guide

This guide walks you through setting up Radar from scratch.

## Prerequisites

### Required
- **Python 3.8+** - For fetching and data processing
- **Claude Code** - For intelligence synthesis (install from [claude.ai/code](https://claude.ai/code))
- **Git** - For version control and updates

### Optional but Recommended
- **Python virtual environment** - Isolates dependencies
- **API keys** - For premium sources (Hacker News, GitHub, etc.)

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/radar.git
cd radar

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Profile

Edit `state/profile.md` to define your identity and beat:

```bash
cp state/profile.md.example state/profile.md
```

Update these key sections:
- **Identity**: Name, role, audiences you serve
- **Beat**: What you write/teach about
- **Voice DNA**: Your communication style
- **Topics done/bored of**: What to avoid suggesting

### 3. Configure Intelligence Sources

Start with the basic sources:

```bash
# Copy example configurations
cp sources/hn-algolia.yaml.example sources/hn-algolia.yaml
cp sources/anthropic-blog.yaml.example sources/anthropic-blog.yaml

# Edit as needed - most work out of the box
```

Optional: Add API keys for enhanced sources:

```bash
# Create .env file for sensitive data
echo "GITHUB_TOKEN=your_token_here" >> .env
echo "HACKERNEWS_API_KEY=your_key_here" >> .env
```

### 4. Initialize State Files

```bash
# Create empty state files
mkdir -p state/archive
touch state/catalog.md state/trajectory.md state/feedback.md
echo '{}' > state/signals.jsonl
```

### 5. Test the System

```bash
# Test source fetching
python scripts/fetch_sources.py --source hn-algolia

# Check for data
ls raw/$(date +%Y-%m-%d)/

# Test synthesis (in Claude Code)
claude
/radar
```

## Configuration

### Profile Setup

Your `state/profile.md` drives all intelligence. Key sections:

```markdown
## Beat (what I write/teach about)
- AI-for-tech-writers craft and workflow
- Claude Code .md-driven development
- AI tool stacks for non-coders
- Tech writer career evolution under AI

## Voice DNA  
cinematic, visceral, confrontational, philosophical

## Topics done / bored of
- Generic "AI will replace writers" takes
- Tool-roundup posts without opinion
- Surface-level AI integration guides
```

### Source Selection

Choose sources that match your beat:

**For Technical Writers:**
- Technical Writing Weekly (RSS)
- Write the Docs forums (scrape)
- Documentation tools (GitHub)

**For AI Researchers:**
- ArXiv AI papers (API)
- AI/ML conference proceedings (RSS)
- Research Twitter accounts (scrape)

**For Developers:**
- Hacker News (API) ✅ Included
- GitHub trending (API)
- Dev community forums (scrape)

See [Adding Sources](adding-sources.md) for detailed configuration.

## Autonomous Features Setup

### Strategic Hooks (Real-time Monitoring)

Strategic hooks automatically check for threshold-triggered opportunities:

```bash
# The hooks are configured in .claude/settings.json
# They run automatically when Claude Code starts
# No additional setup needed
```

### Autonomous Loops (Scheduled Analysis)

Set up scheduled analysis loops:

```bash
# In Claude Code, create autonomous loops:
claude
```

```javascript
// Every 6 hours - intelligence analysis
CronCreate({
  cron: "47 */6 * * *",
  prompt: "Use Gaurav intelligence analysis on latest signals. Check for HTML-first development trend strengthening (>1000 total engagement), Claude performance pain points amplifying (>3 complaints), or new contrarian technical signals. If any threshold met, provide specific action recommendation with timeline.",
  recurring: true,
  durable: true
})

// Weekly Monday - contrarian signal hunt  
CronCreate({
  cron: "23 9 * * 1", 
  prompt: "Weekly contrarian signal hunt: Analyze past week's intelligence for signals that contradict mainstream developer consensus. Apply Gaurav intelligence analysis - provide specific post recommendations with 'Ship by Friday' urgency if contrarian angle + strong evidence detected.",
  recurring: true,
  durable: true
})
```

## Usage Workflow

### Daily Workflow

1. **Morning**: Claude Code automatically checks thresholds on startup
2. **Throughout day**: Sources auto-fetch based on their schedules
3. **When threshold hits**: Get immediate specific action recommendations

### Bi-weekly Workflow

1. **Fetch latest intelligence**:
   ```bash
   python scripts/fetch_sources.py
   ```

2. **Generate digest** (in Claude Code):
   ```
   /radar
   ```

3. **Process recommendations**:
   - Mark items as Doing/Pass/Done/Watch
   - Update trajectory.md with new projects
   - Update catalog.md with published work

### Weekly Maintenance

1. **Review trajectory.md**:
   - Move completed items to "Finished"
   - Add new items to "Queued"

2. **Clean up state**:
   ```bash
   # Remove old fetch errors
   rm state/fetch-errors.jsonl
   
   # Archive old threshold alerts
   mv state/threshold_alerts.jsonl state/archive/alerts-$(date +%Y-%m-%d).jsonl
   ```

## Customization

### Adjust to Your Beat

1. **Update sources**: Add domain-specific intelligence sources
2. **Tune thresholds**: Modify engagement thresholds in `.claude/hooks/strategic_threshold_monitor.py`
3. **Customize synthesis**: Edit digest structure in the radar skill

### Adjust to Your Psychology

1. **Decision speed**: Higher thresholds = more conservative, lower = more aggressive
2. **Risk tolerance**: Adjust effort estimates and timelines
3. **Voice**: Update voice constraints in profile.md

See [Customization Guide](customization.md) for detailed instructions.

## Troubleshooting

### Common Issues

**No data fetched:**
```bash
# Check source configuration
python scripts/test_source.py sources/hn-algolia.yaml

# Check for errors
tail -f state/fetch-errors.jsonl
```

**Claude synthesis fails:**
- Ensure Claude Code is installed and authenticated
- Check `/radar` skill is available: `/skills` in Claude
- Verify state files exist and are readable

**Autonomous features not working:**
- Check `.claude/settings.json` for hook configuration
- Verify cron jobs: `claude --list-cron` 
- Check threshold logs: `cat state/threshold_alerts.jsonl`

**Sources returning errors:**
- Check API keys in .env file
- Verify endpoint URLs are still valid
- Check rate limits aren't exceeded

### Debug Mode

Run with detailed logging:

```bash
# Debug source fetching
python scripts/fetch_sources.py --debug

# Test threshold monitoring
python .claude/hooks/strategic_threshold_monitor.py

# Check hook execution
tail -f state/hook_errors.jsonl
```

### Getting Help

1. Check existing [issues on GitHub](https://github.com/yourusername/radar/issues)
2. Read the [full documentation](../README.md)
3. Share your configuration (sanitized) when asking for help

## Next Steps

Once setup is complete:

1. **Run for a week** - Let it collect data and learn your patterns
2. **Tune thresholds** - Adjust based on signal quality
3. **Add more sources** - Expand to additional intelligence feeds  
4. **Customize synthesis** - Adapt digest structure to your needs
5. **Share feedback** - Help improve the system for others

## Security Notes

- **Never commit API keys** - Use .env files (in .gitignore)
- **Sanitize logs** - Remove sensitive data from error logs
- **Respect rate limits** - Configure appropriate fetching frequencies
- **Review permissions** - Claude Code hooks run with your user permissions

Your Radar system is now ready for autonomous strategic intelligence!
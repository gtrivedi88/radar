# Contributing to Radar

Thank you for your interest in contributing to Radar! This document outlines how to contribute to this personal intelligence system.

## Philosophy

Radar follows a simple principle: **Python does dumb deterministic fetching, Claude does all the judgment and synthesis.**

When contributing, keep this separation:
- **Python code**: Simple, reliable data fetching and storage
- **Claude skills**: Intelligence analysis, synthesis, and decision-making
- **Configuration**: YAML-based, no code changes for new sources

## Ways to Contribute

### 1. Adding Intelligence Sources

The easiest way to contribute is by adding new intelligence sources that others can use.

**What makes a good source:**
- Provides high-signal data relevant to technical creators
- Has reliable API or RSS feed
- Includes engagement metrics (upvotes, comments, shares)
- Updates frequently enough to catch trends

**How to add a source:**
1. Create a YAML file in `sources/`
2. Follow the format in [docs/adding-sources.md](docs/adding-sources.md)
3. Test with `python scripts/test_source.py sources/your-source.yaml`
4. Submit a pull request

**Example sources we'd love:**
- GitHub trending repositories with engagement metrics
- Technical conference CFP deadlines
- Developer job market signals  
- Technical blog aggregators
- Community discussion platforms (Discord, Slack exports)

### 2. Improving Fetching Infrastructure

**Areas for improvement:**
- Better error handling and retry logic
- Rate limiting improvements
- Support for new source types (GraphQL, WebSockets)
- Data quality filtering
- Deduplication across sources

**Guidelines:**
- Keep Python code simple and focused
- Add comprehensive error handling
- Include unit tests for new fetching logic
- Document new source types in `docs/adding-sources.md`

### 3. Enhancing Autonomous Features

**Autonomous intelligence improvements:**
- New threshold detection algorithms
- Better signal correlation across sources
- Enhanced prediction accuracy tracking
- More sophisticated trend analysis

**Guidelines:**
- Threshold logic should be psychology-agnostic (configurable)
- Include A/B testing for new algorithms
- Document customization options
- Preserve the real-time nature of threshold detection

### 4. Documentation and Examples

**Areas needing help:**
- More source configuration examples
- Beat-specific customization guides
- Video tutorials for setup
- Case studies of different use cases

**Guidelines:**
- Keep examples practical and tested
- Include both simple and advanced configurations
- Focus on different personas (researchers, writers, developers)

## Development Setup

### Prerequisites
- Python 3.8+
- Claude Code CLI
- Git

### Setup Steps
1. **Fork and clone:**
   ```bash
   git clone https://github.com/yourusername/radar.git
   cd radar
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure test sources:**
   ```bash
   cp sources/hn-algolia.yaml.example sources/hn-algolia.yaml
   # Edit with your test configuration
   ```

4. **Test the system:**
   ```bash
   python scripts/fetch_sources.py --source hn-algolia
   claude --exec "/radar"
   ```

### Testing

**Before submitting:**
1. **Test your source configuration:**
   ```bash
   python scripts/test_source.py sources/your-source.yaml
   ```

2. **Run fetching tests:**
   ```bash
   python -m pytest tests/test_fetchers.py
   ```

3. **Test end-to-end flow:**
   ```bash
   python scripts/fetch_sources.py
   claude --exec "/radar"
   ```

4. **Check for errors:**
   ```bash
   tail -f state/fetch-errors.jsonl
   ```

## Contribution Guidelines

### Code Style

**Python:**
- Follow PEP 8
- Use type hints for function signatures
- Include docstrings for public functions
- Keep functions focused and simple

**YAML configurations:**
- Use consistent indentation (2 spaces)
- Include comments for complex configurations
- Validate with `yamllint`

**Documentation:**
- Write for your past self 6 months ago
- Include working examples
- Test all code snippets

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/add-github-trending-source
   ```

2. **Make your changes:**
   - Add/modify source configurations
   - Update documentation
   - Add tests if needed

3. **Test thoroughly:**
   - Run all existing tests
   - Test your new source/feature
   - Verify documentation examples work

4. **Submit pull request:**
   - Clear title describing the change
   - Description of what problem it solves
   - Include example output if adding a source
   - Reference any related issues

### Source Quality Standards

**Data Quality:**
- Must include engagement metrics (votes, comments, shares)
- Should filter out low-quality content
- Must handle API failures gracefully
- Should respect rate limits

**Configuration Quality:**
- Clear, descriptive names and descriptions
- Appropriate audience tags
- Reasonable update frequencies
- Working example queries

**Documentation:**
- Include setup instructions
- Document any required API keys
- Provide example output
- Explain signal types provided

## Issue Guidelines

### Reporting Bugs

**Include:**
- Python and Claude Code versions
- Source configuration (sanitized)
- Error logs from `state/fetch-errors.jsonl`
- Steps to reproduce
- Expected vs actual behavior

### Requesting Features

**Good feature requests:**
- Clearly describe the use case
- Explain why existing features don't work
- Provide examples of the desired behavior
- Consider backwards compatibility

### Source Requests

**When requesting new sources:**
- Explain why this source provides unique intelligence
- Include links to the API documentation
- Mention if you're willing to help implement
- Describe the target audience

## Architecture Decisions

When making significant changes, consider:

### Separation of Concerns
- Keep Python simple and deterministic
- Put intelligence/judgment in Claude skills
- Use configuration over code when possible

### Backwards Compatibility
- Don't break existing source configurations
- Maintain state file formats
- Deprecate features gracefully

### Performance
- Sources should handle hundreds of items efficiently
- Minimize API calls through caching
- Don't block the synthesis process

### Privacy
- Never log API keys or personal data
- Sanitize URLs in error logs
- Respect robots.txt and terms of service

## Community

### Code of Conduct

- Be respectful and constructive
- Help newcomers understand the system
- Focus on improving the intelligence quality
- Share knowledge about good sources and configurations

### Getting Help

- Check existing issues first
- Include enough detail for others to help
- Test your setup before asking for help
- Share your source configurations (sanitized)

## Recognition

Contributors will be:
- Listed in the README
- Mentioned in release notes for significant contributions
- Given credit in source configuration comments

## Release Process

**For maintainers:**

1. **Version bumping:**
   - Update version in `setup.py`
   - Update CHANGELOG.md
   - Tag the release

2. **Release notes:**
   - Highlight new sources
   - Document breaking changes
   - Credit contributors

3. **Testing:**
   - Test with fresh installation
   - Verify example configurations work
   - Test autonomous features

Thank you for helping make Radar a better intelligence system!
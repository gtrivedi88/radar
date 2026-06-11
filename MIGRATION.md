# Migration Guide: Scripts → Radar Engine

## Overview

The Radar project has migrated from simple script-based fetching to a sophisticated autonomous intelligence engine. This document guides you through the migration process.

## What Changed

### Old Approach (Deprecated)
```bash
# This is now deprecated
python scripts/fetch_sources.py
```

### New Approach (Recommended)
```bash
# Use the radar-engine instead
python -m radar-engine run
```

## Migration Steps

### 1. Update Your Workflows

**Before:**
```bash
# Old cron job or manual execution
python scripts/fetch_sources.py
```

**After:**
```bash
# New autonomous intelligence execution
python -m radar-engine run
```

### 2. Configuration Compatibility

Your existing source configurations in `sources/*.yaml` remain fully compatible. No changes needed to:
- `sources/hn-algolia.yaml`
- `sources/anthropic-blog.yaml`
- Any custom source configurations

### 3. Output Format Changes

**Old format:** Raw JSON files in `raw/YYYY-MM-DD/{source}.json`
**New format:** Same raw data PLUS autonomous intelligence processing

The radar-engine produces the same raw data files but also:
- Processes intelligence through autonomous hooks
- Triggers threshold-based actions
- Maintains state across runs
- Logs to `state/threshold_alerts.jsonl`

### 4. State Management

The new system adds persistent state files:
- `state/autonomous-loops.json` - Scheduled intelligence loops
- `state/threshold_alerts.jsonl` - Hook trigger history
- `state/hook_errors.jsonl` - Error logging

These are created automatically - no manual setup required.

## Benefits of Migration

### Autonomous Intelligence
- Real-time threshold monitoring via SessionStart hooks
- Scheduled intelligence loops with frequency control
- Strategic hook system for opportunity detection

### Reliability Improvements
- Better error handling and recovery
- Structured logging for debugging
- State persistence across runs

### Future-Ready
- Container deployment support
- OpenClaw cloud migration path
- Integration with Claude Code synthesis

## Backward Compatibility

### Migration Complete
The old `scripts/fetch_sources.py` has been removed. Use `python -m radar-engine` instead.

### Data Compatibility
All existing data in `raw/` and `state/` directories remains compatible with the new system.

## Testing the Migration

### Migration Verification
```bash
# Old approach (removed)
# python scripts/fetch_sources.py  # No longer exists
```

### Test New Engine
```bash
python -m radar-engine run
# Should execute complete intelligence cycle
```

### Compare Outputs
Both approaches should produce similar raw data files in `raw/YYYY-MM-DD/`.

## Timeline

- **Now:** Both systems work, deprecation warnings shown
- **Next release:** Old script will be removed
- **Migration deadline:** Update your workflows before next major release

## Getting Help

If you encounter issues during migration:
1. Check that `requirements.lock` dependencies are installed
2. Verify source configurations in `sources/` are valid
3. Run tests: `python -m pytest tests/ -v`
4. Check for error logs in `state/hook_errors.jsonl`

## Advanced Features

The new radar-engine includes advanced capabilities not available in the old script:

### Autonomous Loops
```bash
# Set up scheduled intelligence loops
python -m radar-engine setup-loops
```

### Continuous Mode
```bash
# Run autonomous intelligence continuously
python -m radar-engine continuous
```

### Health Monitoring
```bash
# Check system health (when implemented)
python -m radar-engine health-check
```

These features require the new radar-engine and are not available in the deprecated script approach.
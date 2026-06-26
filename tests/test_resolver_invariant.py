# tests/test_resolver_invariant.py
from radar_memory.resolver import Proposal, resolve_theme


def test_renamed_theme_collapses_to_one_id_across_two_cycles():
    registry = {}
    # Cycle 1: theme first appears under one name.
    resolve_theme(Proposal("2026-06-11", "ai_cost_pain", "NEW",
                           3, ["hn"], 245, "surfaced", "first"), registry)
    # Cycle 2: SAME theme, deliberately renamed, and Claude wrongly says NEW.
    resolve_theme(Proposal("2026-06-19", "llm_billing_shock", "ai_cost_pain",
                           5, ["devto"], 300, "surfaced", "again"), registry)
    assert len(registry) == 1, "renamed theme must not create a second entry"
    entry = next(iter(registry.values()))
    assert entry.theme_id == "ai_cost_pain"
    assert entry.cycle_count == 2
    assert "llm_billing_shock" in entry.aliases

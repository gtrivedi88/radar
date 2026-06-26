# tests/test_resolver.py
from radar_memory.registry import RegistryEntry
from radar_memory.resolver import Proposal, resolve_theme


def _entry(theme_id, canonical, aliases, cc):
    return RegistryEntry(theme_id, canonical, list(aliases), "2026-06-11", "2026-06-11", cc)


def test_exact_match_bumps_cycle_count():
    reg = {"html_first": _entry("html_first", "html_first", [], 2)}
    p = Proposal("2026-06-19", "html_first", "NEW", 3, ["hn"], 1545, "surfaced", "x")
    audit = resolve_theme(p, reg)
    assert audit.method == "exact"
    assert audit.chosen_theme_id == "html_first"
    assert reg["html_first"].cycle_count == 3
    assert reg["html_first"].last_seen == "2026-06-19"


def test_alias_match_overrides_wrong_new():
    reg = {"html_first": _entry("html_first", "html first development",
                                ["html_first_development_fading"], 2)}
    p = Proposal("2026-06-19", "html_first_development_fading", "NEW",
                 0, [], 0, "banked", "decayed")
    audit = resolve_theme(p, reg)
    assert audit.method == "alias"
    assert audit.chosen_theme_id == "html_first"
    assert reg["html_first"].cycle_count == 3


def test_claude_match_records_new_alias():
    reg = {"ai_cost_pain": _entry("ai_cost_pain", "ai cost pain", [], 1)}
    p = Proposal("2026-06-19", "llm_billing_shock", "ai_cost_pain",
                 5, ["devto"], 300, "surfaced", "bills exploding")
    audit = resolve_theme(p, reg)
    assert audit.method == "claude"
    assert audit.chosen_theme_id == "ai_cost_pain"
    assert "llm_billing_shock" in reg["ai_cost_pain"].aliases
    assert reg["ai_cost_pain"].cycle_count == 2


def test_new_theme_is_minted():
    reg = {}
    p = Proposal("2026-06-19", "Sovereign AI debate", "NEW",
                 2, ["verge"], 200, "watching", "india")
    audit = resolve_theme(p, reg)
    assert audit.method == "new"
    assert audit.chosen_theme_id == "sovereign_ai_debate"
    assert reg["sovereign_ai_debate"].cycle_count == 1
    assert reg["sovereign_ai_debate"].first_seen == "2026-06-19"

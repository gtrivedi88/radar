from radar_memory.migrate import build_registry, rekey_bank


def _bank():
    return [
        {"date": "2026-06-11", "theme": "html_first_development", "cycle_count": 1,
         "engagement_total": 1545},
        {"date": "2026-06-19", "theme": "html_first_development", "cycle_count": 2,
         "engagement_total": 0},
        {"date": "2026-06-19", "theme": "ai_cost_reliability_pain", "cycle_count": 1,
         "engagement_total": 245},
    ]


def test_build_registry_one_entry_per_distinct_theme():
    reg = build_registry(_bank())
    assert set(reg) == {"html_first_development", "ai_cost_reliability_pain"}
    hf = reg["html_first_development"]
    assert hf.cycle_count == 2
    assert hf.first_seen == "2026-06-11"
    assert hf.last_seen == "2026-06-19"


def test_rekey_bank_adds_theme_id_without_dropping_fields():
    out = rekey_bank(_bank())
    assert out[0]["theme_id"] == "html_first_development"
    assert out[0]["engagement_total"] == 1545  # original field preserved
    assert all("theme_id" in e for e in out)

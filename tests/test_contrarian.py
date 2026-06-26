from radar_memory.registry import RegistryEntry
from radar_memory.contrarian import expected_but_quiet


def test_flags_strong_prior_themes_absent_this_cycle():
    registry = {
        "html_first": RegistryEntry("html_first", "html first", [], "2026-05-28", "2026-06-11", 3),
        "weak_theme": RegistryEntry("weak_theme", "weak", [], "2026-06-11", "2026-06-11", 1),
        "present_theme": RegistryEntry("present_theme", "present", [], "2026-06-11", "2026-06-19", 4),
    }
    bank = [
        {"theme_id": "html_first", "engagement_total": 1545},
        {"theme_id": "weak_theme", "engagement_total": 50},
        {"theme_id": "present_theme", "engagement_total": 900},
    ]
    present = {"present_theme"}
    flagged = expected_but_quiet(registry, present, bank)
    ids = [f["theme_id"] for f in flagged]
    assert ids == ["html_first"]  # strong prior + absent; weak excluded; present excluded
    assert flagged[0]["peak_engagement"] == 1545

from pathlib import Path
from radar_memory.registry import (
    slugify, RegistryEntry, load_registry, save_registry, mint_theme_id,
)


def test_slugify_normalizes():
    assert slugify("HTML-first Development!") == "html_first_development"
    assert slugify("AI  cost/reliability  pain") == "ai_cost_reliability_pain"


def test_mint_theme_id_collision_suffix():
    reg = {"ai_cost": RegistryEntry("ai_cost", "ai cost", [], "2026-06-01", "2026-06-01", 1)}
    assert mint_theme_id("AI cost", reg) == "ai_cost-2"
    assert mint_theme_id("brand new theme", reg) == "brand_new_theme"


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "theme-registry.jsonl"
    reg = {
        "html_first": RegistryEntry(
            "html_first", "html first development",
            ["html_first_development_fading"], "2026-06-11", "2026-06-19", 2,
        )
    }
    save_registry(path, reg)
    assert not path.with_name(path.name + ".tmp").exists()  # atomic write leaves no temp
    loaded = load_registry(path)
    assert loaded == reg


def test_load_missing_file_is_empty(tmp_path):
    assert load_registry(tmp_path / "nope.jsonl") == {}

"""Expected-but-quiet detector: strong prior themes that produced zero items this cycle."""


def _peak_engagement(theme_id: str, bank_entries: list) -> int:
    vals = [e.get("engagement_total", 0) for e in bank_entries if e.get("theme_id") == theme_id]
    return max(vals) if vals else 0


def expected_but_quiet(registry: dict, present_theme_ids: set, bank_entries: list,
                       min_cycle_count: int = 2, min_peak_engagement: int = 500) -> list:
    flagged = []
    for entry in registry.values():
        if entry.theme_id in present_theme_ids:
            continue
        if entry.cycle_count < min_cycle_count:
            continue
        peak = _peak_engagement(entry.theme_id, bank_entries)
        if peak < min_peak_engagement:
            continue
        flagged.append({
            "theme_id": entry.theme_id,
            "canonical_name": entry.canonical_name,
            "cycle_count": entry.cycle_count,
            "peak_engagement": peak,
        })
    flagged.sort(key=lambda f: f["peak_engagement"], reverse=True)
    return flagged

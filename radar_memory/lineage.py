"""Render a theme's history across cycles, keyed on theme_id."""


def theme_lineage(theme_id: str, bank_entries: list) -> list:
    points = [e for e in bank_entries if e.get("theme_id") == theme_id]
    points.sort(key=lambda e: e.get("date", ""))
    return [
        {
            "date": e.get("date", ""),
            "engagement_total": e.get("engagement_total", 0),
            "source_count": e.get("source_count", 0),
            "status": e.get("status", ""),
        }
        for e in points
    ]

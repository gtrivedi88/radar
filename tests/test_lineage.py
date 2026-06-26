from radar_memory.lineage import theme_lineage


def test_lineage_is_chronological_and_filtered():
    bank = [
        {"date": "2026-06-19", "theme_id": "claude_perf", "engagement_total": 1333,
         "source_count": 3, "status": "surfaced"},
        {"date": "2026-06-11", "theme_id": "claude_perf", "engagement_total": 664,
         "source_count": 1, "status": "watching"},
        {"date": "2026-06-19", "theme_id": "other", "engagement_total": 10,
         "source_count": 1, "status": "banked"},
    ]
    line = theme_lineage("claude_perf", bank)
    assert [p["engagement_total"] for p in line] == [664, 1333]
    assert line[0]["status"] == "watching"

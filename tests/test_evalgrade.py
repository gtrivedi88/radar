from radar_memory.evalgrade import Prediction, grade_prediction, scorecard


def _pred():
    return Prediction("2026-06-05", "ai_cost_pain", "Write cost-forensics post", "pending")


def test_outcome_beats_momentum():
    assert grade_prediction(_pred(), later_entries=[], shipped=True, acted=False,
                            elapsed_cycles=3) == "shipped"
    assert grade_prediction(_pred(), later_entries=[], shipped=False, acted=True,
                            elapsed_cycles=3) == "acted"


def test_pending_when_too_early():
    assert grade_prediction(_pred(), later_entries=[], shipped=False, acted=False,
                            elapsed_cycles=1, min_followups=2) == "pending"


def test_sustained_vs_fizzled():
    climbing = [
        {"date": "2026-06-12", "source_count": 3, "cycle_count": 2},
        {"date": "2026-06-19", "source_count": 4, "cycle_count": 3},
    ]
    assert grade_prediction(_pred(), climbing, False, False, elapsed_cycles=3) == "sustained"
    assert grade_prediction(_pred(), [], False, False, elapsed_cycles=3) == "fizzled"


def test_scorecard_string():
    labels = ["shipped", "acted", "sustained", "fizzled", "pending", "shipped"]
    assert scorecard(labels) == (
        "ACT NOW track record: 3 shipped/acted · 1 sustained-only · "
        "1 fizzled · 1 pending"
    )

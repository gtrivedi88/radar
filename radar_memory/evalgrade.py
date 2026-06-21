"""Grade past ACT NOW predictions against real outcomes. Outcome > momentum."""

from dataclasses import dataclass


@dataclass
class Prediction:
    date: str
    theme_id: str
    recommendation: str
    status: str  # "pending" until graded


def grade_prediction(pred: Prediction, later_entries: list, shipped: bool, acted: bool,
                     elapsed_cycles: int, min_followups: int = 2) -> str:
    if shipped:
        return "shipped"
    if acted:
        return "acted"
    if elapsed_cycles < min_followups:
        return "pending"
    distinct_cycles = {e.get("date") for e in later_entries}
    multi_source = any(e.get("source_count", 0) >= 2 for e in later_entries)
    if len(distinct_cycles) >= 2 and multi_source:
        return "sustained"
    return "fizzled"


def scorecard(labels: list) -> str:
    good = sum(1 for l in labels if l in ("shipped", "acted"))
    sustained = labels.count("sustained")
    fizzled = labels.count("fizzled")
    pending = labels.count("pending")
    return (f"ACT NOW track record: {good} shipped/acted · "
            f"{sustained} sustained-only · {fizzled} fizzled · {pending} pending")

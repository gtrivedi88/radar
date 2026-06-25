"""Thin CLI over the tested memory-layer functions. Python owns all deterministic writes."""

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from .registry import load_registry, save_registry
from .resolver import Proposal, resolve_theme
from .lineage import theme_lineage
from .contrarian import expected_but_quiet
from .evalgrade import Prediction, grade_prediction, scorecard

# Anchored to the repo, overridable for tests (see migrate.py for the rationale).
ROOT_DIR = Path(__file__).resolve().parent.parent
STATE = Path(os.environ.get("RADAR_STATE_DIR", ROOT_DIR / "state"))


def _read_jsonl(path: Path) -> list:
    """Tolerant reader: skip malformed lines (the LLM writes some of these files)."""
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"⚠️  Skipping malformed line {i} in {path.name}: {e}")
    return out


def _append_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def cmd_resolve() -> None:
    registry = load_registry(STATE / "theme-registry.jsonl")
    proposals_path = STATE / "theme-resolutions.jsonl"
    raw_proposals = _read_jsonl(proposals_path)

    audits, bank_lines, predictions = [], [], []
    for raw in raw_proposals:
        try:
            proposal = Proposal(**raw)
        except TypeError as e:  # missing/extra key from a malformed LLM proposal
            print(f"⚠️  Skipping malformed proposal {raw!r}: {e}")
            continue
        audit = resolve_theme(proposal, registry)      # mutates registry in place
        entry = registry[audit.chosen_theme_id]
        audits.append(audit)
        bank_lines.append({
            "date": proposal.date,
            "theme_id": entry.theme_id,
            "theme": proposal.surfaced_name,
            "source_count": proposal.source_count,
            "sources": proposal.sources,
            "engagement_total": proposal.engagement_total,
            "status": proposal.status,
            "cycle_count": entry.cycle_count,
            "first_seen": entry.first_seen,
            "evidence": proposal.evidence,
        })
        if proposal.act_now:
            predictions.append({
                "date": proposal.date,
                "theme_id": entry.theme_id,
                "recommendation": proposal.recommendation,
                "status": "pending",
            })

    # Commit deterministically: registry first (atomic), then append-only logs, then
    # CLEAR the consumed proposals so a re-run can't double-apply them (not idempotent).
    save_registry(STATE / "theme-registry.jsonl", registry)
    for audit in audits:
        _append_jsonl(STATE / "theme-resolution-log.jsonl", asdict(audit))
    for line in bank_lines:
        _append_jsonl(STATE / "signal-bank.jsonl", line)
    for pred in predictions:
        _append_jsonl(STATE / "act-now-predictions.jsonl", pred)
    proposals_path.write_text("", encoding="utf-8")

    print(f"Resolved {len(bank_lines)} themes "
          f"({len(predictions)} ACT NOW predictions); "
          f"registry now {len(registry)} themes. Proposals cleared.")


def cmd_eval() -> None:
    preds = []
    for p in _read_jsonl(STATE / "act-now-predictions.jsonl"):
        try:
            preds.append(Prediction(**p))
        except TypeError as e:  # missing/extra key from a malformed prediction
            print(f"⚠️  Skipping malformed prediction {p!r}: {e}")
    bank = _read_jsonl(STATE / "signal-bank.jsonl")
    catalog = (STATE / "catalog.md").read_text(encoding="utf-8") if (STATE / "catalog.md").exists() else ""
    feedback = (STATE / "feedback.md").read_text(encoding="utf-8") if (STATE / "feedback.md").exists() else ""
    registry = load_registry(STATE / "theme-registry.jsonl")
    dates = sorted({e.get("date", "") for e in bank})
    labels = []
    for pred in preds:
        later = [e for e in bank if e.get("theme_id") == pred.theme_id and e.get("date", "") > pred.date]
        elapsed = sum(1 for d in dates if d > pred.date)
        name = registry[pred.theme_id].canonical_name if pred.theme_id in registry else pred.theme_id
        shipped = name in catalog or pred.theme_id in catalog
        acted = (name in feedback or pred.theme_id in feedback)
        labels.append(grade_prediction(pred, later, shipped, acted, elapsed))
    print(scorecard(labels))


def cmd_contrarian() -> None:
    registry = load_registry(STATE / "theme-registry.jsonl")
    bank = _read_jsonl(STATE / "signal-bank.jsonl")
    if not bank:
        print("[]")
        return
    latest = max(e.get("date", "") for e in bank)
    present = {e.get("theme_id") for e in bank if e.get("date") == latest and e.get("theme_id")}
    flagged = expected_but_quiet(registry, present, bank)
    print(json.dumps(flagged, ensure_ascii=False, indent=2))


def cmd_lineage() -> None:
    bank = _read_jsonl(STATE / "signal-bank.jsonl")
    if not bank:
        print("(no signal bank yet)")
        return
    latest = max(e.get("date", "") for e in bank)
    seen = set()
    for e in bank:
        tid = e.get("theme_id")
        if not tid or e.get("date") != latest or tid in seen:
            continue
        seen.add(tid)
        chain = " → ".join(f"{p['engagement_total']} ({p['date']})" for p in theme_lineage(tid, bank))
        print(f"{tid}: {chain}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="radar_memory")
    parser.add_argument("command", choices=["resolve", "eval", "contrarian", "lineage"])
    args = parser.parse_args()
    {
        "resolve": cmd_resolve,
        "eval": cmd_eval,
        "contrarian": cmd_contrarian,
        "lineage": cmd_lineage,
    }[args.command]()


if __name__ == "__main__":
    main()

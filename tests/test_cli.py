import json
import os
import subprocess
import sys
from pathlib import Path


def test_resolve_subcommand_banks_logs_and_clears(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "theme-registry.jsonl").write_text(
        json.dumps({"theme_id": "ai_cost_pain", "canonical_name": "ai cost pain",
                    "aliases": [], "first_seen": "2026-06-11", "last_seen": "2026-06-11",
                    "cycle_count": 1}) + "\n", encoding="utf-8")
    (state / "theme-resolutions.jsonl").write_text(
        json.dumps({"date": "2026-06-19", "surfaced_name": "llm_billing_shock",
                    "proposed_theme_id": "ai_cost_pain", "source_count": 5,
                    "sources": ["devto"], "engagement_total": 300,
                    "status": "surfaced", "evidence": "bills",
                    "act_now": True, "recommendation": "Write cost-forensics post"}) + "\n",
        encoding="utf-8")
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "radar_memory", "resolve"],
        cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(repo_root), "RADAR_STATE_DIR": str(state)},
    )
    assert proc.returncode == 0, proc.stderr

    reg = [json.loads(l) for l in (state / "theme-registry.jsonl").read_text().splitlines()]
    assert reg[0]["cycle_count"] == 2
    assert "llm_billing_shock" in reg[0]["aliases"]

    bank = (state / "signal-bank.jsonl").read_text().splitlines()
    assert len(bank) == 1
    assert json.loads(bank[0])["theme_id"] == "ai_cost_pain"
    assert json.loads(bank[0])["cycle_count"] == 2  # Python wrote it, not the LLM

    preds = (state / "act-now-predictions.jsonl").read_text().splitlines()
    assert json.loads(preds[0])["recommendation"] == "Write cost-forensics post"

    assert (state / "theme-resolutions.jsonl").read_text() == ""  # consumed, won't re-apply
    assert "ai_cost_pain" in (state / "theme-resolution-log.jsonl").read_text()


def test_eval_tolerates_malformed_predictions(tmp_path):
    """Verify cmd_eval skips malformed predictions (missing/extra keys) and produces scorecard."""
    state = tmp_path / "state"
    state.mkdir()

    # Minimal registry
    (state / "theme-registry.jsonl").write_text(
        json.dumps({"theme_id": "test_id", "canonical_name": "test",
                    "aliases": [], "first_seen": "2026-06-01", "last_seen": "2026-06-01",
                    "cycle_count": 1}) + "\n", encoding="utf-8")

    # Valid prediction + malformed line (valid JSON but missing required keys)
    (state / "act-now-predictions.jsonl").write_text(
        json.dumps({"date": "2026-06-01", "theme_id": "test_id",
                    "recommendation": "test", "status": "pending"}) + "\n" +
        json.dumps({"oops": 1}) + "\n",  # malformed: missing required keys
        encoding="utf-8")

    # Minimal signal bank
    (state / "signal-bank.jsonl").write_text(
        json.dumps({"date": "2026-06-01", "theme_id": "test_id",
                    "theme": "test", "source_count": 1, "sources": [],
                    "engagement_total": 1, "status": "surfaced",
                    "cycle_count": 1, "first_seen": "2026-06-01", "evidence": ""}) + "\n",
        encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "radar_memory", "eval"],
        cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(repo_root), "RADAR_STATE_DIR": str(state)},
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert "ACT NOW track record:" in proc.stdout
    assert "⚠️  Skipping malformed prediction" in proc.stdout

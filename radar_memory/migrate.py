"""One-time migration: build the registry from signal-bank, re-key the bank on theme_id."""

import json
import os
from pathlib import Path

from .registry import RegistryEntry, slugify, save_registry

# Anchor to the repo (module location), not the caller's cwd, so the script can't
# create a rogue state/ folder when run from a subdirectory. Overridable for tests.
ROOT_DIR = Path(__file__).resolve().parent.parent
STATE = Path(os.environ.get("RADAR_STATE_DIR", ROOT_DIR / "state"))
BANK_PATH = STATE / "signal-bank.jsonl"
REGISTRY_PATH = STATE / "theme-registry.jsonl"


def _load_bank(path: Path) -> list:
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_registry(bank_entries: list) -> dict:
    registry = {}
    counts = {}
    for e in bank_entries:
        tid = slugify(e["theme"])
        counts[tid] = counts.get(tid, 0) + 1
        date = e.get("date", "")
        if tid not in registry:
            registry[tid] = RegistryEntry(
                theme_id=tid, canonical_name=e["theme"], aliases=[],
                first_seen=date, last_seen=date,
                cycle_count=e.get("cycle_count", 1),
            )
        else:
            entry = registry[tid]
            entry.first_seen = min(entry.first_seen, date) if entry.first_seen else date
            entry.last_seen = max(entry.last_seen, date)
            entry.cycle_count = max(entry.cycle_count, e.get("cycle_count", 1))
    for tid, n in counts.items():
        registry[tid].cycle_count = max(registry[tid].cycle_count, n)
    return registry


def rekey_bank(bank_entries: list) -> list:
    out = []
    for e in bank_entries:
        new = dict(e)
        new["theme_id"] = slugify(e["theme"])
        out.append(new)
    return out


def main() -> None:
    bank = _load_bank(BANK_PATH)
    if not bank:
        print("No signal-bank.jsonl to migrate.")
        return
    registry = build_registry(bank)
    save_registry(REGISTRY_PATH, registry)
    rekeyed = rekey_bank(bank)
    with open(BANK_PATH, "w", encoding="utf-8") as f:
        for e in rekeyed:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"Migrated {len(bank)} bank entries into {len(registry)} registry themes.")


if __name__ == "__main__":
    main()

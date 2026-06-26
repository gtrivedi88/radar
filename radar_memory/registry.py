"""Theme registry: the canonical identity store. Deterministic, no judgment."""

import json
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", s).strip("_")


@dataclass
class RegistryEntry:
    theme_id: str
    canonical_name: str
    aliases: list = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    cycle_count: int = 0


def load_registry(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {}
    registry = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            registry[d["theme_id"]] = RegistryEntry(**d)
    return registry


def save_registry(path: Path, registry: dict) -> None:
    # Atomic write: a kill mid-write must never corrupt the system of record.
    # with_name (not with_suffix) avoids any version-dependent suffix-parsing surprises.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        for entry in registry.values():
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    tmp_path.replace(path)  # atomic rename on POSIX


def mint_theme_id(canonical_name: str, registry: dict) -> str:
    base = slugify(canonical_name)
    if base not in registry:
        return base
    n = 2
    while f"{base}-{n}" in registry:
        n += 1
    return f"{base}-{n}"

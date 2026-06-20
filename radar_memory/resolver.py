"""Resolve a surfaced theme to a stable theme_id. Deterministic backstop + Claude's match."""

from dataclasses import dataclass, field

from .registry import RegistryEntry, mint_theme_id, slugify


@dataclass
class Proposal:
    date: str
    surfaced_name: str
    proposed_theme_id: str  # an existing id, "NEW", or None
    source_count: int
    sources: list
    engagement_total: int
    status: str
    evidence: str
    act_now: bool = False        # True only for the top ACT NOW items
    recommendation: str = ""     # the specific call; logged as a prediction when act_now


@dataclass
class AuditEntry:
    date: str
    surfaced_name: str
    chosen_theme_id: str
    method: str       # exact | alias | claude | new
    rationale: str


def _deterministic_match(surfaced_name: str, registry: dict):
    slug = slugify(surfaced_name)
    for entry in registry.values():
        if entry.theme_id == slug or slugify(entry.canonical_name) == slug:
            return entry, "exact"
    for entry in registry.values():
        if any(slugify(a) == slug for a in entry.aliases):
            return entry, "alias"
    return None, None


def _touch(entry: RegistryEntry, p: Proposal) -> None:
    entry.cycle_count += 1
    entry.last_seen = p.date
    surfaced = p.surfaced_name
    if surfaced != entry.canonical_name and surfaced not in entry.aliases:
        if slugify(surfaced) != slugify(entry.canonical_name):
            entry.aliases.append(surfaced)


def resolve_theme(proposal: Proposal, registry: dict) -> AuditEntry:
    entry, method = _deterministic_match(proposal.surfaced_name, registry)
    if entry is None and proposal.proposed_theme_id in registry:
        entry, method = registry[proposal.proposed_theme_id], "claude"
    if entry is not None:
        _touch(entry, proposal)
        return AuditEntry(proposal.date, proposal.surfaced_name,
                          entry.theme_id, method,
                          f"matched via {method}")
    theme_id = mint_theme_id(proposal.surfaced_name, registry)
    registry[theme_id] = RegistryEntry(
        theme_id=theme_id, canonical_name=proposal.surfaced_name,
        aliases=[], first_seen=proposal.date, last_seen=proposal.date, cycle_count=1,
    )
    return AuditEntry(proposal.date, proposal.surfaced_name, theme_id, "new", "minted")

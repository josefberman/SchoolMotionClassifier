"""Canonical behavior labels and alias resolution."""

from __future__ import annotations

import json
from pathlib import Path

# Stable schooling regimes plus signed-radial states (E+/E-).
STABLE_BEHAVIORS = (
    "traveling_polarized",
    "milling",
    "shoaling",
)

THREAT_BEHAVIORS = (
    "expansion_burst",
    "compaction",
)

CANONICAL = STABLE_BEHAVIORS + THREAT_BEHAVIORS

BEHAVIOR_SHORT = {
    "traveling_polarized": "tpol",
    "milling": "milling",
    "shoaling": "shoaling",
    "expansion_burst": "expansion",
    "compaction": "compaction",
    "fountain_evasion": "fountain",
}

TRANSITIONS = tuple(
    f"{a}_to_{b}" for a in CANONICAL for b in CANONICAL if a != b
)

ALL_LABELS = CANONICAL + TRANSITIONS


def is_transition(label: str) -> bool:
    return "_to_" in label


def is_baseline(label: str) -> bool:
    return label in CANONICAL


def is_threat(label: str) -> bool:
    return label in THREAT_BEHAVIORS


def is_stable(label: str) -> bool:
    return label in STABLE_BEHAVIORS


def label_set(*, include_transitions: bool, stable_only: bool = False) -> tuple[str, ...]:
    """Return allowed labels. stable_only / not include_transitions → baselines only (incl. e+/e−)."""
    if include_transitions and not stable_only:
        return ALL_LABELS
    return CANONICAL


_ROOT = Path(__file__).resolve().parents[1]
_ALIAS_PATH = _ROOT / "annotations" / "_label_aliases.json"


def load_aliases(path: Path | None = None) -> dict[str, str]:
    p = path or _ALIAS_PATH
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    return {k.lower(): v for k, v in raw.items()}


_SHORT_TO_CANONICAL = {v: k for k, v in BEHAVIOR_SHORT.items()}
_SHORT_TO_CANONICAL.update({
    "polarized": "traveling_polarized",
    "swarming": "shoaling",
})


def _resolve_transition(label: str, aliases: dict[str, str]) -> str | None:
    """Try to parse 'X to Y' / 'X_to_Y' into a canonical transition label."""
    for sep in (" to ", "_to_"):
        if sep in label.lower():
            parts = label.lower().split(sep, 1)
            if len(parts) == 2:
                a_raw, b_raw = parts[0].strip(), parts[1].strip()
                a = aliases.get(a_raw, _SHORT_TO_CANONICAL.get(a_raw, a_raw))
                b = aliases.get(b_raw, _SHORT_TO_CANONICAL.get(b_raw, b_raw))
                trans = f"{a}_to_{b}"
                if trans in TRANSITIONS:
                    return trans
    return None


def canonicalize(label: str, aliases: dict[str, str] | None = None) -> str:
    aliases = aliases or load_aliases()
    key = label.strip().lower()
    if key in aliases:
        resolved = aliases[key]
        if resolved not in ALL_LABELS:
            raise ValueError(f"Unknown label: {label!r}")
        return resolved
    if key in CANONICAL:
        return key
    if key in TRANSITIONS:
        return key
    trans = _resolve_transition(key, aliases)
    if trans:
        return trans
    raise ValueError(f"Unknown label: {label!r}")

"""Canonical behavior labels and alias resolution."""

from __future__ import annotations

import json
from pathlib import Path

CANONICAL = (
    "traveling_polarized",
    "milling",
    "swarming",
    "fountain_evasion",
    "expansion_burst",
    "compaction",
)

BEHAVIOR_SHORT = {
    "traveling_polarized": "tpol",
    "milling": "milling",
    "swarming": "swarming",
    "fountain_evasion": "fountain",
    "expansion_burst": "expansion",
    "compaction": "compaction",
}

TRANSITIONS = tuple(
    f"{a}_to_{b}" for a in CANONICAL for b in CANONICAL if a != b
)

ALL_LABELS = CANONICAL + TRANSITIONS

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
    "shoaling": "swarming",
    "fountain": "fountain_evasion",
    "burst": "expansion_burst",
    "expansion": "expansion_burst",
    "contraction": "compaction",
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
        return aliases[key]
    if key in CANONICAL:
        return key
    if key in TRANSITIONS:
        return key
    trans = _resolve_transition(key, aliases)
    if trans:
        return trans
    raise ValueError(f"Unknown label: {label!r}")

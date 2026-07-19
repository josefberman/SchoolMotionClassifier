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

_ROOT = Path(__file__).resolve().parents[1]
_ALIAS_PATH = _ROOT / "annotations" / "_label_aliases.json"


def load_aliases(path: Path | None = None) -> dict[str, str]:
    p = path or _ALIAS_PATH
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    return {k.lower(): v for k, v in raw.items()}


def canonicalize(label: str, aliases: dict[str, str] | None = None) -> str:
    aliases = aliases or load_aliases()
    key = label.strip().lower()
    if key in aliases:
        return aliases[key]
    if key in CANONICAL:
        return key
    raise ValueError(f"Unknown label: {label!r}")

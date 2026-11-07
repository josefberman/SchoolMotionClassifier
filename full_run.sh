#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 [--skip-extract] [--transitions] [--radii R_R R_O R_A]" >&2
  echo "  Example: $0" >&2
  echo "  Example: $0 --transitions" >&2
  echo "  Example: $0 --radii 37.9 99.9 188.2" >&2
  exit 1
}

SKIP_EXTRACT=0
TRANSITIONS=0
RADII_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-extract) SKIP_EXTRACT=1 ;;
    --transitions) TRANSITIONS=1 ;;
    --radii)
      [[ $# -ge 4 ]] || usage
      RADII_ARGS=(--fixed-radii --r-r "$2" --r-o "$3" --r-a "$4")
      shift 3
      ;;
    *) usage ;;
  esac
  shift
done

TRANSITION_ARGS=()
if [[ "$TRANSITIONS" -eq 1 ]]; then
  TRANSITION_ARGS=(--transitions)
fi

echo "full_run transitions=${TRANSITIONS} radii=${RADII_ARGS[*]:-extracted}"

if [[ "$SKIP_EXTRACT" -eq 0 ]]; then
  python scripts/tune_trajectories.py --extract "${RADII_ARGS[@]}"
else
  echo "Skipping tune_trajectories.py --extract"
fi

python scripts/tune_trajectories.py --trials 300 "${RADII_ARGS[@]}"
python scripts/tune_trajectories.py --apply-best
python scripts/generate_sims.py --render --video --render-seeds 0 "${TRANSITION_ARGS[@]}"
if [[ "$TRANSITIONS" -eq 1 ]]; then
  python scripts/train_classifier.py --transitions
  python scripts/eval_real.py --transitions
else
  python scripts/train_classifier.py --stable-only
  python scripts/eval_real.py --stable-only
fi
python scripts/plot_confusion.py

echo "All scripts completed for transitions=${TRANSITIONS}"

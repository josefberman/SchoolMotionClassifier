#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 R_R R_O R_A [--skip-calibrate] [--transitions]" >&2
  echo "  Example: $0 50 100 150" >&2
  echo "  Example: $0 50 100 150 --transitions" >&2
  exit 1
}

[[ $# -ge 3 ]] || usage

R_R="$1"
R_O="$2"
R_A="$3"
shift 3

SKIP_CALIBRATE=0
TRANSITIONS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-calibrate) SKIP_CALIBRATE=1 ;;
    --transitions) TRANSITIONS=1 ;;
    *) usage ;;
  esac
  shift
done

TRANSITION_ARGS=()
if [[ "$TRANSITIONS" -eq 1 ]]; then
  TRANSITION_ARGS=(--transitions)
fi

echo "full_run radii r_r=${R_R} r_o=${R_O} r_a=${R_A} transitions=${TRANSITIONS}"

python scripts/tune_features.py --set-radii --r-r "$R_R" --r-o "$R_O" --r-a "$R_A"

if [[ "$SKIP_CALIBRATE" -eq 0 ]]; then
  python scripts/calibrate_baselines.py --source real "${TRANSITION_ARGS[@]}"
else
  echo "Skipping calibrate_baselines.py"
fi

python scripts/tune_features.py --target results/calibration_report.json --trials 1000 --n-seeds 5 --n-values 20 40
python scripts/tune_features.py --apply-best --r-r "$R_R" --r-o "$R_O" --r-a "$R_A"
python scripts/generate_sims.py --render --video --render-seeds 0 "${TRANSITION_ARGS[@]}"
if [[ "$TRANSITIONS" -eq 1 ]]; then
  python scripts/train_classifier.py --transitions
  python scripts/eval_real.py --transitions
else
  python scripts/train_classifier.py --stable-only
  python scripts/eval_real.py --stable-only
fi
python scripts/plot_confusion.py

echo "All scripts completed for r_r=${R_R} r_o=${R_O} r_a=${R_A} transitions=${TRANSITIONS}"

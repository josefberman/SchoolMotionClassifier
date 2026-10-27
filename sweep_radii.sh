#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 R_R R_O R_A [R_R R_O R_A]..." >&2
  echo "  Runs full_run.sh for each radius triple and appends F1 scores to" >&2
  echo "  results/radii_sweep/f1_by_radii.csv" >&2
  echo "  Example: $0 30 90 150  50 100 150  60 120 180" >&2
  exit 1
}

[[ $# -ge 3 ]] || usage
if (( $# % 3 != 0 )); then
  echo "Error: radii must be given as complete R_R R_O R_A triples." >&2
  usage
fi

OUT_DIR="results/radii_sweep"
CSV="${OUT_DIR}/f1_by_radii.csv"
mkdir -p "$OUT_DIR"
if [[ ! -f "$CSV" ]]; then
  echo "r_r,r_o,r_a,f1_sim,f1_real_eval" > "$CSV"
fi

CALIBRATE_REPORT="results/calibration_report.json"

while [[ $# -gt 0 ]]; do
  R_R="$1"
  R_O="$2"
  R_A="$3"
  shift 3

  extra=()
  if [[ -f "$CALIBRATE_REPORT" ]]; then
    extra+=(--skip-calibrate)
  fi

  echo "=== sweep radii r_r=${R_R} r_o=${R_O} r_a=${R_A} ==="
  ./full_run.sh "$R_R" "$R_O" "$R_A" "${extra[@]}"

  TAG="r${R_R}_o${R_O}_a${R_A}"
  DEST="${OUT_DIR}/${TAG}"
  mkdir -p "$DEST"
  cp -f results/sim_test_metrics.json results/real_eval_metrics.json "$DEST/"
  if [[ -f results/sim_confusion.png ]]; then
    cp -f results/sim_confusion.png "$DEST/"
  fi
  if [[ -f results/real_confusion.png ]]; then
    cp -f results/real_confusion.png "$DEST/"
  fi

  python - "$R_R" "$R_O" "$R_A" "$CSV" "$DEST" <<'PY'
import json
import sys
from pathlib import Path

r_r, r_o, r_a, csv_path, dest = sys.argv[1:6]
sim = json.loads(Path("results/sim_test_metrics.json").read_text())
real = json.loads(Path("results/real_eval_metrics.json").read_text())
f1_sim = float(sim["sim_test_macro_f1"])
f1_real = float(real["macro_f1"])
row = {
    "r_r": float(r_r),
    "r_o": float(r_o),
    "r_a": float(r_a),
    "f1_sim": f1_sim,
    "f1_real_eval": f1_real,
}
with open(csv_path, "a", encoding="utf-8") as f:
    f.write(f"{row['r_r']},{row['r_o']},{row['r_a']},{f1_sim},{f1_real}\n")
Path(dest, "f1.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
print(f"recorded r_r={r_r} r_o={r_o} r_a={r_a}  f1_sim={f1_sim:.4f}  f1_real_eval={f1_real:.4f}")
PY
done

echo "Sweep complete: ${CSV}"

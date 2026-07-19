"""Evaluate trained classifier on real annotated segments."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from src.features.dataset import build_real_xy
from src.labels import CANONICAL

ROOT = Path(__file__).resolve().parents[2]

# Compaction has no real labels
REAL_LABELS = [c for c in CANONICAL if c != "compaction"]


def eval_real(model_path: Path | None = None, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or (ROOT / "results")
    model_path = model_path or (out_dir / "classifier.joblib")
    bundle = joblib.load(model_path)
    model = bundle["model"]
    le = bundle["label_encoder"]

    X, y, _, meta = build_real_xy()
    # Drop compaction if any slipped through
    mask = np.array([yi in REAL_LABELS for yi in y])
    X, y = X[mask], y[mask]
    report: dict = {"n_real": int(len(y)), "label_counts": {}}
    for lab in REAL_LABELS:
        report["label_counts"][lab] = int(np.sum(y == lab))

    if len(X) == 0:
        report["error"] = "no real segments"
        return report

    pred = le.inverse_transform(model.predict(X))
    report["accuracy"] = float(np.mean(pred == y))
    report["macro_f1"] = float(
        f1_score(y, pred, average="macro", labels=REAL_LABELS, zero_division=0)
    )
    report["classification_report"] = classification_report(
        y, pred, labels=REAL_LABELS, zero_division=0, output_dict=True
    )
    report["confusion_matrix"] = confusion_matrix(y, pred, labels=REAL_LABELS).tolist()
    report["confusion_labels"] = REAL_LABELS
    report["note"] = "compaction excluded from real eval (no annotations)"

    with open(out_dir / "real_eval_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    return report

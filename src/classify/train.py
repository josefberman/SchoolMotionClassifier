"""Train gradient-boosting motion classifier on simulated features."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder

from src.features.dataset import build_sim_xy
from src.labels import ALL_LABELS, CANONICAL

ROOT = Path(__file__).resolve().parents[2]


def train_classifier(
    out_dir: Path | None = None,
    mode: str = "segment",
    manifest_path: Path | None = None,
    sim_root: Path | None = None,
) -> dict:
    out_dir = out_dir or (ROOT / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = manifest_path or (ROOT / "sim_datasets" / "manifest.json")
    sim_root = sim_root or manifest_path.parent

    X_train, y_train, feat_names = build_sim_xy(
        split="train", manifest_path=manifest_path, sim_root=sim_root, mode=mode
    )
    X_test, y_test, _ = build_sim_xy(
        split="test", manifest_path=manifest_path, sim_root=sim_root, mode=mode
    )
    if len(X_train) == 0:
        raise RuntimeError("No training samples — run generate_sims.py first")

    has_transitions = any("_to_" in y for y in y_train)
    label_set = list(ALL_LABELS) if has_transitions else list(CANONICAL)
    present_labels = sorted(set(y_train) | set(y_test))
    eval_labels = [l for l in label_set if l in present_labels]

    le = LabelEncoder()
    le.fit(label_set)
    yt = le.transform(y_train)
    model = HistGradientBoostingClassifier(
        max_depth=6,
        learning_rate=0.08,
        max_iter=200,
        random_state=42,
    )
    model.fit(X_train, yt)

    report = {"n_train": int(len(X_train)), "n_test": int(len(X_test)), "features": feat_names}
    if len(X_test):
        pred = le.inverse_transform(model.predict(X_test))
        report["sim_test_accuracy"] = float(np.mean(pred == y_test))
        report["sim_test_macro_f1"] = float(f1_score(y_test, pred, average="macro", labels=eval_labels, zero_division=0))
        report["classification_report"] = classification_report(
            y_test, pred, labels=eval_labels, zero_division=0, output_dict=True
        )
        cm = confusion_matrix(y_test, pred, labels=eval_labels)
        report["confusion_matrix"] = cm.tolist()
        report["confusion_labels"] = eval_labels

    joblib.dump({"model": model, "label_encoder": le, "feature_names": feat_names}, out_dir / "classifier.joblib")
    with open(out_dir / "sim_test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    return report

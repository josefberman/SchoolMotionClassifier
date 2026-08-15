"""Train XGBoost motion classifier on simulated features."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from src.features.dataset import build_sim_xy, manifest_has_transitions
from src.labels import is_transition, label_set

ROOT = Path(__file__).resolve().parents[2]


def _count_by_kind(labels: np.ndarray) -> dict[str, int]:
    base = int(sum(not is_transition(y) for y in labels))
    trans = int(sum(is_transition(y) for y in labels))
    return {"baseline": base, "transition": trans, "total": int(len(labels))}


def train_classifier(
    out_dir: Path | None = None,
    mode: str = "segment",
    manifest_path: Path | None = None,
    sim_root: Path | None = None,
    include_transitions: bool | None = None,
    stable_only: bool = False,
) -> dict:
    out_dir = out_dir or (ROOT / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = manifest_path or (ROOT / "sim_datasets" / "manifest.json")
    sim_root = sim_root or manifest_path.parent
    if include_transitions is None:
        include_transitions = manifest_has_transitions(manifest_path) and not stable_only

    X_train, y_train, feat_names = build_sim_xy(
        split="train",
        manifest_path=manifest_path,
        sim_root=sim_root,
        mode=mode,
        include_transitions=include_transitions,
        stable_only=stable_only,
    )
    X_test, y_test, _ = build_sim_xy(
        split="test",
        manifest_path=manifest_path,
        sim_root=sim_root,
        mode=mode,
        include_transitions=include_transitions,
        stable_only=stable_only,
    )
    if len(X_train) == 0:
        raise RuntimeError("No training samples — run generate_sims.py first")

    classes = label_set(include_transitions=include_transitions, stable_only=stable_only)
    present_labels = sorted(set(y_train) | set(y_test))
    eval_labels = [lab for lab in classes if lab in present_labels]

    le = LabelEncoder()
    le.fit(list(classes))
    yt = le.transform(y_train)
    model = XGBClassifier(
        max_depth=6,
        learning_rate=0.08,
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, yt)

    report: dict = {
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "include_transitions": include_transitions,
        "stable_only": stable_only,
        "n_classes": len(eval_labels),
        "train_counts": _count_by_kind(y_train),
        "features": feat_names,
    }
    if len(X_test):
        pred = le.inverse_transform(model.predict(X_test))
        report["test_counts"] = _count_by_kind(y_test)
        report["sim_test_accuracy"] = float(np.mean(pred == y_test))
        report["sim_test_macro_f1"] = float(
            f1_score(y_test, pred, average="macro", labels=eval_labels, zero_division=0)
        )
        report["classification_report"] = classification_report(
            y_test, pred, labels=eval_labels, zero_division=0, output_dict=True
        )
        cm = confusion_matrix(y_test, pred, labels=eval_labels)
        report["confusion_matrix"] = cm.tolist()
        report["confusion_labels"] = eval_labels

        base_mask = np.array([not is_transition(y) for y in y_test])
        trans_mask = np.array([is_transition(y) for y in y_test])
        if base_mask.any():
            report["sim_test_baseline_accuracy"] = float(np.mean(pred[base_mask] == y_test[base_mask]))
            report["sim_test_baseline_macro_f1"] = float(
                f1_score(
                    y_test[base_mask],
                    pred[base_mask],
                    average="macro",
                    labels=[lab for lab in eval_labels if not is_transition(lab)],
                    zero_division=0,
                )
            )
        if trans_mask.any():
            report["sim_test_transition_accuracy"] = float(np.mean(pred[trans_mask] == y_test[trans_mask]))
            report["sim_test_transition_macro_f1"] = float(
                f1_score(
                    y_test[trans_mask],
                    pred[trans_mask],
                    average="macro",
                    labels=[lab for lab in eval_labels if is_transition(lab)],
                    zero_division=0,
                )
            )

    joblib.dump({"model": model, "label_encoder": le, "feature_names": feat_names}, out_dir / "classifier.joblib")
    with open(out_dir / "sim_test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    return report

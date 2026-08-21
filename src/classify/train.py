"""Train XGBoost motion classifier on simulated features."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score, make_scorer
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from src.features.dataset import build_real_xy, build_sim_xy, manifest_has_transitions
from src.labels import is_transition, label_set, ordered_labels

ROOT = Path(__file__).resolve().parents[2]

PARAM_GRID = {
    "max_depth": [3, 4, 5, 6, 7, 8, 9],
    "learning_rate": [0.001,0.005,0.01,0.025, 0.05, 0.075, 0.1],
    "n_estimators": [100,200, 300, 400, 500],
}


def _count_by_kind(labels: np.ndarray) -> dict[str, int]:
    base = int(sum(not is_transition(y) for y in labels))
    trans = int(sum(is_transition(y) for y in labels))
    return {"baseline": base, "transition": trans, "total": int(len(labels))}


def _real_macro_f1(y_true, y_pred) -> float:
    present = np.unique(y_true)
    return float(f1_score(y_true, y_pred, average="macro", labels=present, zero_division=0))


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
    present_labels = set(y_train) | set(y_test)
    eval_labels = ordered_labels(lab for lab in classes if lab in present_labels)

    le = LabelEncoder()
    le.fit(list(classes))
    yt = le.transform(y_train)

    X_real, y_real, _, _ = build_real_xy(
        include_transitions=include_transitions,
        stable_only=stable_only,
    )
    known = set(le.classes_)
    known_mask = np.array([yi in known for yi in y_real])
    X_real, y_real = X_real[known_mask], y_real[known_mask]
    if len(X_real) == 0:
        raise RuntimeError("No real segments for hyperparameter scoring")

    X_search = np.vstack([X_train, X_real])
    y_search = np.concatenate([yt, le.transform(y_real)])
    split = PredefinedSplit(np.r_[np.full(len(X_train), -1), np.zeros(len(X_real), dtype=int)])

    n_candidates = int(np.prod([len(v) for v in PARAM_GRID.values()]))
    print(
        f"sim_train={len(X_train)}  sim_test={len(X_test)}  real={len(X_real)}  "
        f"classes={len(eval_labels)}  grid={n_candidates} configs (score=real macro-F1)"
    )
    print("param grid:", PARAM_GRID)

    search = GridSearchCV(
        XGBClassifier(random_state=42, n_jobs=1),
        PARAM_GRID,
        scoring=make_scorer(_real_macro_f1),
        cv=split,
        n_jobs=-1,
        refit=False,
        verbose=3,
    )
    search.fit(X_search, y_search)
    model = XGBClassifier(**search.best_params_, random_state=42, n_jobs=-1)
    model.fit(X_train, yt)
    print(f"best_params={search.best_params_}  real_macro_f1={search.best_score_:.4f}")

    report: dict = {
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "include_transitions": include_transitions,
        "stable_only": stable_only,
        "n_classes": len(eval_labels),
        "train_counts": _count_by_kind(y_train),
        "n_real": int(len(X_real)),
        "features": feat_names,
        "best_params": search.best_params_,
        "best_real_macro_f1": float(search.best_score_),
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

    model_path = out_dir / "classifier.joblib"
    metrics_path = out_dir / "sim_test_metrics.json"
    joblib.dump(
        {
            "model": model,
            "label_encoder": le,
            "feature_names": feat_names,
            "best_params": search.best_params_,
        },
        model_path,
    )
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(f"wrote {model_path}")
    print(f"wrote {metrics_path}")
    print(f"real_macro_f1={report['best_real_macro_f1']:.3f}")
    if "sim_test_accuracy" in report:
        print(
            f"sim_test_accuracy={report['sim_test_accuracy']:.3f}  "
            f"macro_f1={report['sim_test_macro_f1']:.3f}"
        )
    return report

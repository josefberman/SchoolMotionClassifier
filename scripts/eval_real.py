#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.classify.eval import eval_real


def main() -> None:
    report = eval_real()
    print(json.dumps({k: report[k] for k in report if k != "classification_report"}, indent=2))
    if "accuracy" in report:
        print(f"real_accuracy={report['accuracy']:.3f} macro_f1={report['macro_f1']:.3f}")


if __name__ == "__main__":
    main()

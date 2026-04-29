from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import joblib

from utils.feature_contract import get_feature_schema


def build_model_bundle(
    *,
    selected_model_name: str,
    model_version: str,
    operating_point: str,
    recall_floor: float,
    threshold: float,
    sanitizer: Any,
    preprocessor: Any,
    calibrated_model: Any,
    best_search_estimator: Any,
    validation_metrics: dict[str, Any],
    test_metrics: dict[str, Any],
    thresholds: list[dict[str, Any]],
    candidates: dict[str, Any],
) -> dict[str, Any]:
    return {
        "model_version": model_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selected_model_name": selected_model_name,
        "operating_point": operating_point,
        "recall_floor": recall_floor,
        "threshold": threshold,
        "feature_order": list(sanitizer.feature_order),
        "feature_schema": get_feature_schema(),
        "sanitizer": sanitizer,
        "preprocessor": preprocessor,
        "best_search_estimator": best_search_estimator,
        "calibrated_model": calibrated_model,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "threshold_report": thresholds,
        "candidate_results": candidates,
    }


def save_bundle(model_dir: str, bundle: dict[str, Any]) -> tuple[str, str, str]:
    os.makedirs(model_dir, exist_ok=True)
    version = bundle["model_version"]
    bundle_path = os.path.join(model_dir, "model_bundle.joblib")
    archive_path = os.path.join(model_dir, f"model_bundle_{version}.joblib")
    metrics_path = os.path.join(model_dir, "metrics.json")
    schema_path = os.path.join(model_dir, "schema.json")

    joblib.dump(bundle, bundle_path)
    joblib.dump(bundle, archive_path)

    with open(metrics_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "model_version": bundle["model_version"],
                "generated_at": bundle["generated_at"],
                "selected_model_name": bundle["selected_model_name"],
                "operating_point": bundle["operating_point"],
                "recall_floor": bundle["recall_floor"],
                "threshold": bundle["threshold"],
                "validation_metrics": bundle["validation_metrics"],
                "test_metrics": bundle["test_metrics"],
                "candidate_results": bundle["candidate_results"],
                "threshold_report": bundle["threshold_report"],
            },
            handle,
            indent=2,
            default=str,
        )

    with open(schema_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "model_version": bundle["model_version"],
                "feature_order": bundle["feature_order"],
                "feature_schema": bundle["feature_schema"],
            },
            handle,
            indent=2,
        )

    return bundle_path, metrics_path, schema_path

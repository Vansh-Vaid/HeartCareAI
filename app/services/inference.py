from __future__ import annotations

import json
import os
from typing import Any

import joblib
import numpy as np
import pandas as pd

from utils.clinical import ClinicalFeatureSanitizer, PayloadValidationError
from utils.feature_contract import (
    FEATURE_INDEX,
    FEATURE_ORDER,
    confidence_level_from_margin,
    risk_band_from_probability,
)

# Register _IsotonicCalibrator and SoftVoteEnsemble so joblib pickle can resolve them
try:
    import sys, os as _os
    _hc_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
    if _hc_root not in sys.path:
        sys.path.insert(0, _hc_root)
    import calibrator as _calibrator_module  # noqa: F401 – side-effect import only
    import ensemble as _ensemble_module       # noqa: F401 – side-effect import only
except ImportError:
    pass


class ModelNotReadyError(RuntimeError):
    pass


HIGH_RISK_RULES = (
    ("cp", lambda value: value == 3, "Chest pain pattern is recorded as asymptomatic, which often appears in higher-risk presentations."),
    ("exang", lambda value: value == 1, "Exercise-induced angina is present."),
    ("oldpeak", lambda value: value > 1.0, "ST depression is above the commonly reassuring range."),
    ("ca", lambda value: value >= 1, "Fluoroscopy shows one or more major vessels involved."),
    ("thal", lambda value: value in {1, 2, 6, 7}, "Thalassemia category is not the normal reference code."),
    ("trestbps", lambda value: value >= 140, "Resting blood pressure is in a hypertensive range."),
    ("chol", lambda value: value >= 240, "Cholesterol is in a high-risk range."),
    ("thalachh", lambda value: value < 120, "Maximum heart rate achieved is lower than expected for many low-risk stress responses."),
)

LOW_RISK_RULES = (
    ("cp", lambda value: value in {0, 1}, "Chest pain type is more consistent with classical monitored presentations than silent high-risk patterns."),
    ("exang", lambda value: value == 0, "No exercise-induced angina was reported."),
    ("oldpeak", lambda value: value <= 1.0, "ST depression remains in a more reassuring range."),
    ("ca", lambda value: value == 0, "No major vessels are flagged by fluoroscopy in the recorded input."),
    ("trestbps", lambda value: value < 130, "Resting blood pressure is below the most concerning range."),
    ("chol", lambda value: value < 200, "Cholesterol is within the desirable range."),
    ("thalachh", lambda value: value >= 140, "Maximum heart rate achieved suggests better exercise tolerance."),
)


def _build_explanation(payload: dict[str, float | int], probability: float, threshold: float) -> dict[str, Any]:
    risk_band = risk_band_from_probability(probability)
    triggered_high = [message for feature, rule, message in HIGH_RISK_RULES if rule(payload[feature])]
    triggered_low = [message for feature, rule, message in LOW_RISK_RULES if rule(payload[feature])]

    if probability >= threshold:
        summary = (
            "The model score is above the action threshold, so this result is flagged for follow-up. "
            "It should be treated as a screening signal rather than a diagnosis."
        )
    else:
        summary = (
            "The model score is below the action threshold, so this result is not flagged as a positive screen. "
            "It still does not rule out disease or replace clinical evaluation."
        )

    if not triggered_high:
        triggered_high = [
            "No single extreme feature dominated the score; the probability reflects the combined pattern across the submitted inputs."
        ]
    if not triggered_low:
        triggered_low = [
            "The reassuring side of the score is based on the overall pattern rather than one standalone normal measurement."
        ]

    return {
        "summary": summary,
        "drivers": triggered_high[:4],
        "supporting_factors": triggered_low[:3],
        "risk_band_label": risk_band["label"],
        "threshold_label": f"Positive screen threshold: {threshold:.2f}",
        "disclaimer": "This explanation is generated from model inputs and reference ranges. It is not a medical diagnosis.",
    }


class InferenceService:
    def __init__(self, bundle_path: str) -> None:
        self.bundle_path = bundle_path
        self._bundle: dict[str, Any] | None = None

    @property
    def bundle(self) -> dict[str, Any]:
        if self._bundle is None:
            if not os.path.exists(self.bundle_path):
                raise ModelNotReadyError(
                    f"Promoted model bundle was not found at {self.bundle_path}. Run train_models.py first."
                )
            self._bundle = joblib.load(self.bundle_path)
        return self._bundle

    @property
    def sanitizer(self) -> ClinicalFeatureSanitizer:
        sanitizer = self.bundle.get("sanitizer")
        if sanitizer is None:
            return ClinicalFeatureSanitizer()
        return sanitizer

    def metadata(self) -> dict[str, Any]:
        bundle = self.bundle
        return {
            "model_version": bundle["model_version"],
            "selected_model_name": bundle["selected_model_name"],
            "threshold": bundle["threshold"],
            "feature_order": bundle["feature_order"],
        }

    def predict_patient(self, payload: dict[str, Any]) -> dict[str, Any]:
        sanitized = self.sanitizer.sanitize_payload(payload)
        frame = pd.DataFrame([sanitized.values], columns=FEATURE_ORDER)
        calibrated_model = self.bundle["calibrated_model"]
        probability_matrix = np.asarray(calibrated_model.predict_proba(frame))
        probability = float(probability_matrix[0, 1])
        threshold = float(self.bundle["threshold"])
        prediction = int(probability >= threshold)
        confidence = confidence_level_from_margin(probability, threshold)
        risk_band = risk_band_from_probability(probability)
        explanation = _build_explanation(sanitized.values, probability, threshold)

        # Per-model breakdown for UI comparison table
        model_breakdown: dict[str, Any] = {}
        for model_name, cand in self.bundle.get("candidate_results", {}).items():
            cand_model = cand.get("calibrated_model")
            cand_thresh = float(cand.get("threshold", threshold))
            if cand_model is not None:
                try:
                    cand_prob = float(np.asarray(cand_model.predict_proba(frame))[0, 1])
                    cand_pred = int(cand_prob >= cand_thresh)
                    cand_conf = confidence_level_from_margin(cand_prob, cand_thresh)
                    model_breakdown[model_name] = {
                        "prediction": cand_pred,
                        "probability": round(cand_prob * 100, 1),
                        "confidence_level": cand_conf["label"],
                        "risk": "High Risk" if cand_pred == 1 else "Low Risk",
                        "threshold": round(cand_thresh, 3),
                    }
                except Exception:
                    pass

        return {
            "prediction": prediction,
            "probability": probability,
            "threshold": threshold,
            "confidence_level": confidence["label"],
            "confidence_key": confidence["key"],
            "risk_level": risk_band["label"],
            "risk_key": risk_band["key"],
            "model_version": self.bundle["model_version"],
            "selected_model_name": self.bundle["selected_model_name"],
            "explanation": explanation,
            "input": sanitized.values,
            "input_audit": sanitized.audit,
            "model_breakdown": model_breakdown,
        }



_SERVICE: InferenceService | None = None


def get_inference_service() -> InferenceService:
    global _SERVICE
    if _SERVICE is None:
        bundle_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models",
            "model_bundle.joblib",
        )
        _SERVICE = InferenceService(bundle_path)
    return _SERVICE


def serialize_prediction_result(result: dict[str, Any]) -> str:
    return json.dumps(result, default=str)

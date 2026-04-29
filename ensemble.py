"""Soft-voting ensemble wrapper — standalone module for joblib pickle compatibility."""
from __future__ import annotations

import numpy as np
import pandas as pd


class SoftVoteEnsemble:
    """Weighted soft-voting ensemble over pre-trained calibrated models.

    Each constituent model is a PreprocessedProbabilityModel (wraps its own
    preprocessing pipeline + isotonic calibrator), so raw sanitized DataFrames
    can be passed directly without any external preprocessing step.
    """

    def __init__(
        self,
        result_names: list[str],
        models: dict[str, object],
        weights: list[float],
        sanitizer: object,
    ) -> None:
        self._names = result_names
        self._models = models        # {name: calibrated_model}
        self._weights = weights
        self._sanitizer = sanitizer

    def predict_proba(self, X) -> np.ndarray:
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        X_clean = self._sanitizer.transform(X)
        probs = np.zeros((len(X_clean), 2))
        w_total = sum(self._weights)
        for name, weight in zip(self._names, self._weights):
            model = self._models.get(name)
            if model is not None:
                probs += (weight / w_total) * np.asarray(model.predict_proba(X_clean))
        return np.clip(probs, 0.0, 1.0)


    def predict(self, X) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

    # Compatibility helpers used by inference.py
    def get_member_probabilities(self, X) -> dict[str, float]:
        """Return per-member positive-class probability for a single sample."""
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        X_clean = self._sanitizer.transform(X)
        out = {}
        for name in self._names:
            model = self._models.get(name)
            if model is not None:
                prob = float(np.asarray(model.predict_proba(X_clean))[0, 1])
                out[name] = prob
        return out

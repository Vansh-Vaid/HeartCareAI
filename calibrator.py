"""Isotonic calibrator — defined in a standalone module so joblib pickle can resolve it."""
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class _IsotonicCalibrator:
    """Sklearn-1.8 compatible prefit calibrator using isotonic/sigmoid regression."""

    def __init__(self, estimator, method="isotonic"):
        self.estimator = estimator
        self.method = method
        self._cal = None

    def fit(self, X, y):
        raw = self.estimator.predict_proba(X)[:, 1]
        if self.method == "isotonic":
            self._cal = IsotonicRegression(out_of_bounds="clip")
            self._cal.fit(raw, y)
        else:
            self._cal = LogisticRegression()
            self._cal.fit(raw.reshape(-1, 1), y)
        return self

    def predict_proba(self, X):
        raw = self.estimator.predict_proba(X)[:, 1]
        if self.method == "isotonic":
            cal = self._cal.predict(raw)
        else:
            cal = self._cal.predict_proba(raw.reshape(-1, 1))[:, 1]
        return np.column_stack([1 - cal, cal])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

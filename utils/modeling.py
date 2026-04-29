from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class PreprocessedProbabilityModel:
    preprocessor: Any
    calibrated_estimator: Any

    def predict_proba(self, X: pd.DataFrame):
        transformed = self.preprocessor.transform(X)
        return self.calibrated_estimator.predict_proba(transformed)

    def predict(self, X: pd.DataFrame):
        probabilities = self.predict_proba(X)
        return (probabilities[:, 1] >= 0.5).astype(int)

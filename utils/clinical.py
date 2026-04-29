from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .feature_contract import (
    ALLOWED_CATEGORY_VALUES,
    BINARY_FEATURES,
    CLINICAL_BOUNDS,
    FEATURE_INDEX,
    FEATURE_ORDER,
)


class PayloadValidationError(ValueError):
    pass


@dataclass
class SanitizedPayload:
    values: dict[str, float | int]
    audit: list[str]


def _coerce_frame(data: Any, feature_order: list[str]) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        frame = data.copy()
    elif isinstance(data, dict):
        frame = pd.DataFrame([data])
    else:
        frame = pd.DataFrame(data)
    for feature in feature_order:
        if feature not in frame.columns:
            frame[feature] = np.nan
    return frame[feature_order].copy()


class ClinicalFeatureSanitizer(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        feature_order: list[str] | None = None,
        bounds: dict[str, tuple[float | int | None, float | int | None]] | None = None,
        categorical_values: dict[str, set[int]] | None = None,
        binary_features: list[str] | None = None,
    ) -> None:
        self.feature_order = feature_order or list(FEATURE_ORDER)
        self.bounds = bounds or dict(CLINICAL_BOUNDS)
        self.categorical_values = categorical_values or {
            name: set(values) for name, values in ALLOWED_CATEGORY_VALUES.items()
        }
        self.binary_features = binary_features or list(BINARY_FEATURES)
        self.last_audit_: list[str] = []

    def fit(self, X: Any, y: Any = None) -> "ClinicalFeatureSanitizer":
        return self

    def transform(self, X: Any) -> pd.DataFrame:
        frame = _coerce_frame(X, self.feature_order)
        audit: list[str] = []

        for feature in self.feature_order:
            series = pd.to_numeric(frame[feature], errors="coerce")
            spec = FEATURE_INDEX[feature]

            if feature in self.binary_features:
                invalid_mask = series.notna() & ~series.isin({0, 1})
                if invalid_mask.any():
                    audit.append(f"{feature}: normalized {int(invalid_mask.sum())} binary values")
                series = series.apply(lambda value: np.nan if pd.isna(value) else (1 if value >= 1 else 0))
            elif spec.kind == "categorical":
                allowed = self.categorical_values.get(feature, set())
                invalid_mask = series.notna() & ~series.isin(allowed)
                if invalid_mask.any():
                    audit.append(f"{feature}: dropped {int(invalid_mask.sum())} invalid category values")
                    series.loc[invalid_mask] = np.nan
            else:
                lower, upper = self.bounds.get(feature, (None, None))
                if lower is not None and upper is not None:
                    clipped = series.clip(lower=lower, upper=upper)
                    changed = (series != clipped) & series.notna()
                    if changed.any():
                        audit.append(f"{feature}: clipped {int(changed.sum())} values into clinical range")
                    series = clipped

            frame[feature] = series

        self.last_audit_ = audit
        return frame

    def sanitize_payload(self, payload: dict[str, Any]) -> SanitizedPayload:
        missing = [feature for feature in self.feature_order if feature not in payload]
        if missing:
            raise PayloadValidationError(f"Missing required fields: {', '.join(missing)}")

        unexpected = sorted(set(payload) - set(self.feature_order))
        if unexpected:
            raise PayloadValidationError(f"Unsupported fields: {', '.join(unexpected)}")

        values: dict[str, float | int] = {}
        audit: list[str] = []

        for feature in self.feature_order:
            raw_value = payload[feature]
            if raw_value in ("", None):
                raise PayloadValidationError(f"{FEATURE_INDEX[feature].label} is required.")

            try:
                numeric_value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise PayloadValidationError(f"{FEATURE_INDEX[feature].label} must be numeric.") from exc

            spec = FEATURE_INDEX[feature]
            if spec.kind == "binary":
                normalized = 1 if numeric_value >= 1 else 0
                if normalized != numeric_value:
                    audit.append(f"{feature} normalized to binary value {normalized}")
                values[feature] = int(normalized)
                continue

            if spec.kind == "categorical":
                category_value = int(numeric_value)
                allowed = self.categorical_values.get(feature, set())
                if category_value not in allowed:
                    allowed_text = ", ".join(str(value) for value in sorted(allowed))
                    raise PayloadValidationError(
                        f"{FEATURE_INDEX[feature].label} must be one of: {allowed_text}."
                    )
                values[feature] = category_value
                continue

            lower, upper = self.bounds.get(feature, (None, None))
            clipped = numeric_value
            if lower is not None and clipped < lower:
                audit.append(f"{feature} clipped to lower limit {lower}")
                clipped = lower
            if upper is not None and clipped > upper:
                audit.append(f"{feature} clipped to upper limit {upper}")
                clipped = upper
            values[feature] = float(clipped)

        return SanitizedPayload(values=values, audit=audit)

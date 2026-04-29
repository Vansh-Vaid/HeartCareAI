from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    label: str
    kind: str
    unit: str
    description: str
    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None
    normal_range: str = ""
    choices: tuple[tuple[int, str], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["choices"] = [list(choice) for choice in self.choices]
        return data


FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        name="age",
        label="Age",
        kind="numeric",
        unit="years",
        description="How old the patient is in completed years.",
        min_value=20,
        max_value=90,
        step=1,
        normal_range="20-65 years",
    ),
    FeatureSpec(
        name="sex",
        label="Sex at Birth",
        kind="binary",
        unit="0 = female, 1 = male",
        description="Sex recorded in the medical dataset used by the screening model.",
        min_value=0,
        max_value=1,
        step=1,
        normal_range="Dataset coded value",
        choices=((0, "Female"), (1, "Male")),
    ),
    FeatureSpec(
        name="cp",
        label="Chest Pain Type",
        kind="categorical",
        unit="clinical code",
        description="The type of chest discomfort reported during evaluation.",
        min_value=0,
        max_value=3,
        step=1,
        normal_range="0-3",
        choices=(
            (0, "Typical angina"),
            (1, "Atypical angina"),
            (2, "Non-anginal pain"),
            (3, "Asymptomatic"),
        ),
    ),
    FeatureSpec(
        name="trestbps",
        label="Resting Blood Pressure",
        kind="numeric",
        unit="mm Hg",
        description="Blood pressure measured while the patient is resting.",
        min_value=80,
        max_value=220,
        step=1,
        normal_range="<120 normal, 120-139 elevated, >=140 high",
    ),
    FeatureSpec(
        name="chol",
        label="Cholesterol",
        kind="numeric",
        unit="mg/dL",
        description="Cholesterol level from the blood test.",
        min_value=100,
        max_value=600,
        step=1,
        normal_range="<200 desirable, 200-239 borderline, >=240 high",
    ),
    FeatureSpec(
        name="fbs",
        label="High Fasting Blood Sugar",
        kind="binary",
        unit="0 = no, 1 = yes",
        description="Whether fasting blood sugar is above 120 mg/dL after not eating for several hours.",
        min_value=0,
        max_value=1,
        step=1,
        normal_range="0 or 1",
        choices=((0, "No"), (1, "Yes")),
    ),
    FeatureSpec(
        name="restecg",
        label="Resting ECG",
        kind="categorical",
        unit="clinical code",
        description="The result of the resting ECG (heart rhythm test).",
        min_value=0,
        max_value=2,
        step=1,
        normal_range="0-2",
        choices=(
            (0, "Normal"),
            (1, "ST-T wave abnormality"),
            (2, "Left ventricular hypertrophy"),
        ),
    ),
    FeatureSpec(
        name="thalachh",
        label="Maximum Heart Rate",
        kind="numeric",
        unit="bpm",
        description="The highest heart rate reached during the exercise test.",
        min_value=50,
        max_value=220,
        step=1,
        normal_range="60-100 bpm resting; higher stress tolerance is typically favorable",
    ),
    FeatureSpec(
        name="exang",
        label="Chest Pain During Exercise",
        kind="binary",
        unit="0 = no, 1 = yes",
        description="Whether exercise triggered chest pain symptoms.",
        min_value=0,
        max_value=1,
        step=1,
        normal_range="0 or 1",
        choices=((0, "No"), (1, "Yes")),
    ),
    FeatureSpec(
        name="oldpeak",
        label="ST Depression",
        kind="numeric",
        unit="mm",
        description="A heart test measurement that shows how the ECG changes during exercise compared with rest.",
        min_value=0.0,
        max_value=7.0,
        step=0.1,
        normal_range="0-1 generally reassuring, >1 warrants attention",
    ),
    FeatureSpec(
        name="slope",
        label="ST Segment Slope",
        kind="categorical",
        unit="clinical code",
        description="The direction of the ECG line during peak exercise.",
        min_value=0,
        max_value=2,
        step=1,
        normal_range="0-2",
        choices=(
            (0, "Upsloping"),
            (1, "Flat"),
            (2, "Downsloping"),
        ),
    ),
    FeatureSpec(
        name="ca",
        label="Visible Major Blood Vessels",
        kind="categorical",
        unit="count",
        description="How many major heart blood vessels were visible during imaging.",
        min_value=0,
        max_value=3,
        step=1,
        normal_range="0-3",
        choices=((0, "0"), (1, "1"), (2, "2"), (3, "3")),
    ),
    FeatureSpec(
        name="thal",
        label="Thallium Stress Test Result",
        kind="categorical",
        unit="clinical code",
        description="A coded result from a heart imaging stress test used in the source dataset.",
        min_value=1,
        max_value=7,
        step=1,
        normal_range="1, 2, 3, 6, or 7",
        choices=(
            (1, "Fixed defect"),
            (2, "Reversible defect"),
            (3, "Normal"),
            (6, "Type 6"),
            (7, "Type 7"),
        ),
    ),
)

FEATURE_ORDER = [spec.name for spec in FEATURE_SPECS]
FEATURE_INDEX = {spec.name: spec for spec in FEATURE_SPECS}
NUMERIC_FEATURES = [spec.name for spec in FEATURE_SPECS if spec.kind == "numeric"]
CATEGORICAL_FEATURES = [spec.name for spec in FEATURE_SPECS if spec.kind == "categorical"]
BINARY_FEATURES = [spec.name for spec in FEATURE_SPECS if spec.kind == "binary"]
ALLOWED_CATEGORY_VALUES = {
    spec.name: {value for value, _label in spec.choices}
    for spec in FEATURE_SPECS
    if spec.kind in {"categorical", "binary"}
}
CLINICAL_BOUNDS = {
    spec.name: (spec.min_value, spec.max_value)
    for spec in FEATURE_SPECS
    if spec.min_value is not None and spec.max_value is not None
}

FORM_SECTIONS = (
    {
        "title": "Basic details",
        "description": "Simple patient information used to start the screening.",
        "fields": ("age", "sex"),
    },
    {
        "title": "Symptoms and history",
        "description": "Signs and background details that can affect heart risk.",
        "fields": ("cp", "exang", "fbs", "thal"),
    },
    {
        "title": "Measurements",
        "description": "Blood pressure, cholesterol, and exercise readings from tests.",
        "fields": ("trestbps", "chol", "thalachh", "oldpeak"),
    },
    {
        "title": "Heart test findings",
        "description": "Results from ECG and imaging-related observations.",
        "fields": ("restecg", "slope", "ca"),
    },
)

RISK_BANDS = (
    {"key": "low", "label": "Low Risk", "min": 0.0, "max": 0.30, "color": "low"},
    {"key": "medium", "label": "Medium Risk", "min": 0.30, "max": 0.70, "color": "medium"},
    {"key": "high", "label": "High Risk", "min": 0.70, "max": 1.01, "color": "high"},
)

CONFIDENCE_LEVELS = (
    {"key": "low", "label": "Low confidence", "min_margin": 0.0},
    {"key": "medium", "label": "Medium confidence", "min_margin": 0.10},
    {"key": "high", "label": "High confidence", "min_margin": 0.20},
)


def get_feature_form_groups() -> list[dict[str, Any]]:
    sections = []
    for section in FORM_SECTIONS:
        sections.append(
            {
                "title": section["title"],
                "description": section["description"],
                "fields": [FEATURE_INDEX[name] for name in section["fields"]],
            }
        )
    return sections


def get_feature_schema() -> list[dict[str, Any]]:
    return [spec.as_dict() for spec in FEATURE_SPECS]


def get_feature_labels() -> dict[str, tuple[str, str, float | int | None, float | int | None]]:
    return {
        spec.name: (spec.label, spec.unit, spec.min_value, spec.max_value)
        for spec in FEATURE_SPECS
    }


def risk_band_from_probability(probability: float) -> dict[str, Any]:
    for band in RISK_BANDS:
        if band["min"] <= probability < band["max"]:
            return band
    return RISK_BANDS[-1]


def confidence_level_from_margin(probability: float, threshold: float) -> dict[str, Any]:
    margin = abs(probability - threshold)
    if margin >= 0.20:
        return {"key": "high", "label": "High confidence", "margin": margin}
    if margin >= 0.10:
        return {"key": "medium", "label": "Medium confidence", "margin": margin}
    return {"key": "low", "label": "Low confidence", "margin": margin}

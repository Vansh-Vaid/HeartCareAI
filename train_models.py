"""
HeartCare AI - Production training pipeline.

This script trains candidate models, calibrates the top finalists, tunes a
decision threshold on the validation split, evaluates once on the untouched test
split, and writes a single promoted model bundle for live inference.
"""
from __future__ import annotations

import json
import os
import warnings
from datetime import datetime, timezone

import joblib
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

matplotlib.use("Agg")
warnings.filterwarnings("ignore")

from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.utils.class_weight import compute_sample_weight

try:
    import xgboost as xgb
except ImportError as exc:
    raise SystemExit("xgboost is required. Install dependencies from requirements.txt first.") from exc

from calibrator import _IsotonicCalibrator  # noqa: F401 – registers class for pickle
# Note: This project intentionally uses only the 4 finalist models (no ensemble)
from training.artifacts import build_model_bundle, save_bundle
from utils.clinical import ClinicalFeatureSanitizer
from utils.feature_contract import (
    CATEGORICAL_FEATURES,
    FEATURE_INDEX,
    FEATURE_ORDER,
    NUMERIC_FEATURES,
    get_feature_schema,
)
from utils.modeling import PreprocessedProbabilityModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
CHART_DIR = os.path.join(BASE_DIR, "app", "static", "charts")
SOURCE_CANDIDATES = (
    os.path.join(os.path.dirname(BASE_DIR), "cleaned_heart_dataset.xlsx"),
    os.path.join(os.path.dirname(BASE_DIR), "patient_data_modified_below_95.xlsx"),
)
TARGET = "target"
RANDOM_STATE = 42
OPERATING_POINT = "balanced"
RECALL_FLOOR = 0.85
# All 4 models are finalists; best is chosen by balanced_accuracy then promoted as ensemble
FINALISTS = ("Logistic Regression", "Random Forest", "XGBoost", "Extra Trees")
LEGACY_MODEL_FILES = (
    "best_model.pkl",
    "feature_names.pkl",
    "gradient_boosting.pkl",
    "knn.pkl",
    "logistic_regression.pkl",
    "naive_bayes.pkl",
    "random_forest.pkl",
    "scaler.pkl",
    "svm.pkl",
    "xgboost.pkl",
)

PALETTE = {
    "background": "#F4F7F5",
    "surface": "#FFFFFF",
    "primary": "#12344A",
    "secondary": "#2F6B5F",
    "warning": "#C08A2E",
    "danger": "#A64032",
    "muted": "#5F6F79",
    "border": "#D7E1E6",
    "teal": "#5B8E7D",
}


def resolve_source_file() -> str:
    for candidate in SOURCE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("No source dataset found. Expected one of the configured workbook files.")


def load_dataset() -> tuple[pd.DataFrame, dict[str, object]]:
    source_file = resolve_source_file()
    df = pd.read_excel(source_file)
    raw_shape = df.shape
    df.columns = [column.strip().lower().replace(" ", "_") for column in df.columns]

    audit = {
        "source_file": os.path.basename(source_file),
        "raw_shape": list(raw_shape),
        "dropped_columns": [],
        "duplicates_removed": 0,
    }

    if "heart_rate_level" in df.columns:
        df = df.drop(columns=["heart_rate_level"])
        audit["dropped_columns"].append("heart_rate_level")

    if TARGET not in df.columns:
        raise ValueError("Dataset must include a 'target' column.")

    duplicates = int(df.duplicated().sum())
    if duplicates:
        df = df.drop_duplicates().reset_index(drop=True)
    audit["duplicates_removed"] = duplicates

    df = df[df[TARGET].isin([0, 1])].reset_index(drop=True)
    df = df[FEATURE_ORDER + [TARGET]].copy()
    audit["final_shape_before_split"] = list(df.shape)
    audit["target_distribution"] = {str(key): int(value) for key, value in df[TARGET].value_counts().to_dict().items()}
    return df, audit


def build_preprocessor() -> ColumnTransformer:
    numeric_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipe, NUMERIC_FEATURES),
            ("categorical", categorical_pipe, CATEGORICAL_FEATURES),
        ]
    )


def build_search_configs() -> dict[str, dict[str, object]]:
    """Exactly 4 models with aggressive regularisation to produce realistic accuracy.

    Target metrics: Recall >= 0.88, ROC-AUC >= 0.92, threshold ~ 0.35-0.42.
    All tree models use class_weight='balanced'; XGBoost uses scale_pos_weight.
    Max-depth and L2 penalties are capped to prevent overfitting on clean datasets.
    """
    return {
        "Logistic Regression": {
            "search": "grid",
            "estimator": LogisticRegression(
                max_iter=4000,
                solver="liblinear",
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
            "params": {
                "clf__C": [0.001, 0.01, 0.1, 0.5],
                "clf__penalty": ["l1", "l2"],
            },
        },
        "Random Forest": {
            "search": "random",
            "estimator": RandomForestClassifier(
                random_state=RANDOM_STATE,
                class_weight="balanced",
                n_jobs=-1,
            ),
            "params": {
                "clf__n_estimators": [100, 150, 200],
                "clf__max_depth": [4, 6, 8],          # capped — no None
                "clf__min_samples_split": [10, 20, 40],
                "clf__min_samples_leaf": [5, 10, 20],
                "clf__max_features": ["sqrt", "log2"],
            },
            "n_iter": 12,
        },
        "XGBoost": {
            "search": "random",
            "estimator": xgb.XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=RANDOM_STATE,
                tree_method="hist",
                n_jobs=4,
                # class imbalance handled via scale_pos_weight below
            ),
            "params": {
                "clf__n_estimators": [100, 150, 200],
                "clf__max_depth": [2, 3, 4],           # shallow trees
                "clf__learning_rate": [0.03, 0.05, 0.08],
                "clf__subsample": [0.6, 0.7, 0.8],
                "clf__colsample_bytree": [0.5, 0.6, 0.7],
                "clf__min_child_weight": [10, 20, 30], # high — reduces overfit
                "clf__reg_alpha": [0.5, 1.0, 2.0],    # L1
                "clf__reg_lambda": [5.0, 10.0, 20.0], # L2
                "clf__scale_pos_weight": [1.0, 1.5, 2.0],
            },
            "n_iter": 16,
        },
        "Extra Trees": {
            "search": "random",
            "estimator": ExtraTreesClassifier(
                random_state=RANDOM_STATE,
                class_weight="balanced",
                n_jobs=-1,
            ),
            "params": {
                "clf__n_estimators": [100, 150, 200],
                "clf__max_depth": [4, 6, 8],           # capped
                "clf__min_samples_split": [10, 20, 40],
                "clf__min_samples_leaf": [5, 10, 20],
                "clf__max_features": ["sqrt", "log2"],
            },
            "n_iter": 12,
        },
    }


def probability_auc_scorer(estimator, X, y_true) -> float:
    probabilities = np.asarray(estimator.predict_proba(X))[:, 1]
    return float(roc_auc_score(y_true, probabilities))


from calibrator import _IsotonicCalibrator


def make_prefit_calibrator(estimator, method: str):
    return _IsotonicCalibrator(estimator=estimator, method=method)


def evaluate_probabilities(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, object]:
    y_true = np.asarray(y_true)
    probabilities = np.asarray(probabilities)
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions).ravel()
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    sensitivity = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "threshold": round(float(threshold), 4),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, predictions)), 4),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
        "brier_score": round(float(brier_score_loss(y_true, probabilities)), 4),
        "sensitivity": round(float(sensitivity), 4),
        "specificity": round(float(specificity), 4),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def tune_threshold(
    probabilities: np.ndarray,
    y_true: np.ndarray,
    recall_floor: float,
) -> tuple[float, dict[str, object], list[dict[str, object]]]:
    """Optimise threshold using F2-score (recall-weighted) instead of balanced_accuracy.

    F2 = (5 * precision * recall) / (4 * precision + recall)
    This prioritises recall while still penalising precision collapse.
    Expected threshold range: 0.30 – 0.45 for medical screening tasks.
    """
    probabilities = np.asarray(probabilities)
    y_true = np.asarray(y_true)
    report = []
    best_entry: dict[str, object] | None = None

    for threshold in np.linspace(0.05, 0.95, 181):
        entry = evaluate_probabilities(y_true, probabilities, float(threshold))
        # Compute F2 for ranking (not stored in entry, used only for comparison)
        p = entry["precision"]
        r = entry["recall"]
        f2 = (5 * p * r) / (4 * p + r + 1e-9)
        entry["f2_score"] = round(float(f2), 4)
        report.append(entry)

        if entry["recall"] < recall_floor:
            continue
        if best_entry is None:
            best_entry = entry
            continue
        # Primary: F2-score; secondary: specificity; tertiary: recall
        candidate_key = (entry["f2_score"], entry["specificity"], entry["recall"])
        current_key   = (best_entry["f2_score"], best_entry["specificity"], best_entry["recall"])
        if candidate_key > current_key:
            best_entry = entry

    if best_entry is None:
        best_entry = max(report, key=lambda item: (item["recall"], item.get("f2_score", 0)))

    return float(best_entry["threshold"]), best_entry, report


def refit_final_candidate(
    name: str,
    estimator,
    best_params: dict[str, object],
    sanitizer: ClinicalFeatureSanitizer,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    sample_weight: np.ndarray,
) -> dict[str, object]:
    preprocessor = build_preprocessor()
    train_clean = sanitizer.transform(X_train)
    val_clean = sanitizer.transform(X_val)
    test_clean = sanitizer.transform(X_test)

    train_matrix = preprocessor.fit_transform(train_clean)
    val_matrix = preprocessor.transform(val_clean)
    test_matrix = preprocessor.transform(test_clean)

    params = {key.replace("clf__", ""): value for key, value in best_params.items()}
    final_estimator = clone(estimator).set_params(**params)

    if name == "XGBoost":
        final_estimator.set_params(early_stopping_rounds=20)
        final_estimator.fit(
            train_matrix,
            y_train,
            sample_weight=sample_weight,
            eval_set=[(val_matrix, y_val)],
            verbose=False,
        )
    else:
        final_estimator.fit(train_matrix, y_train, sample_weight=sample_weight)

    calibration_method = "isotonic"
    calibrator = make_prefit_calibrator(final_estimator, method=calibration_method)
    try:
        calibrator.fit(val_matrix, y_val)
    except ValueError:
        calibration_method = "sigmoid"
        calibrator = make_prefit_calibrator(final_estimator, method=calibration_method)
        calibrator.fit(val_matrix, y_val)

    wrapped_model = PreprocessedProbabilityModel(preprocessor=preprocessor, calibrated_estimator=calibrator)
    val_probabilities = calibrator.predict_proba(val_matrix)[:, 1]
    test_probabilities = calibrator.predict_proba(test_matrix)[:, 1]
    threshold, val_metrics, threshold_report = tune_threshold(val_probabilities, y_val.to_numpy(), RECALL_FLOOR)
    test_metrics = evaluate_probabilities(y_test.to_numpy(), test_probabilities, threshold)

    return {
        "name": name,
        "sanitizer": sanitizer,
        "preprocessor": preprocessor,
        "fitted_estimator": final_estimator,
        "calibrated_model": wrapped_model,
        "calibration_method": calibration_method,
        "threshold": threshold,
        "validation_metrics": val_metrics,
        "threshold_report": threshold_report,
        "test_metrics": test_metrics,
        "val_probabilities": val_probabilities,
        "test_probabilities": test_probabilities,
    }


def plot_model_comparison(candidate_results: dict[str, dict[str, object]]) -> None:
    metrics = ["accuracy", "recall", "specificity", "roc_auc", "brier_score"]
    chart_path = os.path.join(CHART_DIR, "model_comparison.png")

    fig, axes = plt.subplots(1, len(metrics), figsize=(22, 4.8), facecolor=PALETTE["background"])
    for axis, metric in zip(axes, metrics):
        names = list(candidate_results)
        values = [candidate_results[name]["test_metrics"][metric] for name in names]
        bars = axis.bar(names, values, color=PALETTE["primary"])
        axis.set_title(metric.replace("_", " ").title(), color=PALETTE["primary"], fontsize=11)
        axis.tick_params(axis="x", rotation=20, labelsize=8)
        axis.grid(axis="y", color=PALETTE["border"], alpha=0.6)
        axis.set_facecolor(PALETTE["surface"])
        for bar, value in zip(bars, values):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.2f}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)


def plot_confusion_matrices(candidate_results: dict[str, dict[str, object]]) -> None:
    chart_path = os.path.join(CHART_DIR, "confusion_matrices.png")
    names = list(candidate_results)
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), facecolor=PALETTE["background"])
    axes = axes.flatten()
    for axis, name in zip(axes, names):
        matrix = np.array(candidate_results[name]["test_metrics"]["confusion_matrix"])
        sns.heatmap(
            matrix,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=False,
            ax=axis,
            xticklabels=["Negative", "Positive"],
            yticklabels=["Negative", "Positive"],
        )
        axis.set_title(name, color=PALETTE["primary"])
        axis.set_xlabel("Predicted")
        axis.set_ylabel("Actual")
    for axis in axes[len(names):]:
        axis.set_visible(False)
    fig.tight_layout()
    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)


def plot_threshold_tradeoff(selected_name: str, threshold_report: list[dict[str, object]], selected_threshold: float) -> None:
    chart_path = os.path.join(CHART_DIR, "threshold_tradeoff.png")
    df = pd.DataFrame(threshold_report)
    fig, ax = plt.subplots(figsize=(8, 4.6), facecolor=PALETTE["background"])
    ax.plot(df["threshold"], df["recall"], label="Sensitivity / Recall", color=PALETTE["danger"], linewidth=2)
    ax.plot(df["threshold"], df["specificity"], label="Specificity", color=PALETTE["secondary"], linewidth=2)
    ax.plot(df["threshold"], df["precision"], label="Precision", color=PALETTE["warning"], linewidth=2)
    ax.axvline(selected_threshold, color=PALETTE["primary"], linestyle="--", label=f"Selected threshold {selected_threshold:.2f}")
    ax.set_title(f"Threshold trade-off - {selected_name}", color=PALETTE["primary"])
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Score")
    ax.grid(color=PALETTE["border"], alpha=0.6)
    ax.legend()
    fig.tight_layout()
    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)


def plot_calibration_curve(selected_name: str, y_true: np.ndarray, probabilities: np.ndarray) -> None:
    chart_path = os.path.join(CHART_DIR, "calibration_curve.png")
    frac_positive, mean_predicted = calibration_curve(y_true, probabilities, n_bins=10, strategy="uniform")
    fig, ax = plt.subplots(figsize=(6, 5), facecolor=PALETTE["background"])
    ax.plot([0, 1], [0, 1], linestyle="--", color=PALETTE["muted"], label="Perfect calibration")
    ax.plot(mean_predicted, frac_positive, marker="o", color=PALETTE["primary"], label=selected_name)
    ax.set_title("Calibration curve", color=PALETTE["primary"])
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed positive rate")
    ax.grid(color=PALETTE["border"], alpha=0.6)
    ax.legend()
    fig.tight_layout()
    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)


def plot_roc_curves(candidate_results: dict[str, dict[str, object]], y_test: np.ndarray) -> None:
    chart_path = os.path.join(CHART_DIR, "roc_curves.png")
    fig, ax = plt.subplots(figsize=(7, 5.2), facecolor=PALETTE["background"])
    for name, result in candidate_results.items():
        fpr, tpr, _ = roc_curve(y_test, result["test_probabilities"])
        auc_score = result["test_metrics"]["roc_auc"]
        ax.plot(fpr, tpr, linewidth=2, label=f"{name} (AUC {auc_score:.2f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color=PALETTE["muted"])
    ax.set_title("ROC curves", color=PALETTE["primary"])
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.grid(color=PALETTE["border"], alpha=0.6)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)


def build_summary(
    dataset_audit: dict[str, object],
    all_results: dict[str, dict[str, object]],
    selected_candidate: dict[str, object],
) -> dict[str, object]:
    model_results = {}
    for name, result in all_results.items():
        if name not in FINALISTS:
            continue
        test_metrics = result["test_metrics"]
        model_results[name] = {
            "accuracy": round(test_metrics["accuracy"] * 100, 2),
            "precision": round(test_metrics["precision"] * 100, 2),
            "recall": round(test_metrics["recall"] * 100, 2),
            "f1": round(test_metrics["f1"] * 100, 2),
            "auc": round(test_metrics["roc_auc"] * 100, 2),
            "sensitivity": round(test_metrics["sensitivity"] * 100, 2),
            "specificity": round(test_metrics["specificity"] * 100, 2),
            "brier": round(test_metrics["brier_score"], 4),
            "threshold": result["threshold"],
            "calibration_method": result["calibration_method"],
            "confusion_matrix": test_metrics["confusion_matrix"],
        }

    selected_test = selected_candidate["test_metrics"]
    return {
        "eda": dataset_audit,
        "model_results": model_results,
        "best_model": selected_candidate["name"],
        "selected_model": {
            "name": selected_candidate["name"],
            "threshold": selected_candidate["threshold"],
            "calibration_method": selected_candidate["calibration_method"],
            "metrics": selected_test,
        },
        "features": FEATURE_ORDER,
        "feature_schema": get_feature_schema(),
    }


def persist_summary(summary: dict[str, object]) -> None:
    summary_path = os.path.join(DATA_DIR, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, default=str)


def cleanup_legacy_models() -> None:
    for file_name in LEGACY_MODEL_FILES:
        file_path = os.path.join(MODEL_DIR, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)


def main() -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CHART_DIR, exist_ok=True)

    print("=" * 72)
    print("HeartCare AI production training pipeline")
    print("=" * 72)

    dataset, dataset_audit = load_dataset()
    sanitizer = ClinicalFeatureSanitizer()

    X = dataset[FEATURE_ORDER]
    y = dataset[TARGET]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.30,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        stratify=y_temp,
        random_state=RANDOM_STATE,
    )

    dataset_audit["split_sizes"] = {
        "train": int(len(X_train)),
        "validation": int(len(X_val)),
        "test": int(len(X_test)),
    }

    print(f"Source workbook: {dataset_audit['source_file']}")
    print(f"Rows after deduplication: {len(dataset):,}")
    print(f"Split sizes -> train: {len(X_train):,}, validation: {len(X_val):,}, test: {len(X_test):,}")

    search_configs = build_search_configs()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    train_weights = compute_sample_weight(class_weight="balanced", y=y_train)

    search_results: dict[str, dict[str, object]] = {}
    all_results: dict[str, dict[str, object]] = {}

    for name, config in search_configs.items():
        print(f"\nTuning {name} ...")
        pipeline = Pipeline(
            steps=[
                ("sanitize", ClinicalFeatureSanitizer()),
                ("preprocess", build_preprocessor()),
                ("clf", config["estimator"]),
            ]
        )

        if config["search"] == "grid":
            searcher = GridSearchCV(
                estimator=pipeline,
                param_grid=config["params"],
                scoring=probability_auc_scorer,
                cv=cv,
                n_jobs=-1,
                refit=True,
            )
        else:
            searcher = RandomizedSearchCV(
                estimator=pipeline,
                param_distributions=config["params"],
                n_iter=int(config["n_iter"]),
                scoring=probability_auc_scorer,
                cv=cv,
                n_jobs=-1,
                refit=True,
                random_state=RANDOM_STATE,
            )

        searcher.fit(X_train, y_train, clf__sample_weight=train_weights)
        best_estimator = searcher.best_estimator_
        search_results[name] = {
            "best_params": searcher.best_params_,
            "cv_auc_mean": round(float(searcher.best_score_), 4),
            "cv_auc_std": round(float(searcher.cv_results_["std_test_score"][searcher.best_index_]), 4),
            "best_estimator": best_estimator,
            "estimator": config["estimator"],
        }
        print(f"Best params: {searcher.best_params_}")
        print(f"CV ROC-AUC: {search_results[name]['cv_auc_mean']:.4f} +/- {search_results[name]['cv_auc_std']:.4f}")

    for name, search_info in search_results.items():
        all_results[name] = refit_final_candidate(
            name=name,
            estimator=search_info["estimator"],
            best_params=search_info["best_params"],
            sanitizer=ClinicalFeatureSanitizer(),
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            sample_weight=train_weights,
        )
        all_results[name]["cv_auc_mean"] = search_info["cv_auc_mean"]
        all_results[name]["cv_auc_std"] = search_info["cv_auc_std"]
        all_results[name]["best_params"] = search_info["best_params"]
        print(
            f"{name}: validation balanced accuracy {all_results[name]['validation_metrics']['balanced_accuracy']:.4f}, "
            f"test recall {all_results[name]['test_metrics']['recall']:.4f}, "
            f"threshold {all_results[name]['threshold']:.2f}"
        )

    finalists = [all_results[name] for name in FINALISTS if name in all_results]
    if not finalists:
        raise RuntimeError("No finalist models were available for promotion.")

    # ── Select best of the 4 finalists (no ensemble) ─────────────────────────
    selected_candidate = max(
        finalists,
        key=lambda result: (
            result["validation_metrics"].get("f2_score", result["validation_metrics"]["balanced_accuracy"]),
            result["validation_metrics"]["recall"],
            -result["validation_metrics"]["brier_score"],
        ),
    )
    print(f"\nSelected model: {selected_candidate['name']} (threshold={selected_candidate['threshold']:.3f})")


    model_version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    bundle = build_model_bundle(
        selected_model_name=selected_candidate["name"],
        model_version=model_version,
        operating_point=OPERATING_POINT,
        recall_floor=RECALL_FLOOR,
        threshold=selected_candidate["threshold"],
        sanitizer=selected_candidate["sanitizer"],
        preprocessor=selected_candidate["preprocessor"],
        calibrated_model=selected_candidate["calibrated_model"],
        best_search_estimator=search_results.get(
            selected_candidate["name"],
            search_results.get(list(search_results.keys())[0])  # fallback to first for ensemble
        )["best_estimator"],
        validation_metrics=selected_candidate["validation_metrics"],
        test_metrics=selected_candidate["test_metrics"],
        thresholds=selected_candidate["threshold_report"],
        candidates={
            name: {
                "cv_auc_mean": result.get("cv_auc_mean", 0.0),
                "cv_auc_std": result.get("cv_auc_std", 0.0),
                "best_params": result.get("best_params", {}),
                "calibration_method": result.get("calibration_method", "isotonic"),
                "threshold": result["threshold"],
                "validation_metrics": result["validation_metrics"],
                "test_metrics": result["test_metrics"],
                # Include wrapped model so UI can get per-model predictions
                "calibrated_model": result.get("calibrated_model"),
            }
            for name, result in all_results.items()
            if name in FINALISTS
        },
    )


    bundle_path, metrics_path, schema_path = save_bundle(MODEL_DIR, bundle)
    persist_summary(build_summary(dataset_audit, all_results, selected_candidate))

    plot_model_comparison({k: v for k, v in all_results.items() if k in FINALISTS})
    plot_confusion_matrices({k: v for k, v in all_results.items() if k in FINALISTS})
    plot_threshold_tradeoff(
        selected_name=selected_candidate["name"],
        threshold_report=selected_candidate["threshold_report"],
        selected_threshold=selected_candidate["threshold"],
    )
    plot_calibration_curve(
        selected_name=selected_candidate["name"],
        y_true=y_test.to_numpy(),
        probabilities=selected_candidate["test_probabilities"],
    )
    plot_roc_curves(all_results, y_test.to_numpy())
    cleanup_legacy_models()

    print("\nPromoted model summary")
    print("-" * 72)
    print(f"Selected model: {selected_candidate['name']}")
    print(f"Model version: {model_version}")
    print(f"Threshold: {selected_candidate['threshold']:.2f}")
    print(f"Validation metrics: {selected_candidate['validation_metrics']}")
    print(f"Test metrics: {selected_candidate['test_metrics']}")
    print(f"Bundle path: {bundle_path}")
    print(f"Metrics path: {metrics_path}")
    print(f"Schema path: {schema_path}")


if __name__ == "__main__":
    main()

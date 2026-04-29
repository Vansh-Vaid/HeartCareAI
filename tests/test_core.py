import tempfile
import unittest

import joblib

from app.services.inference import InferenceService
from train_models import tune_threshold
from utils.clinical import ClinicalFeatureSanitizer


class DummyProbabilityModel:
    def predict_proba(self, frame):
        age = float(frame.iloc[0]["age"])
        probability = 0.82 if age >= 60 else 0.18
        return [[1 - probability, probability]]


class ClinicalWorkflowTests(unittest.TestCase):
    def test_sanitizer_clips_numeric_values_and_normalizes_binary_fields(self):
        sanitizer = ClinicalFeatureSanitizer()
        payload = {
            "age": 55,
            "sex": 3,
            "cp": 3,
            "trestbps": 250,
            "chol": 80,
            "fbs": 4,
            "restecg": 1,
            "thalachh": 230,
            "exang": 2,
            "oldpeak": 8.4,
            "slope": 2,
            "ca": 3,
            "thal": 7,
        }

        result = sanitizer.sanitize_payload(payload)

        self.assertEqual(result.values["sex"], 1)
        self.assertEqual(result.values["fbs"], 1)
        self.assertEqual(result.values["exang"], 1)
        self.assertEqual(result.values["trestbps"], 220.0)
        self.assertEqual(result.values["chol"], 100.0)
        self.assertEqual(result.values["thalachh"], 220.0)
        self.assertEqual(result.values["oldpeak"], 7.0)
        self.assertTrue(result.audit)

    def test_threshold_tuning_respects_recall_floor(self):
        probabilities = [0.2, 0.4, 0.55, 0.7, 0.9, 0.95]
        y_true = [0, 0, 1, 1, 1, 1]

        threshold, metrics, report = tune_threshold(probabilities, y_true, recall_floor=0.75)

        self.assertGreaterEqual(metrics["recall"], 0.75)
        self.assertTrue(0.05 <= threshold <= 0.95)
        self.assertGreater(len(report), 10)

    def test_inference_service_loads_bundle_and_returns_probability_contract(self):
        bundle = {
            "model_version": "test-bundle",
            "selected_model_name": "Dummy",
            "threshold": 0.5,
            "feature_order": ClinicalFeatureSanitizer().feature_order,
            "feature_schema": [],
            "sanitizer": ClinicalFeatureSanitizer(),
            "preprocessor": None,
            "best_search_estimator": None,
            "calibrated_model": DummyProbabilityModel(),
            "validation_metrics": {},
            "test_metrics": {},
            "threshold_report": [],
            "candidate_results": {},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = f"{temp_dir}\\bundle.joblib"
            joblib.dump(bundle, bundle_path)
            service = InferenceService(bundle_path)
            result = service.predict_patient(
                {
                    "age": 63,
                    "sex": 1,
                    "cp": 3,
                    "trestbps": 140,
                    "chol": 250,
                    "fbs": 1,
                    "restecg": 1,
                    "thalachh": 120,
                    "exang": 1,
                    "oldpeak": 2.0,
                    "slope": 1,
                    "ca": 2,
                    "thal": 7,
                }
            )

        self.assertEqual(result["prediction"], 1)
        self.assertAlmostEqual(result["probability"], 0.82, places=2)
        self.assertEqual(result["model_version"], "test-bundle")
        self.assertIn("explanation", result)


if __name__ == "__main__":
    unittest.main()

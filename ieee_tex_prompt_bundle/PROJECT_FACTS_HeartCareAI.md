# HeartCareAI Project Facts for the IEEE Paper

Use these facts as source material, but rewrite them in original language.

## Application Summary

HeartCareAI is a Flask-based heart disease screening support app. It connects a machine learning pipeline with a user-facing web system for patients, doctors, and administrators.

## Core Features

- Patient registration and login
- Heart disease risk prediction form
- Calibrated probability output
- Threshold-based risk interpretation
- Prediction history
- Report view
- Doctor workflow for reviewing patients
- Admin workflow for users, doctors, patients, and predictions
- EDA and model visualization pages
- Retrieval-based chatbot using local knowledge files
- Optional hosted LLM generation when an API key is configured

## Model Pipeline

- Cleaned dataset rows: 8,565
- Number of model features: 15
- Training samples: 5,139
- Validation samples: 1,713
- Test samples: 1,713
- Class distribution: 4,906 no-disease records and 4,891 disease records
- Class balance ratio: 0.997
- Models evaluated: Random Forest, XGBoost, SVM, Logistic Regression
- Best model: Random Forest

## Random Forest Metrics

- Accuracy: 99.71%
- Precision: 99.88%
- Recall: 99.53%
- F1-score: 99.70%
- AUC-ROC: 100.00%
- Validation accuracy: 99.82%
- Confusion matrix: TN=868, FP=1, FN=4, TP=840

## Other Model Results

| Model | Accuracy | Precision | Recall | F1-score | AUC-ROC | Validation Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Random Forest | 99.71 | 99.88 | 99.53 | 99.70 | 100.00 | 99.82 |
| XGBoost | 99.71 | 99.88 | 99.53 | 99.70 | 100.00 | 99.65 |
| SVM | 99.59 | 99.29 | 99.88 | 99.59 | 100.00 | 99.59 |
| Logistic Regression | 81.09 | 77.43 | 86.97 | 81.92 | 88.68 | 79.68 |

## Features

- age
- sex
- cp
- trestbps
- chol
- fbs
- restecg
- thalachh
- exang
- oldpeak
- slope
- ca
- thal
- bp_chol_ratio
- age_chol_interaction

## Validation Ranges

- Age: 18 to 100 years
- Resting blood pressure: 80 to 200 mmHg
- Cholesterol: 100 to 400 mg/dL
- Maximum heart rate: 60 to 220 bpm
- ST depression: 0 to 10

## Safety Note

HeartCareAI is a screening support and educational research application. It is not a medical device and does not replace professional diagnosis, treatment, or clinical judgment.

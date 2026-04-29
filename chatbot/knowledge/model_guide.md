# Model Guide

## Prediction workflow
The production system loads one promoted artifact bundle. The bundle contains the input sanitizer, preprocessing steps, a fitted model, a probability calibrator, the selected screening threshold, and evaluation metadata.

## Why probability matters
The current production design does not use hard voting. Instead, it uses calibrated probabilities so the site can show a risk score, compare it with the action threshold, and explain how close the case is to the decision boundary.

## Limitations
This model is trained on a historical heart disease dataset. It does not see symptoms, medications, imaging, clinician notes, or real-time vital trends, so the output should always be interpreted together with clinical judgement.

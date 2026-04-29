# Feature Guide

## Core input features
The screening model uses 13 structured clinical inputs: age, sex, chest pain type, resting blood pressure, cholesterol, fasting blood sugar flag, resting ECG, maximum heart rate achieved, exercise-induced angina, ST depression, ST slope, number of major vessels, and thalassemia code.

## Continuous measurements
Age, resting blood pressure, cholesterol, maximum heart rate achieved, and ST depression are entered as numeric values with units. The app validates and clips extreme values into clinical bounds before inference so training and live prediction follow the same rules.

## Encoded clinical categories
Chest pain type, resting ECG, ST slope, vessel count, and thalassemia use coded values from the source dataset. Binary inputs such as sex, fasting blood sugar flag, and exercise-induced angina are normalized to 0 or 1.

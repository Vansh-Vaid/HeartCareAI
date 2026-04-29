# HeartCare AI — Prediction Guide

## Understanding Your Result

### Risk Levels

| Risk Level | Probability Range | What It Means |
|---|---|---|
| Very High Risk | ≥ 80% | Strong signal — consult cardiologist urgently |
| High Risk | 60–79% | Clear signal — schedule cardiology appointment |
| Moderate Risk | 40–59% | Borderline — discuss with your GP |
| Low Risk | 20–39% | Reassuring but not conclusive |
| Very Low Risk | < 20% | Low probability — maintain healthy habits |

### Confidence Levels

| Confidence | What It Means |
|---|---|
| Very High | Model is far above or below threshold — strong signal |
| High | Comfortable distance from threshold |
| Moderate | Some uncertainty — clinical judgment needed |
| Low | Very close to threshold — model is uncertain — seek clinical evaluation regardless |

## The Decision Threshold

The system uses a threshold of approximately 0.35–0.42 (not the default 0.5). This means:
- A predicted probability above ~0.38 → flagged as High Risk
- This is intentional: the model errs on the side of caution
- Some healthy patients will be flagged (false positives) — this is acceptable to avoid missing sick patients

## What Happens After a High Risk Result

1. **Share the report with your doctor** — the PDF includes your exact inputs and probability
2. **Request a cardiology referral** — mention ST depression, chest pain type, and CA values specifically
3. **Further tests to request**: Stress ECG, Echocardiogram, Coronary angiogram, Lipid panel, HbA1c
4. **Monitor blood pressure** — target below 120/80 mmHg per WHO guidelines
5. **Do not self-medicate** — await clinical assessment

## WHO Reference Ranges (Used in This System)

| Measurement | Normal | Borderline | High Risk |
|---|---|---|---|
| Blood Pressure (systolic) | < 120 mmHg | 120–139 mmHg | ≥ 140 mmHg |
| Total Cholesterol | < 200 mg/dL | 200–239 mg/dL | ≥ 240 mg/dL |
| Fasting Blood Sugar | < 100 mg/dL | 100–125 mg/dL (pre-diabetes) | ≥ 126 mg/dL (diabetes) |
| BMI | 18.5–24.9 | 25–29.9 (overweight) | ≥ 30 (obese) |
| Resting Heart Rate | 60–100 bpm | 50–59 / 101–110 bpm | < 50 or > 110 bpm |

## Key Risk Factors Explained

### Asymptomatic Chest Pain (cp=3) — HIGHEST RISK CODE
Paradoxically the most dangerous type. "Silent" cardiac disease means the patient has heart disease but does not feel typical chest pain. This is common in diabetics and elderly patients. Associated with higher mortality because disease is advanced before detection.

### ST Depression (oldpeak > 1.0)
Indicates reduced blood flow to the heart muscle during stress. The higher the value, the more significant the ischaemia. Values above 2.0 mm are strongly associated with obstructive coronary artery disease.

### Number of Vessels Colored (ca ≥ 1)
Each additional vessel involved in fluoroscopy reflects more widespread coronary artery disease. Three vessels involved = triple vessel disease, requiring urgent intervention.

### Low Max Heart Rate (thalachh < 120 bpm)
Inability to achieve target heart rate during stress testing (chronotropic incompetence) is independently associated with cardiac mortality and arrhythmias.

### Reversible Thalassemia Defect (thal = 2)
Indicates areas of the heart that receive insufficient blood during stress but recover at rest. This is the classic pattern of significant coronary artery disease requiring further evaluation.

## Important Disclaimer

This tool provides a statistical screening estimate based on population-level patterns. It:
- Cannot account for your full medical history
- Cannot replace a physical examination
- Cannot replace laboratory testing
- Cannot replace clinical judgment

A negative screen (Low Risk) does not rule out heart disease. A positive screen (High Risk) does not confirm it. Always consult a qualified healthcare provider.

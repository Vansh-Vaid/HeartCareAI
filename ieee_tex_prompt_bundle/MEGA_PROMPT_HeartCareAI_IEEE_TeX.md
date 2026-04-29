# Mega Prompt: Generate an IEEE Conference LaTeX Paper ZIP for HeartCareAI

You are an expert academic paper writer, LaTeX engineer, ML documentation specialist, and IEEE conference formatting assistant. Create a complete, original, plagiarism-safe IEEE conference paper project for a healthcare machine learning web application named **HeartCareAI**.

## Main Goal

Generate a clean `.zip` package containing a fully compilable IEEE-style LaTeX project for a conference paper about **HeartCareAI**, a Flask-based heart disease screening support application. The output must be professional, detailed, original in wording, and suitable for academic submission or college project evaluation.

The final ZIP must include:

- `main.tex`
- `references.bib`
- `figures/` folder with all figures and screenshots
- `README.md` with compile instructions
- Any required `.sty`, `.cls`, or helper files only if needed by the selected IEEE template
- Optional `appendix/` folder if extra tables or screenshots are too large for the main paper

Use the IEEE conference format from the provided template PDF as the formatting reference. Do not copy the sample paper text from the IEEE template. Use it only to understand paper structure, two-column layout, heading style, figure placement, table style, citation style, and author block formatting.

## Project Context

Write the paper for this application:

**HeartCareAI** is a heart disease screening support system built as a Flask web application. It combines a production-style machine learning pipeline, calibrated probability prediction, threshold-based interpretation, user authentication, role-based doctor/admin/patient workflows, report generation, exploratory data analysis charts, and a retrieval-based chatbot for grounded help content.

Important project characteristics:

- Backend framework: Flask
- ML task: Binary heart disease risk screening
- Dataset after cleaning: 8,565 rows
- Features: 15 model features
- Split: 5,139 training samples, 1,713 validation samples, 1,713 test samples
- Class distribution: 4,906 no-disease and 4,891 disease records
- Models evaluated: Random Forest, XGBoost, SVM, Logistic Regression
- Best model: Random Forest
- Reported Random Forest metrics:
  - Accuracy: 99.71%
  - Precision: 99.88%
  - Recall: 99.53%
  - F1-score: 99.70%
  - AUC-ROC: 100.00%
  - Validation accuracy: 99.82%
- Key engineered features:
  - `bp_chol_ratio`
  - `age_chol_interaction`
- Main input features:
  - age
  - sex
  - chest pain type
  - resting blood pressure
  - cholesterol
  - fasting blood sugar
  - resting ECG
  - maximum heart rate
  - exercise induced angina
  - ST depression
  - slope
  - major vessels
  - thalassemia
  - engineered blood pressure/cholesterol ratio
  - engineered age/cholesterol interaction
- Safety limits used during cleaning and validation:
  - Age: 18 to 100 years
  - Resting blood pressure: 80 to 200 mmHg
  - Cholesterol: 100 to 400 mg/dL
  - Maximum heart rate: 60 to 220 bpm
  - ST depression: 0 to 10
- Application features:
  - Patient registration and login
  - Prediction form
  - Risk result page with calibrated probability
  - Prediction history
  - Report view
  - Doctor dashboard and patient detail views
  - Admin dashboard, users, doctors, patients, predictions
  - EDA/model visualization pages
  - Retrieval-based chatbot using local knowledge files
  - Optional hosted LLM synthesis if API key is configured
- Important disclaimer:
  HeartCareAI is a screening support and educational research application. It is not a medical device and must not replace clinical diagnosis or a qualified healthcare professional.

## Tone and Originality Requirements

Write the paper in original academic language. Do not plagiarize from:

- IEEE template sample text
- README files
- online heart disease prediction papers
- generic ML project descriptions

Use the project facts, but rewrite all explanations naturally. Prefer precise, modest claims. Avoid exaggerated claims such as "guaranteed diagnosis," "perfect medical accuracy," or "fully replaces doctors."

Because the reported model scores are extremely high, include a careful limitations paragraph explaining that future external validation, multi-site datasets, prospective testing, and bias analysis are needed before clinical deployment.

## Required Paper Structure

Create a polished IEEE conference paper of approximately 6 to 8 pages when compiled, using a two-column IEEE conference layout.

Use this structure:

1. Title
2. Abstract
3. Keywords
4. Introduction
5. Related Work
6. System Overview
7. Dataset and Preprocessing
8. Methodology
9. Implementation
10. Results and Evaluation
11. User Interface and Workflow
12. Ethical, Safety, and Clinical Considerations
13. Limitations
14. Future Work
15. Conclusion
16. References

## Suggested Title

Use one of these or create a stronger original title:

- HeartCareAI: A Web-Based Machine Learning System for Heart Disease Screening Support
- HeartCareAI: Integrating Calibrated Machine Learning and Role-Based Clinical Workflows for Cardiovascular Risk Screening
- Design and Evaluation of HeartCareAI, a Flask-Based Heart Disease Screening Support Platform

## Abstract Requirements

The abstract must be 150 to 250 words. It should summarize:

- The clinical motivation
- The application architecture
- The machine learning pipeline
- The evaluated models
- The best-performing model
- The web-based workflow
- The non-diagnostic nature of the system

Do not overclaim. Mention that the system supports screening and decision awareness, not diagnosis.

## Introduction Requirements

The introduction must:

- Explain why cardiovascular disease screening matters
- Describe the challenge of making ML models usable in real workflows
- Introduce HeartCareAI as a bridge between model training and application use
- Mention patient, doctor, and admin workflows
- State the paper contributions

Include a short contributions list:

- A Flask-based role-aware screening platform
- A validated ML pipeline with train/validation/test separation
- Calibrated probability output and threshold interpretation
- Integrated EDA and reporting views
- A retrieval-based chatbot for grounded application help

## Related Work Requirements

Discuss, in original words:

- Traditional cardiovascular risk assessment
- ML for heart disease prediction
- Explainability and calibration in clinical decision support
- Web-based clinical support tools
- The gap between notebook experiments and deployed screening workflows

Use citations. Do not invent fake citations. If exact sources are unavailable, use safe standard references and mark placeholders clearly for verification.

Recommended citation topics:

- WHO cardiovascular disease fact sheet or global CVD burden source
- UCI heart disease dataset or heart disease ML benchmark papers if relevant
- Scikit-learn documentation/paper
- XGBoost paper
- Random Forest paper
- Clinical decision support or model reporting guidance
- TRIPOD or CONSORT-AI style reporting guidance if appropriate

## System Overview Requirements

Describe the application architecture:

- Browser-based UI
- Flask route/controller layer
- Authentication and role-based access
- Prediction service
- Model artifact loading
- Schema validation
- Database persistence
- Report generation
- Chart/EDA module
- Chatbot retrieval module

Include an architecture figure. If no diagram screenshot exists, generate a clean figure in LaTeX using TikZ or include a created PNG diagram. The diagram should show:

User Interface -> Flask Application -> Prediction Service -> Model Bundle -> Database/Reports
and a side path for Chatbot -> Local Knowledge Base.

## Dataset and Preprocessing Requirements

Include:

- Dataset size before/after cleaning if available
- Final dataset size: 8,565 rows
- Feature count: 15 model features
- Balanced class distribution
- Train/validation/test split
- Feature validation ranges
- Outlier removal using IQR
- Engineered features
- Importance of schema consistency between training and live prediction

Add a table named "Dataset Summary" with:

- Total rows
- Features
- Training samples
- Validation samples
- Test samples
- No-disease records
- Disease records
- Class balance ratio

Add a table named "Clinical Input Validation Ranges" with:

- Age
- Resting blood pressure
- Cholesterol
- Maximum heart rate
- ST depression

## Methodology Requirements

Explain:

- Data cleaning
- Feature engineering
- Train/validation/test split
- Stratified cross-validation
- Models trained
- Hyperparameter tuning
- Model selection based on F1-score and validation behavior
- Probability calibration
- Threshold-based interpretation
- Artifact versioning

Include pseudocode or a compact algorithm block for the training and prediction workflow.

## Implementation Requirements

Describe:

- Flask app structure
- Model bundle loading
- Input validation
- Prediction persistence
- User authentication
- Doctor/admin panels
- Prediction report flow
- Chatbot retrieval design

Avoid dumping code. Explain implementation at system level.

## Results and Evaluation Requirements

Include a model comparison table:

| Model | Accuracy | Precision | Recall | F1-score | AUC-ROC | Validation Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Random Forest | 99.71 | 99.88 | 99.53 | 99.70 | 100.00 | 99.82 |
| XGBoost | 99.71 | 99.88 | 99.53 | 99.70 | 100.00 | 99.65 |
| SVM | 99.59 | 99.29 | 99.88 | 99.59 | 100.00 | 99.59 |
| Logistic Regression | 81.09 | 77.43 | 86.97 | 81.92 | 88.68 | 79.68 |

Include a confusion matrix description for the best model:

- True negatives: 868
- False positives: 1
- False negatives: 4
- True positives: 840

Include charts as figures if available:

- `model_comparison.png`
- `confusion_matrices.png`
- `roc_curves.png`
- `calibration_curve.png`
- `feature_importance.png`
- `heatmap.png`
- `target_dist.png`

Interpret results carefully. State that the high metrics are promising within the available dataset but require external validation.

## User Interface and Screenshot Requirements

Capture or include screenshots from the HeartCareAI app. Save all screenshots in `figures/screenshots/`.

Required screenshots:

1. Home or landing page
2. Login or registration page
3. Prediction input form
4. Prediction result page showing probability/risk interpretation
5. Prediction history page
6. Report view page
7. EDA/model visualization page
8. Chatbot page
9. Doctor dashboard or patient detail page
10. Admin dashboard or predictions page

Screenshot quality rules:

- Use clear browser screenshots, not phone photos
- Crop browser chrome only if needed
- Keep patient data fictional or anonymized
- Do not expose passwords, API keys, database files, or real personal details
- Use consistent viewport size, preferably 1440x900 or 1366x768
- Name files descriptively, such as `prediction_form.png`, `risk_result.png`, `doctor_dashboard.png`

In the paper, include 4 to 6 most important screenshots only. Put extra screenshots in the appendix or leave them in the ZIP.

Recommended UI figures:

- Figure: HeartCareAI prediction form
- Figure: Calibrated risk result and interpretation
- Figure: Doctor-facing patient review workflow
- Figure: Admin monitoring dashboard
- Figure: Chatbot support interface

## IEEE Template Screenshot Requirement

Use the provided IEEE template PDF screenshots only as formatting reference. Do not include screenshots of the IEEE sample paper in the final academic paper unless the assignment specifically asks for proof of template matching. If screenshots are included in the ZIP for reference, place them in `template_reference/` and do not cite them as research figures.

## Ethical and Safety Requirements

Add a dedicated section explaining:

- The system is a screening support tool, not a diagnostic authority
- Users should consult qualified clinicians
- Potential bias from dataset limitations
- Need for privacy protection and secure handling of health-related data
- Importance of explainability, calibration, and auditability
- Need for prospective validation before clinical deployment

## Limitations Requirements

Mention:

- Dataset may not represent all populations
- Very high performance can indicate dataset-specific patterns
- External hospital validation was not performed
- No real-time EHR integration
- The chatbot is informational and must not provide diagnosis
- The application needs stronger security review before production use

## Future Work Requirements

Include:

- External validation on multi-center datasets
- Stronger explainability using SHAP or similar approaches
- EHR/FHIR integration
- More robust calibration monitoring
- Audit logs and privacy hardening
- Clinician usability testing
- Deployment monitoring and model drift detection

## LaTeX Requirements

Use IEEE conference LaTeX style. The document should compile with `pdflatex` or `latexmk`.

Use packages only when necessary:

- `graphicx`
- `booktabs`
- `amsmath`
- `cite`
- `url`
- `hyperref` only if compatible with the IEEE format required by the assignment
- `tikz` only if generating an architecture diagram directly in LaTeX
- `algorithm` and `algorithmic` only if used cleanly

Formatting requirements:

- Two-column IEEE layout
- Proper title and author block
- IEEE-style section headings
- Numbered figures and tables
- All figures referenced in the text
- All tables referenced in the text
- Citations use IEEE numeric style
- No broken image paths
- No placeholder text such as "Lorem ipsum"
- No copied IEEE sample paragraphs
- No claims of clinical approval unless explicitly documented

## References Requirements

Create `references.bib` with credible references. Use BibTeX entries for:

- Random Forest original paper
- XGBoost paper
- Scikit-learn paper
- WHO cardiovascular disease source
- Clinical prediction model reporting guidance such as TRIPOD
- A heart disease ML/dataset reference if available
- Flask documentation or software citation if appropriate

If a citation is uncertain, add a comment in `references.bib` saying it must be verified before submission. Do not fabricate DOI values.

## Required ZIP Quality Checklist

Before finalizing the ZIP:

1. Compile `main.tex`.
2. Fix all LaTeX errors.
3. Confirm all figures appear correctly.
4. Confirm no text overlaps tables or figures.
5. Confirm references compile.
6. Confirm all images are inside the ZIP.
7. Confirm no real sensitive patient data is visible.
8. Confirm no API keys, passwords, database files, or model binaries are included.
9. Confirm the writing is original and not copied from the IEEE sample.
10. Include a short `README.md` explaining how to compile.

## Expected Final Output

Return one ZIP file named:

`HeartCareAI_IEEE_LaTeX_Paper.zip`

The ZIP should have this structure:

```text
HeartCareAI_IEEE_LaTeX_Paper/
  main.tex
  references.bib
  README.md
  figures/
    architecture.png
    model_comparison.png
    confusion_matrices.png
    roc_curves.png
    calibration_curve.png
    feature_importance.png
    screenshots/
      home.png
      prediction_form.png
      prediction_result.png
      prediction_history.png
      report_view.png
      eda_page.png
      chatbot.png
      doctor_dashboard.png
      admin_dashboard.png
  appendix/
    extra_screenshots.md
```

Now create the full LaTeX project with original academic writing, correct IEEE formatting, complete figures, careful medical disclaimers, and a professional README. Package everything into the requested ZIP.

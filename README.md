# HeartCare AI

HeartCare AI is a Flask-based heart disease screening application built around a production-style ML workflow. The current version promotes one calibrated model artifact, validates live inputs against the training schema, persists model version metadata with each prediction, and surfaces grounded help content through a retrieval-based chatbot.

## What changed

- Replaced hard voting with one promoted probability model.
- Added explicit train/validation/test separation.
- Added calibration and threshold tuning.
- Added versioned `model_bundle.joblib`, `metrics.json`, and `schema.json`.
- Reworked the screening UI around calibrated probability and threshold interpretation.
- Added a hybrid RAG chatbot with local retrieval and optional hosted LLM generation.

## Project layout

```text
healthcare_app/
├── app/
│   ├── services/
│   │   ├── chatbot.py
│   │   └── inference.py
│   ├── chatbot.py
│   ├── predict.py
│   ├── report.py
│   └── templates/
├── chatbot/
│   ├── knowledge/
│   ├── provider.py
│   └── retriever.py
├── training/
│   └── artifacts.py
├── utils/
│   ├── clinical.py
│   ├── feature_contract.py
│   └── modeling.py
├── models/
├── data/
├── tests/
├── run.py
└── train_models.py
```

## Setup

```bash
cd healthcare_app
pip install -r requirements.txt
python train_models.py
python run.py
```

The trainer writes:

- `models/model_bundle.joblib`
- `models/metrics.json`
- `models/schema.json`
- `data/summary.json`
- updated charts under `app/static/charts/`

## Default access

- Admin: `admin / admin@123`
- Doctors: `[email-prefix] / doctor@123`
- Patients: register through the app

## Chatbot

The chatbot always uses local retrieval from `chatbot/knowledge/`. If `OPENAI_API_KEY` is configured, it can optionally synthesize grounded answers with a hosted model. Without that key, it falls back to retrieval-only answers.

## Disclaimer

HeartCare AI is a screening support tool and research-style application. It is not a medical device and does not replace a qualified clinician.

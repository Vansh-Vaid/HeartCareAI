"""Main Blueprint – public-facing pages"""
import os, json
from flask import Blueprint, render_template, current_app
from flask_login import current_user

main_bp = Blueprint('main', __name__)

_APP_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR  = os.path.join(_APP_ROOT, 'data')
MODEL_DIR = os.path.join(_APP_ROOT, 'models')


def _load_summary():
    for path in [os.path.join(DATA_DIR, 'summary.json'), os.path.join(MODEL_DIR, 'metrics.json')]:
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                return json.load(f)
    return {}


_TOP4_MODELS = ("Logistic Regression", "Random Forest", "XGBoost", "Extra Trees")


def _filter_top4(model_results: dict) -> dict:
    """UI should only show the top 4 finalists (no ensemble/candidates)."""
    return {name: model_results[name] for name in _TOP4_MODELS if name in model_results}


@main_bp.route('/')
def index():
    summary = _load_summary()
    model_results = _filter_top4(summary.get('model_results', {}) or {})
    best_model    = summary.get('best_model', '')
    eda_shape     = summary.get('eda', {}).get('shape', [0, 0])
    return render_template('index.html',
                           model_results=model_results,
                           best_model=best_model,
                           eda_shape=eda_shape,
                           summary=summary)


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/eda')
def eda():
    summary = _load_summary()
    eda_data = summary.get('eda', {})
    return render_template('eda.html', eda=eda_data, summary=summary)


@main_bp.route('/models')
def models():
    summary = _load_summary()
    model_results = _filter_top4(summary.get('model_results', {}) or {})
    best_model    = summary.get('best_model', '')
    return render_template('models.html',
                           model_results=model_results,
                           best_model=best_model,
                           summary=summary)


@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

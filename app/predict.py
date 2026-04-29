"""Prediction Blueprint - single-model probability inference."""
from __future__ import annotations

import json
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from utils.clinical import PayloadValidationError
from utils.feature_contract import (
    FEATURE_ORDER,
    get_feature_form_groups,
    get_feature_labels,
)
from .extensions import db
from .models_db import Doctor, Patient, Prediction
from .services.inference import ModelNotReadyError, get_inference_service

predict_bp = Blueprint("predict", __name__, url_prefix="/predict")

FEATURE_LABELS = get_feature_labels()


def _get_model_metadata():
    service = get_inference_service()
    return service.metadata()


@predict_bp.route("/", methods=["GET"])
@login_required
def predict_form():
    try:
        metadata = _get_model_metadata()
    except ModelNotReadyError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("main.index"))

    doctors = Doctor.query.filter_by(available=True).all()
    return render_template(
        "predict/form.html",
        feature_groups=get_feature_form_groups(),
        feature_labels=FEATURE_LABELS,
        doctors=doctors,
        model_meta=metadata,
        show_chatbot=True,
        chatbot_page="predict",
    )


def _find_or_create_patient(patient_name: str, age: int, sex: int, doctor_id: str | None):
    patient_record = Patient.query.filter_by(name=patient_name).first()
    if patient_record:
        if doctor_id:
            patient_record.doctor_id = int(doctor_id)
        patient_record.age = age
        patient_record.sex = sex
        return patient_record

    patient_identifier = "P" + str(Patient.query.count() + 1000).zfill(4)
    patient_record = Patient(
        patient_id=patient_identifier,
        name=patient_name,
        age=age,
        sex=sex,
        user_id=current_user.id,
    )
    if doctor_id:
        patient_record.doctor_id = int(doctor_id)
    db.session.add(patient_record)
    db.session.flush()
    return patient_record


@predict_bp.route("/result", methods=["POST"])
@login_required
def predict_result():
    patient_name = request.form.get("patient_name", "Anonymous").strip() or "Anonymous"
    doctor_id = request.form.get("doctor_id") or None

    feature_payload = {feature: request.form.get(feature, "") for feature in FEATURE_ORDER}

    try:
        result = get_inference_service().predict_patient(feature_payload)
    except ModelNotReadyError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("main.index"))
    except PayloadValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("predict.predict_form"))

    patient_record = _find_or_create_patient(
        patient_name=patient_name,
        age=int(result["input"]["age"]),
        sex=int(result["input"]["sex"]),
        doctor_id=doctor_id,
    )

    prediction_record = Prediction(
        patient_id=patient_record.id,
        patient_name=patient_name,
        input_data=json.dumps(result["input"]),
        model_results=json.dumps(
            {
                "selected_model_name": result["selected_model_name"],
                "model_version": result["model_version"],
                "threshold": result["threshold"],
                "probability": result["probability"],
            }
        ),
        final_prediction=result["prediction"],
        risk_level=result["risk_level"],
        confidence=round(result["probability"] * 100, 2),
        risk_probability=result["probability"],
        threshold_used=result["threshold"],
        model_version=result["model_version"],
        model_name=result["selected_model_name"],
        confidence_label=result["confidence_level"],
        explanation_json=json.dumps(result["explanation"]),
        input_audit=json.dumps(result["input_audit"]),
        created_by=current_user.id,
    )
    db.session.add(prediction_record)
    db.session.commit()

    assigned_doctor = None
    if patient_record.doctor_id:
        assigned_doctor = Doctor.query.get(patient_record.doctor_id)

    return render_template(
        "predict/result.html",
        prediction=result,
        patient_name=patient_name,
        patient_age=int(result["input"]["age"]),
        patient_sex=int(result["input"]["sex"]),
        assigned_doctor=assigned_doctor,
        prediction_id=prediction_record.id,
        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        feature_labels=FEATURE_LABELS,
        show_chatbot=True,
        chatbot_page="result",
    )


@predict_bp.route("/history")
@login_required
def history():
    predictions = (
        Prediction.query.filter_by(created_by=current_user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return render_template("predict/history.html", predictions=predictions)

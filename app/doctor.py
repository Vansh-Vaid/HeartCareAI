"""Doctor Blueprint"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from .extensions import db
from .models_db import Doctor, Patient, Prediction

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')


def doctor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'doctor'):
            flash('Doctor access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@doctor_bp.route('/profile')
@login_required
@doctor_required
def profile():
    if current_user.role == 'admin':
        doctors = Doctor.query.all()
        return render_template('doctor/all_doctors.html', doctors=doctors)
    doc = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doc:
        flash('Doctor profile not found.', 'warning')
        return redirect(url_for('main.index'))
    patients = Patient.query.filter_by(doctor_id=doc.id).all()
    return render_template('doctor/profile.html', doc=doc, patients=patients)


@doctor_bp.route('/patients')
@login_required
@doctor_required
def my_patients():
    if current_user.role == 'admin':
        patients = Patient.query.all()
    else:
        doc = Doctor.query.filter_by(user_id=current_user.id).first()
        patients = Patient.query.filter_by(doctor_id=doc.id).all() if doc else []
    return render_template('doctor/patients.html', patients=patients)


@doctor_bp.route('/patient/<int:pat_id>')
@login_required
@doctor_required
def patient_detail(pat_id):
    patient = Patient.query.get_or_404(pat_id)
    predictions = Prediction.query.filter_by(patient_id=pat_id)\
                            .order_by(Prediction.created_at.desc()).all()
    return render_template('doctor/patient_detail.html',
                           patient=patient, predictions=predictions)


@doctor_bp.route('/all')
def all_doctors():
    doctors = Doctor.query.filter_by(available=True).all()
    return render_template('doctor/all_doctors.html', doctors=doctors)

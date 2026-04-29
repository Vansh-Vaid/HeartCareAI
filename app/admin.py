"""Admin Blueprint"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from .extensions import db
from .models_db import User, Doctor, Patient, Prediction

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_patients = Patient.query.count()
    total_doctors  = Doctor.query.count()
    total_users    = User.query.count()
    total_preds    = Prediction.query.count()
    recent_preds   = Prediction.query.order_by(Prediction.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html',
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           total_users=total_users,
                           total_preds=total_preds,
                           recent_preds=recent_preds)


@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors():
    docs = Doctor.query.all()
    return render_template('admin/doctors.html', doctors=docs)


@admin_bp.route('/doctors/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_doctor():
    if request.method == 'POST':
        name   = request.form['name']
        email  = request.form['email']
        spec   = request.form['specialization']
        phone  = request.form.get('phone', '')
        exp    = int(request.form.get('experience', 0))
        hosp   = request.form.get('hospital', '')
        bio    = request.form.get('bio', '')
        pwd    = request.form.get('password', 'doctor@123')

        uname = email.split('@')[0]
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
        else:
            user = User(username=uname, email=email, full_name=name,
                        password=generate_password_hash(pwd), role='doctor')
            db.session.add(user)
            db.session.flush()

            import uuid
            did = 'D' + str(Doctor.query.count() + 100).zfill(3)
            doc = Doctor(doctor_id=did, name=name, specialization=spec,
                         email=email, phone=phone, experience=exp,
                         hospital=hosp, bio=bio, user_id=user.id)
            db.session.add(doc)
            db.session.commit()
            flash(f'Doctor {name} created. Login: {uname} / {pwd}', 'success')
            return redirect(url_for('admin.doctors'))
    return render_template('admin/create_doctor.html')


@admin_bp.route('/doctors/edit/<int:doc_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(doc_id):
    doc = Doctor.query.get_or_404(doc_id)
    if request.method == 'POST':
        doc.name           = request.form['name']
        doc.specialization = request.form['specialization']
        doc.phone          = request.form.get('phone', doc.phone)
        doc.experience     = int(request.form.get('experience', doc.experience))
        doc.hospital       = request.form.get('hospital', doc.hospital)
        doc.bio            = request.form.get('bio', doc.bio)
        doc.available      = request.form.get('available') == 'on'
        if request.form.get('new_password'):
            doc.user.password = generate_password_hash(request.form['new_password'])
        db.session.commit()
        flash('Doctor profile updated.', 'success')
        return redirect(url_for('admin.doctors'))
    return render_template('admin/edit_doctor.html', doc=doc)


@admin_bp.route('/patients')
@login_required
@admin_required
def patients():
    pts = Patient.query.order_by(Patient.created_at.desc()).all()
    docs = Doctor.query.all()
    return render_template('admin/patients.html', patients=pts, doctors=docs)


@admin_bp.route('/patients/assign/<int:pat_id>', methods=['POST'])
@login_required
@admin_required
def assign_doctor(pat_id):
    patient = Patient.query.get_or_404(pat_id)
    patient.doctor_id = int(request.form['doctor_id'])
    db.session.commit()
    flash('Doctor assigned successfully.', 'success')
    return redirect(url_for('admin.patients'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/predictions')
@login_required
@admin_required
def all_predictions():
    preds = Prediction.query.order_by(Prediction.created_at.desc()).all()
    return render_template('admin/predictions.html', predictions=preds)


@admin_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_pw = request.form.get('new_password', 'Welcome@123')
    user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash(f'Password reset for {user.username}.', 'success')
    return redirect(url_for('admin.users'))

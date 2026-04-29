"""Database Models"""
from datetime import datetime
from flask_login import UserMixin
from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    full_name  = db.Column(db.String(120), default='')
    role       = db.Column(db.String(20),  default='patient')   # admin | doctor | patient
    is_active  = db.Column(db.Boolean,     default=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    doctor  = db.relationship('Doctor',  backref='user', uselist=False)
    patient = db.relationship('Patient', backref='user', uselist=False)


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id             = db.Column(db.Integer, primary_key=True)
    doctor_id      = db.Column(db.String(20), unique=True, nullable=False)
    name           = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(80),  default='')
    email          = db.Column(db.String(120), unique=True, nullable=False)
    phone          = db.Column(db.String(30),  default='')
    experience     = db.Column(db.Integer,     default=0)
    hospital       = db.Column(db.String(120), default='')
    bio            = db.Column(db.Text,        default='')
    available      = db.Column(db.Boolean,     default=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    patients       = db.relationship('Patient', backref='doctor', lazy=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class Patient(db.Model):
    __tablename__ = 'patients'
    id            = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.String(20), unique=True, nullable=False)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), default='')
    age           = db.Column(db.Integer, default=0)
    sex           = db.Column(db.Integer, default=0)
    phone         = db.Column(db.String(30), default='')
    address       = db.Column(db.Text, default='')
    doctor_id     = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    predictions   = db.relationship('Prediction', backref='patient', lazy=True)


class Prediction(db.Model):
    __tablename__ = 'predictions'
    id               = db.Column(db.Integer, primary_key=True)
    patient_id       = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    patient_name     = db.Column(db.String(120), default='Anonymous')
    input_data       = db.Column(db.Text,  default='{}')   # JSON
    model_results    = db.Column(db.Text,  default='{}')   # JSON
    final_prediction = db.Column(db.Integer, default=0)
    risk_level       = db.Column(db.String(30), default='Unknown')
    confidence       = db.Column(db.Float, default=0.0)
    risk_probability = db.Column(db.Float, default=0.0)
    threshold_used   = db.Column(db.Float, default=0.5)
    model_version    = db.Column(db.String(64), default='')
    model_name       = db.Column(db.String(80), default='')
    confidence_label = db.Column(db.String(30), default='')
    explanation_json = db.Column(db.Text, default='{}')
    input_audit      = db.Column(db.Text, default='[]')
    report_file      = db.Column(db.String(255), default='')
    created_by       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

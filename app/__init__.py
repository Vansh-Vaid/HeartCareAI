"""
Healthcare Risk Prediction – Flask Application
Main app entry point using Blueprints
"""
import os
from flask import Flask
from flask_login import LoginManager
from sqlalchemy import inspect, text
from .extensions import db
from .auth import auth_bp
from .main import main_bp
from .admin import admin_bp
from .doctor import doctor_bp
from .chatbot import chatbot_bp
from .predict import predict_bp
from .report import report_bp
from .models_db import User


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config['SECRET_KEY']           = os.environ.get('SECRET_KEY', 'dev-only-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///' + os.path.join(app.instance_path, 'healthcare.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'reports')

    os.makedirs(app.instance_path,       exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    login_mgr = LoginManager(app)
    login_mgr.login_view = 'auth.login'
    login_mgr.login_message = 'Please login to access this page.'
    login_mgr.login_message_category = 'info'

    @login_mgr.user_loader
    def load_user(uid):
        return User.query.get(int(uid))

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(report_bp)

    with app.app_context():
        db.create_all()
        _apply_runtime_migrations()
        _seed_data()

    return app


def _apply_runtime_migrations():
    inspector = inspect(db.engine)
    if 'predictions' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('predictions')}
    pending_columns = {
        'risk_probability': 'FLOAT DEFAULT 0.0',
        'threshold_used': 'FLOAT DEFAULT 0.5',
        'model_version': "VARCHAR(64) DEFAULT ''",
        'model_name': "VARCHAR(80) DEFAULT ''",
        'confidence_label': "VARCHAR(30) DEFAULT ''",
        'explanation_json': "TEXT DEFAULT '{}'",
        'input_audit': "TEXT DEFAULT '[]'",
    }

    with db.engine.begin() as connection:
        for column_name, sql_type in pending_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE predictions ADD COLUMN {column_name} {sql_type}"))


def _seed_data():
    """Seed admin, doctors and demo patient if not already present."""
    from .models_db import User, Doctor, Patient
    from werkzeug.security import generate_password_hash
    import csv, os, json

    # Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@heartcare.com',
                     password=generate_password_hash('admin@123'),
                     role='admin', full_name='System Administrator',
                     is_active=True)
        db.session.add(admin)

    # Load doctor CSV
    # data dir is healthcare_app/data (two levels up from this file's dir)
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    doctors_csv = os.path.join(_root, 'data', 'doctors.csv')
    if os.path.exists(doctors_csv):
        with open(doctors_csv) as f:
            for row in csv.DictReader(f):
                if not Doctor.query.filter_by(doctor_id=row['doctor_id']).first():
                    # Create login user
                    email = row['email']
                    uname = email.split('@')[0]
                    user = User.query.filter_by(username=uname).first()
                    if not user:
                        user = User(username=uname, email=email,
                                    password=generate_password_hash('doctor@123'),
                                    role='doctor', full_name=row['name'],
                                    is_active=True)
                        db.session.add(user)
                        db.session.flush()

                    doc = Doctor(
                        doctor_id=row['doctor_id'],
                        name=row['name'],
                        specialization=row['specialization'],
                        email=email,
                        phone=row.get('phone', ''),
                        experience=int(row.get('experience', 0)),
                        hospital=row.get('hospital', ''),
                        bio=row.get('bio', ''),
                        available=row.get('available', 'True') == 'True',
                        user_id=user.id,
                    )
                    db.session.add(doc)

    db.session.commit()

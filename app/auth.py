"""Authentication Blueprint"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db
from .models_db import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password) and user.is_active:
            login_user(user, remember=request.form.get('remember'))
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            nxt = request.args.get('next')
            if user.role == 'admin':
                return redirect(nxt or url_for('admin.dashboard'))
            if user.role == 'doctor':
                return redirect(nxt or url_for('doctor.profile'))
            return redirect(nxt or url_for('main.index'))
        flash('Invalid credentials or account inactive.', 'danger')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
        else:
            user = User(username=username, email=email, full_name=full_name,
                        password=generate_password_hash(password), role='patient')
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old = request.form.get('old_password', '')
        new = request.form.get('new_password', '')
        if check_password_hash(current_user.password, old):
            current_user.password = generate_password_hash(new)
            db.session.commit()
            flash('Password updated successfully.', 'success')
        else:
            flash('Old password is incorrect.', 'danger')
    return render_template('change_password.html')

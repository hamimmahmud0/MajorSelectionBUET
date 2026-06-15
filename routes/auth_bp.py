import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Student
from config import Config

auth_bp = Blueprint('auth', __name__)

# Compiled regex: exactly 7 digits
_STUDENT_ID_REGEX = re.compile(r'^\d{7}$')


def _validate_student_id(student_id):
    """Validate student ID format and prefix. Returns (is_valid, error_message)."""
    if not student_id:
        return False, 'Please enter your Student ID.'

    if not _STUDENT_ID_REGEX.match(student_id):
        prefix = Config.STUDENT_ID_PREFIX
        return False, f'Invalid Student ID format. Must be exactly 7 digits (e.g., {prefix}XXX).'

    if not student_id.startswith(Config.STUDENT_ID_PREFIX):
        prefix = Config.STUDENT_ID_PREFIX
        return False, f'Invalid Student ID. All IDs must start with <strong>{prefix}</strong>.'

    return True, ''


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Two-step login:
       Step 1: Enter Student ID.
       Step 2: Enter password (existing user) or create password (new user).
    """
    if current_user.is_authenticated:
        logout_user()

    # ─── Step 2: password was submitted ───
    if request.method == 'POST' and request.form.get('password', '').strip():
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '').strip()

        is_valid, error_msg = _validate_student_id(student_id)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('login.html')

        student = Student.query.get(student_id)

        if not student or student.has_default_password():
            # New or pending merit-list student — create account password
            if len(password) < 4:
                flash('Password must be at least 4 characters.', 'error')
                return render_template('login.html', student_id=student_id, is_new=True)
            if password == student_id:
                flash('Please choose a password different from your Student ID.', 'error')
                return render_template('login.html', student_id=student_id, is_new=True)

            if not student:
                student = Student(id=student_id)
                db.session.add(student)
            student.set_password(password)
            student.registered = True
            db.session.commit()
            login_user(student)
            flash('Account created successfully! Welcome.', 'success')
            return redirect(url_for('dashboard.index'))

        else:
            # Existing student — authenticate
            if student.check_password(password):
                login_user(student)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                flash('Incorrect password. Please try again.', 'error')
                return render_template('login.html', student_id=student_id, is_existing=True)

    # ─── Step 1: Student ID submitted (or fresh GET) ───
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()

        # Validate format
        is_valid, error_msg = _validate_student_id(student_id)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('login.html')

        student = Student.query.get(student_id)

        if student and student.is_registered():
            # Existing registered user → go to step 2 (password entry)
            return render_template('login.html', student_id=student_id, is_existing=True)
        else:
            # New or pending merit-list user → go to step 2 (create password)
            return render_template('login.html', student_id=student_id, is_new=True)

    # Fresh GET — show step 1
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

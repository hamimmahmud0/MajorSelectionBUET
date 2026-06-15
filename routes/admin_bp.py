import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Admin, Student, Supervisor, ComboSeat, StudentPref, Allocation
from services.allocator import try_run_allocation, get_submission_stats, has_allocation_run, clear_allocation_run

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin access."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin/login.html')


@admin_bp.route('/')
@admin_required
def dashboard():
    sub_stats = get_submission_stats()
    from services.allocator import is_allocation_on_cooldown, seconds_since_last_allocation, \
        ALLOCATION_COOLDOWN, last_allocation_time
    on_cooldown = is_allocation_on_cooldown()

    allocation_has_run = has_allocation_run()
    unallocated_students = []
    if allocation_has_run:
        allocated_ids = {a.student_id for a in Allocation.query.with_entities(Allocation.student_id).all()}
        submitted_ids = {row.student_id for row in db.session.query(StudentPref.student_id).distinct().all()}
        unallocated_ids = submitted_ids - allocated_ids
        unallocated_students = Student.query.filter(Student.id.in_(unallocated_ids)).order_by(Student.rank).all()

    stats = {
        'students': Student.query.count(),
        'supervisors': Supervisor.query.count(),
        'combos': ComboSeat.query.count(),
        'allocated': Allocation.query.count(),
        'submitted_prefs': sub_stats['submitted'],
        'total_ranked': sub_stats['total'],
        'remaining': sub_stats['remaining'],
        'threshold': sub_stats['threshold'],
        'can_run': sub_stats['can_run'],
        'allocation_has_run': allocation_has_run,
        'needed': max(0, sub_stats['threshold'] - sub_stats['submitted']),
        'cooldown_active': on_cooldown,
        'cooldown_remaining': round(ALLOCATION_COOLDOWN - seconds_since_last_allocation(), 1) if on_cooldown else 0,
        'cooldown_total': ALLOCATION_COOLDOWN,
        'unallocated_count': len(unallocated_students),
    }
    return render_template('admin/dashboard.html', stats=stats, unallocated_students=unallocated_students)


# ─── Supervisor Management (List One) ───

@admin_bp.route('/supervisors', methods=['GET', 'POST'])
@admin_required
def supervisors():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            major = request.form.get('major', '').strip().upper()
            seats = request.form.get('seats', 0, type=int)
            if name and major in ('S', 'T', 'E', 'G') and seats > 0:
                sup = Supervisor(name=name, major_code=major, seats=seats)
                db.session.add(sup)
                db.session.commit()
                flash('Supervisor added.', 'success')
            else:
                flash('Invalid input.', 'error')

        elif action == 'edit':
            sup_id = request.form.get('id', type=int)
            sup = Supervisor.query.get(sup_id)
            if sup:
                sup.name = request.form.get('name', sup.name).strip()
                sup.major_code = request.form.get('major', sup.major_code).strip().upper()
                sup.seats = request.form.get('seats', sup.seats, type=int)
                db.session.commit()
                flash('Supervisor updated.', 'success')

        elif action == 'delete':
            sup_id = request.form.get('id', type=int)
            sup = Supervisor.query.get(sup_id)
            if sup:
                db.session.delete(sup)
                db.session.commit()
                flash('Supervisor deleted.', 'success')

        elif action == 'import_csv':
            csv_file = request.files.get('csv_file')
            if csv_file:
                content = csv_file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(content))
                count = 0
                for row in reader:
                    name = row.get('name', '').strip()
                    major = row.get('major', '').strip().upper()
                    seats = int(row.get('seats', 0))
                    if name and major in ('S', 'T', 'E', 'G') and seats > 0:
                        sup = Supervisor(name=name, major_code=major, seats=seats)
                        db.session.add(sup)
                        count += 1
                db.session.commit()
                flash(f'Imported {count} supervisors.', 'success')

    supervisors = Supervisor.query.order_by(Supervisor.major_code, Supervisor.name).all()
    return render_template('admin/supervisors.html', supervisors=supervisors)


@admin_bp.route('/supervisors/export')
@admin_required
def export_supervisors():
    supervisors = Supervisor.query.order_by(Supervisor.major_code, Supervisor.name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'major', 'seats'])
    for s in supervisors:
        writer.writerow([s.name, s.major_code, s.seats])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=supervisors.csv'}
    )


# ─── Combo Seat Management (List Two) ───

@admin_bp.route('/combos', methods=['GET', 'POST'])
@admin_required
def combos():
    MAJORS = ['S', 'T', 'E', 'G']

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            major = request.form.get('major', '').strip().upper()
            minor = request.form.get('minor', '').strip().upper()
            seats = request.form.get('seats', 0, type=int)
            if major in MAJORS and minor in MAJORS and major != minor and seats > 0:
                existing = ComboSeat.query.filter_by(major_code=major, minor_code=minor).first()
                if existing:
                    flash('This combo already exists.', 'error')
                else:
                    cs = ComboSeat(major_code=major, minor_code=minor, seats=seats)
                    db.session.add(cs)
                    db.session.commit()
                    flash('Combo seat added.', 'success')
            else:
                flash('Invalid input. Major and minor must differ.', 'error')

        elif action == 'edit':
            cs_id = request.form.get('id', type=int)
            cs = ComboSeat.query.get(cs_id)
            if cs:
                cs.major_code = request.form.get('major', cs.major_code).strip().upper()
                cs.minor_code = request.form.get('minor', cs.minor_code).strip().upper()
                cs.seats = request.form.get('seats', cs.seats, type=int)
                db.session.commit()
                flash('Combo seat updated.', 'success')

        elif action == 'delete':
            cs_id = request.form.get('id', type=int)
            cs = ComboSeat.query.get(cs_id)
            if cs:
                db.session.delete(cs)
                db.session.commit()
                flash('Combo seat deleted.', 'success')

        elif action == 'import_csv':
            csv_file = request.files.get('csv_file')
            if csv_file:
                content = csv_file.read().decode('utf-8')
                for line in content.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) == 2:
                        code = parts[0].strip().upper()
                        seats = int(parts[1].strip())
                        if len(code) == 2 and seats > 0:
                            major, minor = code[0], code[1]
                            if major in MAJORS and minor in MAJORS and major != minor:
                                existing = ComboSeat.query.filter_by(major_code=major, minor_code=minor).first()
                                if not existing:
                                    cs = ComboSeat(major_code=major, minor_code=minor, seats=seats)
                                    db.session.add(cs)
                db.session.commit()
                flash('Combos imported from CSV.', 'success')

    combos = ComboSeat.query.order_by(ComboSeat.major_code, ComboSeat.minor_code).all()
    return render_template('admin/combos.html', combos=combos, majors=MAJORS)


@admin_bp.route('/combos/export')
@admin_required
def export_combos():
    combos = ComboSeat.query.order_by(ComboSeat.major_code, ComboSeat.minor_code).all()
    output = io.StringIO()
    for c in combos:
        output.write(f"{c.major_code}{c.minor_code},{c.seats}\n")
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=combos.csv'}
    )


# ─── Merit List Management (List Three) ───

@admin_bp.route('/merit', methods=['GET', 'POST'])
@admin_required
def merit():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload_csv':
            csv_file = request.files.get('csv_file')
            if csv_file:
                content = csv_file.read().decode('utf-8')
                # Reset all ranks
                Student.query.update({Student.rank: None})
                db.session.commit()

                count = 0
                for line in content.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) == 2:
                        rank = int(parts[0].strip())
                        student_id = parts[1].strip()
                        student = Student.query.get(student_id)
                        if not student:
                            student = Student(id=student_id)
                            student.set_password(student_id)  # default password = student_id
                            db.session.add(student)
                        student.rank = rank
                        count += 1
                db.session.commit()
                flash(f'Imported {count} students with ranks.', 'success')

        elif action == 'add':
            student_id = request.form.get('student_id', '').strip()
            rank = request.form.get('rank', 0, type=int)
            if student_id and rank > 0:
                student = Student.query.get(student_id)
                if not student:
                    student = Student(id=student_id)
                    student.set_password(student_id)
                    db.session.add(student)
                student.rank = rank
                db.session.commit()
                flash(f'Student {student_id} added with rank {rank}.', 'success')

        elif action == 'delete':
            student_id = request.form.get('student_id', '').strip()
            student = Student.query.get(student_id)
            if student:
                student.rank = None
                db.session.commit()
                flash(f'Student {student_id} removed from merit list.', 'success')

        elif action == 'clear_all':
            Student.query.update({Student.rank: None})
            db.session.commit()
            flash('All ranks cleared.', 'success')

    students = Student.query.order_by(Student.rank).all()
    return render_template('admin/merit.html', students=students)


@admin_bp.route('/merit/export')
@admin_required
def export_merit():
    students = Student.query.filter(Student.rank.isnot(None)).order_by(Student.rank).all()
    output = io.StringIO()
    for s in students:
        output.write(f"{s.rank},{s.id}\n")
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=merit_list.csv'}
    )


# ─── Students Management ───

@admin_bp.route('/students')
@admin_required
def students():
    all_students = Student.query.order_by(Student.id).all()
    return render_template('admin/students.html', students=all_students)


@admin_bp.route('/students/reset-password', methods=['POST'])
@admin_required
def reset_student_password():
    student_id = request.form.get('student_id', '').strip()
    new_password = request.form.get('new_password', '').strip()
    student = Student.query.get(student_id)
    if student and new_password:
        student.set_password(new_password)
        db.session.commit()
        flash(f'Password for {student_id} reset.', 'success')
    else:
        flash('Invalid input.', 'error')
    return redirect(url_for('admin.students'))


# ─── Allocation ───

@admin_bp.route('/run-allocation', methods=['POST'])
@admin_required
def trigger_allocation():
    try:
        result = try_run_allocation()
        if result.get('reason') == 'cooldown':
            flash(result['message'], 'info')
        elif result.get('success'):
            flash(result['message'], 'success')
        elif result.get('reason') == 'threshold':
            flash(result['message'], 'error')
        else:
            flash(result.get('message', 'Allocation could not be completed.'), 'error')
    except Exception as e:
        flash(f'Allocation error: {str(e)}', 'error')
    return redirect(url_for('admin.dashboard'))


# ─── Generate Demo Preferences ───

@admin_bp.route('/generate-demo-prefs', methods=['POST'])
@admin_required
def generate_demo_prefs():
    """Generate demo combo & supervisor preferences for all ranked students."""
    try:
        from models import StudentPref
        import random
        random.seed(42)

        students = Student.query.filter(Student.rank.isnot(None)).order_by(Student.rank).all()
        combos = list(ComboSeat.query.all())
        all_supervisors = list(Supervisor.query.all())

        if not combos or not all_supervisors:
            flash('Combos and supervisors required. Import them first.', 'error')
            return redirect(url_for('admin.dashboard'))

        # Clear existing preferences and stale allocation results
        StudentPref.query.delete()
        Allocation.query.delete()
        clear_allocation_run()
        db.session.commit()

        SKIP_COUNT = 15
        total = len(students)
        skip_indices = set(random.sample(range(total), min(SKIP_COUNT, total)))
        submitted_count = 0
        PREF_COUNT_WEIGHTS = [20, 15, 15, 12, 10, 8, 6, 4, 3]  # number of pairs each student ranks

        for idx, student in enumerate(students):
            if idx in skip_indices:
                continue

            # Generate a random number of preference pairs for this student
            num_prefs = random.choices(PREF_COUNT_WEIGHTS, k=1)[0]
            num_prefs = min(num_prefs, len(combos) * len(all_supervisors))

            # Create pairs by randomly picking combos and supervisors that match the combo's major
            prefs_set = set()
            for _ in range(num_prefs * 3):  # generate enough to fill
                combo = random.choice(combos)
                # Pick a supervisor from the combo's major
                matching_sups = [s for s in all_supervisors if s.major_code == combo.major_code]
                if not matching_sups:
                    continue
                sup = random.choice(matching_sups)
                key = (combo.major_code, combo.minor_code, sup.id)
                prefs_set.add(key)
                if len(prefs_set) >= num_prefs:
                    break

            for priority, (major, minor, sup_id) in enumerate(prefs_set, 1):
                db.session.add(StudentPref(
                    student_id=student.id, major_code=major,
                    minor_code=minor, supervisor_id=sup_id, priority=priority,
                ))

            submitted_count += 1

        db.session.commit()
        flash(f'Demo prefs generated! {submitted_count}/{total} students have preferences. '
              f'{total - submitted_count} skipped (no prefs).', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('admin.dashboard'))


# ─── Reset All Preferences & Allocations ───

@admin_bp.route('/reset-all', methods=['POST'])
@admin_required
def reset_all():
    """Delete all student accounts (with preferences, allocations, and ranks)."""
    try:
        # Delete in order: child records first, then students
        StudentPref.query.delete()
        Allocation.query.delete()
        clear_allocation_run()
        Student.query.delete()
        db.session.commit()
        flash('All students, preferences, and allocations have been deleted.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('admin.dashboard'))


# ─── Admin Logout ───

@admin_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

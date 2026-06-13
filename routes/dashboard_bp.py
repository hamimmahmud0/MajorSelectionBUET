from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Student, Supervisor, ComboSeat, StudentComboPref, StudentSupervisorPref, Allocation
from services.allocator import get_submission_stats

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    # Current student's allocation
    allocation = Allocation.query.filter_by(student_id=current_user.id).first()

    # All combos from DB
    combos = ComboSeat.query.order_by(ComboSeat.major_code, ComboSeat.minor_code).all()

    # Supervisors grouped by major
    supervisors_by_major = {}
    for sup in Supervisor.query.order_by(Supervisor.major_code, Supervisor.name).all():
        supervisors_by_major.setdefault(sup.major_code, []).append(sup)

    # Current student's preferences
    combo_prefs = StudentComboPref.query.filter_by(student_id=current_user.id).order_by(StudentComboPref.priority).all()
    sup_prefs = StudentSupervisorPref.query.filter_by(student_id=current_user.id).order_by(StudentSupervisorPref.priority).all()
    pref_supervisor_ids = {p.supervisor_id for p in sup_prefs}

    # Submission stats
    sub_stats = get_submission_stats()

    # All allocations for results table
    all_allocations = (
        db.session.query(
            Allocation.student_id,
            Student.rank,
            Allocation.major_code,
            Allocation.minor_code,
            Allocation.supervisor_id,
            Supervisor.name.label('supervisor_name')
        )
        .join(Student, Allocation.student_id == Student.id)
        .outerjoin(Supervisor, Allocation.supervisor_id == Supervisor.id)
        .order_by(Allocation.student_id)
        .all()
    )

    return render_template('dashboard/index.html',
                           allocation=allocation,
                           combos=combos,
                           supervisors_by_major=supervisors_by_major,
                           combo_prefs=combo_prefs,
                           sup_prefs=sup_prefs,
                           pref_supervisor_ids=pref_supervisor_ids,
                           all_allocations=all_allocations,
                           sub_stats=sub_stats)

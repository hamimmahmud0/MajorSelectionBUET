from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Student, Supervisor, ComboSeat, StudentPref, Allocation
from services.allocator import get_submission_stats, get_available_options_for_student

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    # Current student's allocation
    allocation = Allocation.query.filter_by(student_id=current_user.id).first()

    # All combos from DB
    combos = ComboSeat.query.order_by(ComboSeat.major_code, ComboSeat.minor_code).all()

    # All supervisors (for the dropdown as JSON)
    all_supervisors_list = Supervisor.query.order_by(Supervisor.major_code, Supervisor.name).all()
    all_supervisors = [{'id': s.id, 'name': s.name, 'major_code': s.major_code, 'seats': s.seats} for s in all_supervisors_list]

    # Current student's combined preferences
    student_prefs = StudentPref.query.filter_by(student_id=current_user.id).order_by(StudentPref.priority).all()

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

    # Determine if this student submitted but wasn't allocated
    has_submitted = len(student_prefs) > 0
    unallocated = has_submitted and allocation is None

    # Available options for unallocated students
    available_options = []
    if unallocated:
        available_options = get_available_options_for_student(current_user.id)

    return render_template('dashboard/index.html',
                           allocation=allocation,
                           combos=combos,
                           all_supervisors=all_supervisors,
                           student_prefs=student_prefs,
                           all_allocations=all_allocations,
                           sub_stats=sub_stats,
                           has_submitted=has_submitted,
                           unallocated=unallocated,
                           available_options=available_options)

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Student, Supervisor, ComboSeat, StudentPref, Allocation
from services.allocator import try_run_allocation

api_bp = Blueprint('api', __name__)


@api_bp.route('/preferences/save', methods=['POST'])
@login_required
def save_preferences():
    """Save student's combined (combo + supervisor) preference list."""
    data = request.get_json()
    if not data or 'preferences' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    # Delete existing preferences
    StudentPref.query.filter_by(student_id=current_user.id).delete()

    # Insert new preferences (position in list = priority)
    for idx, item in enumerate(data['preferences']):
        pref = StudentPref(
            student_id=current_user.id,
            major_code=item['major'].upper(),
            minor_code=item['minor'].upper(),
            supervisor_id=item['supervisor_id'],
            priority=idx + 1,
        )
        db.session.add(pref)

    db.session.commit()
    alloc_result = try_run_allocation()
    msg = 'Preferences saved!'
    if alloc_result.get('reason') == 'cooldown':
        msg += f' Allocation will update in {alloc_result["cooldown_remaining"]}s (cooldown).'
    elif alloc_result.get('success'):
        msg += ' Allocation updated.'
    return jsonify({'success': True, 'message': msg})


@api_bp.route('/allocation/status')
@login_required
def allocation_status():
    """Get current student's allocation status as JSON."""
    allocation = Allocation.query.filter_by(student_id=current_user.id).first()
    if allocation:
        sup_name = allocation.supervisor.name if allocation.supervisor else 'Not assigned'
        return jsonify({
            'allocated': True,
            'major': allocation.major_code,
            'minor': allocation.minor_code,
            'supervisor': sup_name,
            'supervisor_id': allocation.supervisor_id,
        })
    return jsonify({'allocated': False})


@api_bp.route('/search')
def search():
    """Search students by ID or combo for the results table."""
    q = request.args.get('q', '').strip()
    filter_type = request.args.get('filter', 'student_id')  # student_id or combo

    query = (
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
    )

    if q:
        if filter_type == 'student_id':
            query = query.filter(Allocation.student_id.like(f'%{q}%'))
        elif filter_type == 'combo':
            query = query.filter(
                db.or_(
                    db.concat(Allocation.major_code, Allocation.minor_code).like(f'%{q}%'),
                    Allocation.major_code.like(f'%{q}%'),
                    Allocation.minor_code.like(f'%{q}%'),
                )
            )

    results = query.order_by(Allocation.student_id).limit(50).all()

    return jsonify([{
        'student_id': r.student_id,
        'rank': r.rank,
        'combo': f"{r.major_code}{r.minor_code}",
        'supervisor': r.supervisor_name or 'Not assigned',
    } for r in results])


@api_bp.route('/search/suggestions')
def search_suggestions():
    """Return search suggestions for autocomplete."""
    q = request.args.get('q', '').strip()
    filter_type = request.args.get('filter', 'student_id')

    if not q or len(q) < 1:
        return jsonify([])

    if filter_type == 'student_id':
        students = Student.query.filter(Student.id.like(f'{q}%')).limit(10).all()
        return jsonify([s.id for s in students])
    elif filter_type == 'combo':
        combos = ComboSeat.query.filter(
            db.or_(
                db.concat(ComboSeat.major_code, ComboSeat.minor_code).like(f'{q}%'),
            )
        ).limit(10).all()
        return jsonify([f"{c.major_code}{c.minor_code}" for c in combos])

    return jsonify([])

"""
Greedy rank-based allocation algorithm.

Each student ranks (combo + supervisor) pairs in priority order.
The algorithm iterates students by merit rank and assigns the first
available pair from their preference list.
"""

import time
from models import db, Student, Supervisor, ComboSeat, StudentPref, Allocation

# Minimum number of students who must submit preferences before allocation runs
MIN_PREFERENCE_THRESHOLD = 50

# Cooldown: only one allocation run every N seconds
ALLOCATION_COOLDOWN = 30

# Internal: tracks the last time allocation ran (Unix timestamp)
_last_allocation_time = 0.0


def last_allocation_time():
    return _last_allocation_time


def seconds_since_last_allocation():
    return time.time() - _last_allocation_time


def is_allocation_on_cooldown():
    return seconds_since_last_allocation() < ALLOCATION_COOLDOWN


def get_submission_stats():
    """Get stats about preference submissions."""
    total_students = Student.query.filter(Student.rank.isnot(None)).count()
    submitted = (
        db.session.query(StudentPref.student_id)
        .distinct()
        .count()
    )
    return {
        'total': total_students,
        'submitted': submitted,
        'remaining': total_students - submitted,
        'threshold': MIN_PREFERENCE_THRESHOLD,
        'can_run': submitted >= MIN_PREFERENCE_THRESHOLD,
    }


def try_run_allocation():
    global _last_allocation_time
    if is_allocation_on_cooldown():
        remaining = round(ALLOCATION_COOLDOWN - seconds_since_last_allocation(), 1)
        return {
            'ran': False, 'reason': 'cooldown',
            'message': f'Allocation on cooldown. Try again in {remaining}s.',
            'cooldown_remaining': remaining,
        }
    result = run_allocation()
    if result.get('success'):
        _last_allocation_time = time.time()
    return result


def run_allocation():
    stats = get_submission_stats()
    if not stats['can_run']:
        return {'ran': True, 'success': False, 'reason': 'threshold',
                'message': f"Not enough submissions. {stats['submitted']}/{stats['total']} submitted. Need {stats['threshold']}.",
                **stats}

    Allocation.query.delete()
    students = Student.query.filter(Student.rank.isnot(None)).order_by(Student.rank).all()
    if not students:
        return {'ran': True, 'success': False, 'reason': 'no_students', 'message': 'No ranked students.', **stats}

    combo_seats = {f"{c.major_code}{c.minor_code}": c.seats for c in ComboSeat.query.all()}
    supervisor_seats = {s.id: s.seats for s in Supervisor.query.all()}
    if not combo_seats:
        return {'ran': True, 'success': False, 'reason': 'no_combos', 'message': 'No combos configured.', **stats}

    allocated_count = 0
    for student in students:
        prefs = StudentPref.query.filter_by(student_id=student.id).order_by(StudentPref.priority).all()
        for pref in prefs:
            ck = f"{pref.major_code}{pref.minor_code}"
            if combo_seats.get(ck, 0) <= 0:
                continue
            if supervisor_seats.get(pref.supervisor_id, 0) <= 0:
                continue
            # Assign
            combo_seats[ck] -= 1
            supervisor_seats[pref.supervisor_id] -= 1
            db.session.add(Allocation(
                student_id=student.id, major_code=pref.major_code,
                minor_code=pref.minor_code, supervisor_id=pref.supervisor_id,
            ))
            allocated_count += 1
            break  # assigned one pair, move to next student

    db.session.commit()
    return {'ran': True, 'success': True, 'allocated': allocated_count,
            'total': stats['total'], 'submitted': stats['submitted'],
            'threshold': MIN_PREFERENCE_THRESHOLD, 'can_run': True,
            'message': f'Allocation complete! {allocated_count} students allocated.'}

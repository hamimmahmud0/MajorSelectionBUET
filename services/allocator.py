"""
Greedy rank-based allocation algorithm.

Algorithm:
1. Sort students by rank (ascending).
2. For each student, iterate their combo preferences in priority order.
3. For each combo, check if combo has remaining seats.
4. If yes, check the student's supervisor preference list for that combo's major.
5. First available supervisor with free seats → assign combo + supervisor.
6. If no combo works → student is unassigned.
7. For students with partial preferences (ranked only some combos),
   the remaining unranked combos are treated as equal-lowest priority.
"""

import time
from models import db, Student, Supervisor, ComboSeat, StudentComboPref, StudentSupervisorPref, Allocation

# Minimum number of students who must submit preferences before allocation runs
MIN_PREFERENCE_THRESHOLD = 50

# Cooldown: only one allocation run every N seconds
ALLOCATION_COOLDOWN = 30

# Internal: tracks the last time allocation ran (Unix timestamp)
_last_allocation_time = 0.0


def last_allocation_time():
    """Return the Unix timestamp of the last allocation run."""
    return _last_allocation_time


def seconds_since_last_allocation():
    """Return how many seconds since the last allocation ran."""
    return time.time() - _last_allocation_time


def is_allocation_on_cooldown():
    """Return True if allocation is still on cooldown."""
    return seconds_since_last_allocation() < ALLOCATION_COOLDOWN


def get_submission_stats():
    """Get stats about preference submissions. Returns dict."""
    total_students = Student.query.filter(Student.rank.isnot(None)).count()
    submitted = (
        db.session.query(StudentComboPref.student_id)
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
    """
    Attempt to run allocation, respecting cooldown and threshold.
    Returns dict with status info including whether allocation actually ran.
    """
    global _last_allocation_time

    # Check cooldown
    if is_allocation_on_cooldown():
        remaining = round(ALLOCATION_COOLDOWN - seconds_since_last_allocation(), 1)
        return {
            'ran': False,
            'reason': 'cooldown',
            'message': f'Allocation on cooldown. Try again in {remaining}s.',
            'cooldown_remaining': remaining,
        }

    # Run the allocation
    result = run_allocation()

    # Update timestamp only on success
    if result.get('success'):
        _last_allocation_time = time.time()

    return result


def run_allocation():
    """
    Run the full allocation algorithm and update the Allocation table.
    Returns dict with status info.
    Does NOT check cooldown — use try_run_allocation() for that.
    """
    stats = get_submission_stats()

    if not stats['can_run']:
        return {
            'ran': True,
            'success': False,
            'reason': 'threshold',
            'message': (
                f"Not enough submissions. "
                f"{stats['submitted']}/{stats['total']} students submitted preferences. "
                f"Need at least {stats['threshold']}."
            ),
            **stats,
        }

    # Clear previous allocations
    Allocation.query.delete()

    # Get ranked students
    students = Student.query.filter(Student.rank.isnot(None)).order_by(Student.rank).all()

    if not students:
        return {'ran': True, 'success': False, 'reason': 'no_students', 'message': 'No ranked students found.', **stats}

    # Get combo seats with a mutable counter
    combo_seats = {_combo_key(c): c.seats for c in ComboSeat.query.all()}
    # Get supervisor seats with a mutable counter
    supervisor_seats = {s.id: s.seats for s in Supervisor.query.all()}

    if not combo_seats:
        return {'ran': True, 'success': False, 'reason': 'no_combos', 'message': 'No combo seats configured.', **stats}

    # All possible combos (for default/equal-lowest priority)
    all_combos = list(combo_seats.keys())

    allocated_count = 0
    for student in students:
        assigned = _allocate_student(student, combo_seats, supervisor_seats, all_combos)

        if assigned:
            major_code, minor_code, supervisor_id = assigned
            alloc = Allocation(
                student_id=student.id,
                major_code=major_code,
                minor_code=minor_code,
                supervisor_id=supervisor_id,
            )
            db.session.add(alloc)
            allocated_count += 1

    db.session.commit()

    return {
        'ran': True,
        'success': True,
        'allocated': allocated_count,
        'total': stats['total'],
        'submitted': stats['submitted'],
        'threshold': MIN_PREFERENCE_THRESHOLD,
        'can_run': True,
        'message': f'Allocation complete! {allocated_count} students allocated.',
    }


def _combo_key(c):
    """Return a string key like 'ST' for a ComboSeat row or (major, minor) tuple."""
    if isinstance(c, tuple):
        return f"{c[0]}{c[1]}"
    return f"{c.major_code}{c.minor_code}"


def _allocate_student(student, combo_seats, supervisor_seats, all_combos):
    """
    Try to allocate a combo + supervisor to a student.
    Returns (major_code, minor_code, supervisor_id) or None.
    """
    # Get student's combo preferences (ordered by priority)
    combo_prefs = (
        StudentComboPref.query
        .filter_by(student_id=student.id)
        .order_by(StudentComboPref.priority)
        .all()
    )

    ranked_combos = [(p.major_code, p.minor_code) for p in combo_prefs]
    ranked_keys = [f"{m}{n}" for m, n in ranked_combos]

    # Unranked combos = all combos that student didn't rank
    unranked = [k for k in all_combos if k not in ranked_keys]
    # Sort unranked alphabetically for deterministic behavior
    unranked.sort()

    # Full preference list: ranked first (in priority order), then unranked
    full_preference = ranked_combos + [(k[0], k[1]) for k in unranked]

    for major_code, minor_code in full_preference:
        combo_key = f"{major_code}{minor_code}"

        # Check combo seat availability
        if combo_seats.get(combo_key, 0) <= 0:
            continue

        # Find available supervisor for this major
        sup_id = _find_available_supervisor(student.id, major_code, supervisor_seats)
        if sup_id is None:
            continue

        # Assign!
        combo_seats[combo_key] -= 1
        supervisor_seats[sup_id] -= 1
        return (major_code, minor_code, sup_id)

    return None


def _find_available_supervisor(student_id, major_code, supervisor_seats):
    """
    Find the first available supervisor for a given major
    based on the student's preferences.
    Returns supervisor_id or None.
    """
    # Get student's supervisor preferences for this major
    sup_prefs = (
        StudentSupervisorPref.query
        .filter_by(student_id=student_id, major_code=major_code)
        .order_by(StudentSupervisorPref.priority)
        .all()
    )

    pref_ids = [p.supervisor_id for p in sup_prefs]

    # Get all supervisors for this major
    all_sups = Supervisor.query.filter_by(major_code=major_code).all()
    all_sup_ids = [s.id for s in all_sups]

    # Ranked supervisors first, then unranked (sorted by ID for determinism)
    unranked = sorted([sid for sid in all_sup_ids if sid not in pref_ids])
    full_sup_pref = pref_ids + unranked

    for sup_id in full_sup_pref:
        if supervisor_seats.get(sup_id, 0) > 0:
            return sup_id

    return None

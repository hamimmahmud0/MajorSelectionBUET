"""
Generate demo preferences for all students in the merit list.
Some students are left without preferences to simulate real-world scenarios.

Usage:
    python sample_data/generate_demo_prefs.py

Requires: Flask app context (run via python -c or flask shell)
"""
import random
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from models import db, Student, Supervisor, ComboSeat, StudentComboPref, StudentSupervisorPref

# Seed for reproducibility
random.seed(42)

# How many students (out of ~196) should NOT submit any preferences
SKIP_COUNT = 15

# Probability ranges for how many combos a student ranks
# Some rank all 12, some rank only 3-6, etc.
COMBO_RANK_WEIGHTS = [
    (12, 0.20),   # 20% rank all 12
    (10, 0.15),   # 15% rank 10
    (8,  0.20),   # 20% rank 8
    (6,  0.20),   # 20% rank 6
    (4,  0.15),   # 15% rank 4
    (3,  0.10),   # 10% rank only 3
]


def generate_demo_preferences():
    app = create_app()
    with app.app_context():
        # Get all ranked students
        students = Student.query.filter(Student.rank.isnot(None)).order_by(Student.rank).all()
        total = len(students)

        if total == 0:
            print("No students found. Run the app first to import merit list.")
            return

        # Get all combos and supervisors
        combos = list(ComboSeat.query.all())
        supervisors = list(Supervisor.query.all())
        supervisors_by_major = {}
        for sup in supervisors:
            supervisors_by_major.setdefault(sup.major_code, []).append(sup)

        if not combos:
            print("No combos found. Import combos first.")
            return

        # Clear existing preferences
        StudentComboPref.query.delete()
        StudentSupervisorPref.query.delete()
        db.session.commit()

        # Pick students to skip
        skip_indices = set(random.sample(range(total), min(SKIP_COUNT, total)))
        submitted_count = 0

        for idx, student in enumerate(students):
            if idx in skip_indices:
                continue  # Skip this student — no preferences

            # ─── Combo preferences ───
            # Decide how many combos this student ranks
            how_many = random.choices(
                [w[0] for w in COMBO_RANK_WEIGHTS],
                weights=[w[1] for w in COMBO_RANK_WEIGHTS],
                k=1
            )[0]
            how_many = min(how_many, len(combos))

            ranked_combos = random.sample(combos, how_many)
            for priority, combo in enumerate(ranked_combos, 1):
                pref = StudentComboPref(
                    student_id=student.id,
                    major_code=combo.major_code,
                    minor_code=combo.minor_code,
                    priority=priority,
                )
                db.session.add(pref)

            # ─── Supervisor preferences per major ───
            # For each major that appears in this student's ranked combos
            majors_used = set(c.major_code for c in ranked_combos)
            for major_code in majors_used:
                sups = supervisors_by_major.get(major_code, [])
                if not sups:
                    continue
                # Rank a subset (or all) of the supervisors for this major
                rank_count = random.randint(1, len(sups))
                ranked_sups = random.sample(sups, rank_count)
                for priority, sup in enumerate(ranked_sups, 1):
                    pref = StudentSupervisorPref(
                        student_id=student.id,
                        supervisor_id=sup.id,
                        major_code=major_code,
                        priority=priority,
                    )
                    db.session.add(pref)

            submitted_count += 1

        db.session.commit()

        # Summary
        skipped = total - submitted_count
        total_prefs = StudentComboPref.query.count()
        total_sup_prefs = StudentSupervisorPref.query.count()
        print(f"✅ Demo preferences generated!")
        print(f"   Total students:         {total}")
        print(f"   With preferences:       {submitted_count}")
        print(f"   Skipped (no prefs):     {skipped}")
        print(f"   Total combo prefs:      {total_prefs}")
        print(f"   Total supervisor prefs: {total_sup_prefs}")
        print(f"   Average combos ranked:  {total_prefs / submitted_count:.1f}")


if __name__ == '__main__':
    generate_demo_preferences()

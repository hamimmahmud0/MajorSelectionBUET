import csv
import os
from pathlib import Path
from flask import Flask
from sqlalchemy import inspect, text
from config import Config
from models import db, Admin, Supervisor, ComboSeat, MigrationState
from flask_login import LoginManager

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from routes.auth_bp import auth_bp
    from routes.admin_bp import admin_bp
    from routes.dashboard_bp import dashboard_bp
    from routes.api_bp import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')

    # ─── Root route → dashboard or login ───
    @app.route('/')
    def root():
        from flask import redirect, url_for
        from flask_login import current_user
        from models import Admin
        if current_user.is_authenticated:
            if isinstance(current_user, Admin):
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    with app.app_context():
        db.create_all()
        _ensure_student_registration_state()
        _seed_admin(app)
        _seed_sample_data(app)

    return app


def _ensure_student_registration_state():
    """Keep old databases usable after adding explicit student registration state."""
    inspector = inspect(db.engine)
    columns = {column['name'] for column in inspector.get_columns('student')}
    if 'registered' not in columns:
        db.session.execute(text('ALTER TABLE student ADD COLUMN registered BOOLEAN NOT NULL DEFAULT 0'))
        db.session.commit()

    marker_key = 'student_registered_backfilled'
    if db.session.get(MigrationState, marker_key):
        return

    from models import Student
    for student in Student.query.all():
        student.registered = not student.has_default_password()

    db.session.add(MigrationState(key=marker_key))
    db.session.commit()


def _seed_admin(app):
    """Create default admin if not exists."""
    from config import Config
    admin = Admin.query.filter_by(username=Config.ADMIN_USERNAME).first()
    if not admin:
        admin = Admin(username=Config.ADMIN_USERNAME)
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()


def _seed_sample_data(app):
    """Load sample supervisors and combos from CSV files if tables are empty."""
    sample_dir = Path(__file__).resolve().parent / 'sample_data'

    # ─── Supervisors (List One) ───
    if Supervisor.query.count() == 0:
        csv_path = sample_dir / 'supervisors.csv'
        if csv_path.exists():
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    sup = Supervisor(
                        name=row['name'].strip(),
                        major_code=row['major'].strip().upper(),
                        seats=int(row['seats'])
                    )
                    db.session.add(sup)
                    count += 1
                db.session.commit()
            print(f'[seed] Loaded {count} supervisors from sample_data/supervisors.csv')
        else:
            print(f'[seed] sample_data/supervisors.csv not found, skipping.')

    # ─── Combos (List Two) ───
    if ComboSeat.query.count() == 0:
        csv_path = sample_dir / 'combos.csv'
        if csv_path.exists():
            with open(csv_path, newline='', encoding='utf-8') as f:
                count = 0
                for line in f:
                    line = line.strip()
                    if not line or ',' not in line:
                        continue
                    code, seats = line.split(',')
                    code = code.strip().upper()
                    if len(code) == 2:
                        cs = ComboSeat(
                            major_code=code[0],
                            minor_code=code[1],
                            seats=int(seats.strip())
                        )
                        db.session.add(cs)
                        count += 1
                db.session.commit()
            print(f'[seed] Loaded {count} combos from sample_data/combos.csv')
        else:
            print(f'[seed] sample_data/combos.csv not found, skipping.')


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID — checks both Student and Admin tables."""
    from models import Student
    from flask import current_app
    # Try student first
    student = db.session.get(Student, user_id)
    if student:
        return student
    # Try admin
    admin = db.session.get(Admin, int(user_id))
    return admin


# ─── Production-ready entry point ───
# For development:  python app.py
# For production:   gunicorn wsgi:app -w 4 -b 0.0.0.0:8000
#                   uvicorn wsgi:app --host 0.0.0.0 --port 8000 --workers 4

if __name__ == '__main__':
    app = create_app()
    import os
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

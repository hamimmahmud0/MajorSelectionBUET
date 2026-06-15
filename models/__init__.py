from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(UserMixin, db.Model):
    __tablename__ = 'student'
    id = db.Column(db.String(20), primary_key=True)  # e.g., 2104065
    password_hash = db.Column(db.String(256), nullable=False)
    rank = db.Column(db.Integer, nullable=True)
    registered = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    student_prefs = db.relationship('StudentPref', backref='student_obj', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_default_password(self):
        return self.check_password(self.id)

    def is_registered(self):
        return bool(self.registered)


class MigrationState(db.Model):
    __tablename__ = 'migration_state'
    key = db.Column(db.String(100), primary_key=True)
    applied_at = db.Column(db.DateTime, default=db.func.now())


class Supervisor(db.Model):
    __tablename__ = 'supervisor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    major_code = db.Column(db.String(1), nullable=False)  # S, T, E, G
    seats = db.Column(db.Integer, nullable=False, default=0)


class ComboSeat(db.Model):
    __tablename__ = 'combo_seat'
    id = db.Column(db.Integer, primary_key=True)
    major_code = db.Column(db.String(1), nullable=False)  # S, T, E, G
    minor_code = db.Column(db.String(1), nullable=False)  # S, T, E, G
    seats = db.Column(db.Integer, nullable=False, default=0)


class StudentComboPref(db.Model):
    __tablename__ = 'student_combo_pref'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'), nullable=False)
    major_code = db.Column(db.String(1), nullable=False)
    minor_code = db.Column(db.String(1), nullable=False)
    priority = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'major_code', 'minor_code', name='uq_student_combo'),
    )


class StudentSupervisorPref(db.Model):
    __tablename__ = 'student_supervisor_pref'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    major_code = db.Column(db.String(1), nullable=False)
    priority = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'supervisor_id', name='uq_student_supervisor'),
    )


class StudentPref(db.Model):
    """Combined preference: a student ranks a (combo + supervisor) pair."""
    __tablename__ = 'student_pref'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'), nullable=False)
    major_code = db.Column(db.String(1), nullable=False)
    minor_code = db.Column(db.String(1), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    priority = db.Column(db.Integer, nullable=False)

    supervisor = db.relationship('Supervisor', backref='student_prefs')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'major_code', 'minor_code', 'supervisor_id',
                            name='uq_student_pref'),
    )


class Allocation(db.Model):
    __tablename__ = 'allocation'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'), nullable=False)
    major_code = db.Column(db.String(1), nullable=False)
    minor_code = db.Column(db.String(1), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    student = db.relationship('Student', backref='allocation', uselist=False)
    supervisor = db.relationship('Supervisor', backref='allocations')


class AllocationRun(db.Model):
    """Singleton marker for the latest successful allocation run."""
    __tablename__ = 'allocation_run'
    id = db.Column(db.Integer, primary_key=True, default=1)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

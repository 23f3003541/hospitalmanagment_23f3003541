from .database import db
from datetime import datetime
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """Base user model for authentication"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    user_role = db.Column(db.Integer, nullable=False)  # 0=admin, 1=doctor, 2=patient
    
    # Relationships
    admin = db.relationship('Admin', backref='user', uselist=False)
    doctor = db.relationship('Doctor', backref='user', uselist=False)
    patient = db.relationship('Patient', backref='user', uselist=False)

    def get_id(self):
        return str(self.id)


class Admin(db.Model, UserMixin):
    """Admin/Hospital Staff model"""
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    passworda = db.Column(db.String(70), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def get_id(self):
        return str(self.admin_id)


class Department(db.Model):
    """Medical department/specialization"""
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Relationships
    doctors = db.relationship('Doctor', backref='department', lazy=True)

    @property
    def doctors_count(self):
        """Count of active (non-blacklisted) doctors"""
        return len([d for d in self.doctors if not d.is_blacklisted])


class Doctor(db.Model, UserMixin):
    """Doctor model"""
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passwordd = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact = db.Column(db.String(15))
    specialization = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    qualifications = db.Column(db.Text)
    is_blacklisted = db.Column(db.Boolean, default=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def get_id(self):
        return str(self.doctor_id)


class Patient(db.Model, UserMixin):
    """Patient model"""
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passwordp = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    contact = db.Column(db.String(15))  # Contact field added
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def get_id(self):
        return str(self.patient_id)


class Appointment(db.Model):
    """Appointment/booking between patient and doctor"""
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)  # Nullable for availability slots
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Patient name or 'Available' for slots
    date = db.Column(db.Date, nullable=False)
    st_time = db.Column(db.Time, nullable=False)
    en_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Booked')  # Booked, Completed, Cancelled, Available
    
    # Relationships
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, cascade='all, delete-orphan')

    @property
    def duration_minutes(self):
        """Calculate appointment duration in minutes"""
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.st_time)
        end = datetime.combine(datetime.today(), self.en_time)
        return int((end - start).total_seconds() / 60)


class Treatment(db.Model):
    """Treatment/medical record for completed appointments"""
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
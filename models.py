from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db=SQLAlchemy()
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    user_role = db.Column(db.Integer, nullable=False)  # 0 for admin, 1 for sponsor, 2 for influencer
    admin = db.relationship('Admin', backref='user')
    doctor = db.relationship('Doctor', backref='user')
    patient = db.relationship('Patient', backref='user')

    def get_id(self):
        return str(self.id)

class Admin(db.Model):
    __tablename__="admin"
    id=db.coloumn(db.integer,primary_ket=True)
    UserName=db.column(db.string(20),unique=True , nullable=False)
    passworda=db.column(db.string(70),nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Department(db.Model):
    __tablename__ = 'departments'
    name = db.Column(db.String(100), unique=True, nullable=False)
    doctors = db.relationship('Doctor', backref='department', lazy=True)
    description=db.column(db.text(100),nullable=False)

    @property
    def doctors_count(self):
        return len([d for d in self.doctors if not d.is_blacklisted])


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passwordd = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    qualifications = db.Column(db.Text)
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    passwordp = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


#class DoctorAvailability(db.Model):
    #__tablename__ = 'doctor_availability'
    #id = db.Column(db.Integer, primary_key=True)
    #doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    #date = db.Column(db.Date, nullable=False)
    #start_time = db.Column(db.Time, nullable=False)
    #end_time = db.Column(db.Time, nullable=False)
    #is_available = db.Column(db.Boolean, default=True)


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Booked')  # Booked, Completed, Cancelled
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, cascade='all, delete-orphan')


class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)

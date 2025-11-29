from flask import render_template, request, url_for, session, flash, abort, redirect, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from flask import current_app as app 
from datetime import datetime, date, time, timedelta 
from sqlalchemy import or_, and_
from .models import *
from .database import db


# COMMON ROUTES 


# home
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


# Login ROUTES and register 


# Logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))


# ERROR HANDLERS 
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', 
                         error_code=403, 
                         error_message='Forbidden - You do not have permission to access this resource'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Page Not Found'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', 
                         error_code=500, 
                         error_message='Internal Server Error'), 500


#  ADMIN ROUTES 
# admin login
@app.route('/admin_login', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        us_name = request.form.get('us_name')
        pwd = request.form.get('pwd')
        
        this_admin = Admin.query.filter_by(username=us_name).first()
        if not this_admin:
            return render_template('admin_login.html', error="No user found")
        if this_admin.passworda != pwd:
            return render_template('admin_login.html', error="Password wrong")
        
       
        user = User.query.get(this_admin.admin_id)
        login_user(user)
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_login.html')

# Admin Dashboard

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    # Verify admin role
    if current_user.user_role != 0:
        abort(403)
    
    # Core Func 1: Display  number of doctors, patients, and appointments
    total_doctors = Doctor.query.filter_by(is_blacklisted=False).count()
    total_patients = Patient.query.filter_by(is_blacklisted=False).count()
    total_appointments = Appointment.query.filter(Appointment.status != 'Available').count()
    pending_appointments = Appointment.query.filter_by(status='Booked').count()
    completed_appointments = Appointment.query.filter_by(status='Completed').count()
    total_departments = Department.query.count()
    
    departments = Department.query.all()
    doctors = Doctor.query.filter_by(is_blacklisted=False).all()
    
    #  department wise doctor count 
    dept_doctor_data = []
    for dept in departments:
        doctor_count = Doctor.query.filter_by(department_id=dept.id, is_blacklisted=False).count()
        dept_doctor_data.append({'name': dept.name, 'count': doctor_count})
    
    #  Appointment status distribution
    booked_count = Appointment.query.filter_by(status='Booked').count()
    completed_count = Appointment.query.filter_by(status='Completed').count()
    cancelled_count = Appointment.query.filter_by(status='Cancelled').count()
    status_data = [
        {'status': 'Booked', 'count': booked_count},
        {'status': 'Completed', 'count': completed_count},
        {'status': 'Cancelled', 'count': cancelled_count}
    ]
    
    # all upcoming and past appointments
    today = date.today()
    upcoming_appointments = Appointment.query.filter(
        Appointment.date >= today,
        Appointment.status != 'Available'
    ).order_by(Appointment.date.asc()).limit(10).all()
    
    past_appointments = Appointment.query.filter(
        Appointment.date < today,
        Appointment.status != 'Available'
    ).order_by(Appointment.date.desc()).limit(10).all()
    
    return render_template(
        'admin_dashboard.html',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        pending_appointments=pending_appointments,
        completed_appointments=completed_appointments,
        total_departments=total_departments,
        departments=departments,
        doctors=doctors,
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments,
        dept_doctor_data=dept_doctor_data,
        status_data=status_data
    )

# admin add dept

@app.route('/admin_add_department', methods=['GET', 'POST'])
@login_required
def admin_add_department():
    if current_user.user_role != 0:
        abort(403)
    
    if request.method == 'POST':
        dept_name = request.form.get('dept_name')
        dept_description = request.form.get('dept_description')
        
        if not dept_name or not dept_description:
            return render_template('admin_add_department.html', message="Both fields required")
        
        existing_dept = Department.query.filter_by(name=dept_name).first()
        if existing_dept:
            return render_template('admin_add_department.html', message="Department already exists")
        
        new_dept = Department(name=dept_name, description=dept_description)
        db.session.add(new_dept)
        db.session.commit()
        
        flash('Department added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_add_department.html')

# admin add doctor 

@app.route('/admin_add_doctor', methods=['GET', 'POST'])
@login_required
def admin_add_doctor():
    
    if current_user.user_role != 0:
        abort(403)
    
    departments = Department.query.all()
    
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        pwdd = request.form.get('pwdd')
        name1 = request.form.get('name1')
        email = request.form.get('email')
        specialization = request.form.get('specialization')
        department_id = request.form.get('department_id')
        qualifications = request.form.get('qualifications', '')
        contact = request.form.get('contact', '')
        
        if not (u_name and pwdd and name1 and email and specialization and department_id):
            return render_template('admin_add_doctor.html', 
                                 message="Fill all required fields", 
                                 departments=departments)
        
        # Check if username or email exists
        existing_user = User.query.filter_by(username=u_name).first()
        existing_doctor = Doctor.query.filter_by(email=email).first()
        
        if existing_user:
            return render_template('admin_add_doctor.html', 
                                 message='Username already exists', 
                                 departments=departments)
        if existing_doctor:
            return render_template('admin_add_doctor.html', 
                                 message='Email already exists', 
                                 departments=departments)
        
        # Create User first
        new_user = User(username=u_name, user_role=1)
        db.session.add(new_user)
        db.session.commit()
        
        
        new_doctor = Doctor(
            username=u_name,
            passwordd=pwdd,
            name=name1,
            email=email,
            specialization=specialization,
            department_id=department_id,
            qualifications=qualifications,
            contact=contact,
            doctor_id=new_user.id
        )
        db.session.add(new_doctor)
        db.session.commit()
        
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_add_doctor.html', departments=departments)

# admin add patient 

@app.route('/admin_add_patient', methods=['GET', 'POST'])
@login_required
def admin_add_patient():
    if current_user.user_role != 0:
        abort(403)
    
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        pwdp = request.form.get('pwdp')
        name1 = request.form.get('name1')
        DOB = request.form.get('DOB')
        gender1 = request.form.get('gender')
        blood_group1 = request.form.get('blood_group')
        contact = request.form.get('contact', '')
        
        if not (u_name and pwdp and name1 and DOB and gender1 and blood_group1):
            return render_template('admin_add_patient.html', message="Fill the whole form")
        
        existing_user = User.query.filter_by(username=u_name).first()
        if existing_user:
            return render_template('admin_add_patient.html', 
                                 message='Username already exists. Please choose another.')
        
        date_of_birth = datetime.strptime(DOB, '%Y-%m-%d').date()
        
        # Create User 
        new_user = User(username=u_name, user_role=2)
        db.session.add(new_user)
        db.session.commit()
        
        
        new_patient = Patient(
            username=u_name,
            passwordp=pwdp,
            name=name1,
            date_of_birth=date_of_birth,
            gender=gender1,
            blood_group=blood_group1,
            contact=contact,
            patient_id=new_user.id
        )
        db.session.add(new_patient)
        db.session.commit()
        
        flash('Patient added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_add_patient.html')

#admin view appointment

@app.route('/admin_view_appointments')
@login_required
def admin_view_appointments():
    # Core Func4  View all upcoming and past appointments
    if current_user.user_role != 0:
        abort(403)
    
    today = date.today()
    
    # Filter 
    filter_type = request.args.get('filter', 'all')
    
    if filter_type == 'upcoming':
        appointments = Appointment.query.filter(
            Appointment.date >= today,
            Appointment.status != 'Available'
        ).order_by(Appointment.date.asc()).all()
    elif filter_type == 'past':
        appointments = Appointment.query.filter(
            Appointment.date < today,
            Appointment.status != 'Available'
        ).order_by(Appointment.date.desc()).all()
    elif filter_type == 'completed':
        appointments = Appointment.query.filter_by(status='Completed').order_by(Appointment.date.desc()).all()
    elif filter_type == 'cancelled':
        appointments = Appointment.query.filter_by(status='Cancelled').order_by(Appointment.date.desc()).all()
    else:  # all
        appointments = Appointment.query.filter(
            Appointment.status != 'Available'
        ).order_by(Appointment.date.desc()).all()
    
    return render_template('admin_view_appointments.html', appointments=appointments, filter_type=filter_type)


#Admin search  

'''
Search for patients or doctors and view their details
Search by specialization or doctor's name
Search patients by name, ID, or contact information  
   
'''

@app.route('/admin_search', methods=['GET', 'POST'])
@login_required
def admin_search():

    if current_user.user_role != 0:
        abort(403)
    
    doctors = []
    patients = []
    search_query = ''
    search_type = 'all'
    
    if request.method == 'POST' or request.args.get('search_query'):
        if request.method == 'POST':
            search_query = request.form.get('search_query', '').strip()
            search_type = request.form.get('search_type', 'all')
        else:
            search_query = request.args.get('search_query', '').strip()
            search_type = request.args.get('search_type', 'all')
        
        if search_query:
            # Search doctors by name specialization email, contact
            if search_type in ['doctor', 'all']:
                doctors = Doctor.query.filter(
                    or_(
                        Doctor.name.ilike(f'%{search_query}%'),
                        Doctor.specialization.ilike(f'%{search_query}%'),
                        Doctor.email.ilike(f'%{search_query}%'),
                        Doctor.contact.ilike(f'%{search_query}%')
                    )
                ).all()
            
            # Search patients by name, ID, username, or contact
            if search_type in ['patient', 'all']:
                patients = Patient.query.filter(
                    or_(
                        Patient.name.ilike(f'%{search_query}%'),
                        Patient.username.ilike(f'%{search_query}%'),
                        Patient.contact.ilike(f'%{search_query}%'),
                        Patient.id == int(search_query) if search_query.isdigit() else False
                    )
                ).all()
    
    return render_template('admin_search.html', 
                         doctors=doctors, 
                         patients=patients, 
                         search_query=search_query,
                         search_type=search_type)

# admin view doctor
# doubt 
@app.route('/admin_view_doctor/<int:doctor_id>')
@login_required
def admin_view_doctor(doctor_id):
    
    if current_user.user_role != 0:
        abort(403)
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get doctor appointment statistics
    total_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status != 'Available'
    ).count()
    
    completed = Appointment.query.filter_by(doctor_id=doctor.id, status='Completed').count()
    pending = Appointment.query.filter_by(doctor_id=doctor.id, status='Booked').count()
    
    # Get unique patients
    patient_ids = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status != 'Available'
    ).distinct().all()
    total_patients = len([pid[0] for pid in patient_ids if pid[0] is not None])
    
    return render_template('admin_view_doctor.html', 
                         doctor=doctor,
                         total_appointments=total_appointments,
                         completed=completed,
                         pending=pending,
                         total_patients=total_patients)


@app.route('/admin_view_patient/<int:patient_id>')
@login_required
def admin_view_patient(patient_id):
    # View patient information
    if current_user.user_role != 0:
        abort(403)
    
    print(f"DEBUG: Looking for patient with ID: {patient_id}")
    patient = Patient.query.get_or_404(patient_id)
    print(f"DEBUG: Found patient: {patient.name}, patient.id={patient.id}, patient.patient_id={patient.patient_id}")
    
    # Get appointment history
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date.desc()).all()
    print(f"DEBUG: Found {len(appointments)} appointments")
    
    return render_template('admin_view_patient.html', 
                         patient=patient,
                         appointments=appointments)


# Core Func Edit doctor details such as name, specialization etc.
# Core Func  Update doctor profiles

@app.route('/admin_edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_doctor(doctor_id):
  
    if current_user.user_role != 0:
        abort(403)
    
    doctor = Doctor.query.get_or_404(doctor_id)
    departments = Department.query.all()
    
    if request.method == 'POST':
        doctor.name = request.form.get('name')
        doctor.email = request.form.get('email')
        doctor.specialization = request.form.get('specialization')
        doctor.department_id = request.form.get('department_id')
        doctor.qualifications = request.form.get('qualifications', '')
        doctor.contact = request.form.get('contact', '')
        
        # Check if email is already taken by another doctor
        existing = Doctor.query.filter(Doctor.email == doctor.email, Doctor.id != doctor.id).first()
        if existing:
            flash('Email already exists!', 'error')
            return render_template('admin_edit_doctor.html', doctor=doctor, departments=departments)
        
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin_view_doctor', doctor_id=doctor.id))
    
    return render_template('admin_edit_doctor.html', doctor=doctor, departments=departments)


@app.route('/admin_edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_patient(patient_id):
    # Core Func  Edit patient info
    if current_user.user_role != 0:
        abort(403)
    
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.contact = request.form.get('contact', '')
        DOB = request.form.get('DOB')
        if DOB:
            patient.date_of_birth = datetime.strptime(DOB, '%Y-%m-%d').date()
        
        # Allow password change
        new_password = request.form.get('new_password')
        if new_password:
            patient.passwordp = new_password
        
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('admin_view_patient', patient_id=patient.id))
    
    return render_template('admin_edit_patient.html', patient=patient)


# black list 

@app.route('/admin_blacklist_doctor/<int:doctor_id>')
@login_required
def admin_blacklist_doctor(doctor_id):
    # Core Functionality 7: Remove/blacklist doctors from the system
    if current_user.user_role != 0:
        abort(403)
    
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_blacklisted = not doctor.is_blacklisted
    db.session.commit()
    
    status = 'blacklisted' if doctor.is_blacklisted else 'activated'
    flash(f'Doctor {status} successfully!', 'success')
    return redirect(url_for('admin_view_doctor', doctor_id=doctor.id))


#patient

@app.route('/admin_blacklist_patient/<int:patient_id>')
@login_required
def admin_blacklist_patient(patient_id):
    # Core Functionality 7: Remove/blacklist patients from the system
    if current_user.user_role != 0:
        abort(403)
    
    patient = Patient.query.get_or_404(patient_id)
    patient.is_blacklisted = not patient.is_blacklisted
    db.session.commit()
    
    status = 'blacklisted' if patient.is_blacklisted else 'activated'
    flash(f'Patient {status} successfully!', 'success')
    return redirect(url_for('admin_view_patient', patient_id=patient.id))


@app.route('/admin_view_patients')
@login_required
def admin_view_patients():
    patients = Patient.query.order_by(Patient.id.asc()).all()
    return render_template('admin_view_patients.html', patients=patients)


# ==================== DOCTOR ROUTES ====================
#doctor login

@app.route('/doctorlogin', methods=['GET', 'POST'])
def doctorlogin():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        pwd = request.form.get('pwd')
        
        this_doc = Doctor.query.filter_by(username=u_name).first()
        if not this_doc:
            return render_template('doctor_login.html', error="Doctor does not exist")
        if this_doc.is_blacklisted:
            return render_template('doctor_login.html', error="Account has been suspended")
        if this_doc.passwordd != pwd:
            return render_template('doctor_login.html', error="Incorrect password")
        
        
        user = User.query.get(this_doc.doctor_id)
        login_user(user)
        
        return redirect(url_for('doctor_dashboard'))
    
    return render_template('doctor_login.html')


@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    if not doctor or doctor.is_blacklisted:
        logout_user()
        flash('Account suspended', 'error')
        return redirect(url_for('home'))
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    # Core Func Display upcoming appointments for the week
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date == today,
        Appointment.status != 'Available'
    ).order_by(Appointment.st_time.asc()).all()
    
    week_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date > today,
        Appointment.date <= week_later,
        Appointment.status != 'Available'
    ).order_by(Appointment.date.asc(), Appointment.st_time.asc()).all()
    
    # Past appointments for reference
    past_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date < today,
        Appointment.status != 'Available'
    ).order_by(Appointment.date.desc()).limit(20).all()
    
    # Core Func Show list of patients assigned to the doctor
    patient_ids = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status != 'Available',
        Appointment.patient_id.isnot(None)
    ).distinct().all()
    patient_ids = [pid[0] for pid in patient_ids]
    patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()
    
    # Core Func Doctor availability slots
    availability_slots = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status="Available"
    ).order_by(Appointment.date.asc()).all()
    
    # Combine upcoming appointments for display
    upcoming_appointments = today_appointments + week_appointments
    
    # All appointments 
    all_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id
    ).order_by(Appointment.date.desc()).all()
    
    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        upcoming_appointments=upcoming_appointments,
        assigned_patients=patients,
        available_slots=availability_slots,
        appointments=all_appointments,
        today=today
    )


# update appointment status

@app.route('/update_appointment_status/<int:appointment_id>', methods=['POST', 'GET'])
@login_required
def update_appointment_status(appointment_id):
    # Core Func Mark appointments as Completed or Cancelled
    # Core Func  Update appointment status by the doctor
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appointment.doctor_id != doctor.id:
        abort(403)
    
    new_status = request.form.get('status') or request.args.get('status')
    new_date = request.form.get('new_date')
    new_time = request.form.get('new_time')
    
    # Validate status transitions
    if new_status == 'Completed':
        appointment.status = 'Completed'
        db.session.commit()
        flash('Appointment marked as Completed!', 'success')
        return redirect(url_for('add_treatment', appointment_id=appointment_id))
    elif new_status == 'Cancelled':
        appointment.status = 'Cancelled'
        db.session.commit()
        flash('Appointment has been cancelled!', 'success')
    elif new_status == 'Postponed':
        if not new_date or not new_time:
            flash('Please provide new date and time for postponement!', 'error')
            return redirect(url_for('doctor_view_appointment', appointment_id=appointment_id))
        
        try:
            from datetime import datetime
            appointment.date = datetime.strptime(new_date, '%Y-%m-%d').date()
            appointment.st_time = datetime.strptime(new_time, '%H:%M').time()
            appointment.status = 'Booked'
            db.session.commit()
            flash('Appointment has been postponed!', 'success')
        except ValueError:
            flash('Invalid date or time format!', 'error')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('doctor_dashboard'))


@app.route('/doctor/treatment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def doctor_treatment(appointment_id):
    # Route: /doctor/treatment/<appointment_id>
    # Handle create/edit of Treatment (diagnosis, prescription, notes)
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appointment.doctor_id != doctor.id:
        abort(403)
    
    treatment = appointment.treatment
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis', '').strip()
        prescription = request.form.get('prescription', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not diagnosis:
            flash('Diagnosis is required!', 'error')
            return render_template('doctor_treatment.html', appointment=appointment, treatment=treatment)
        
        # Create or update treatment
        if treatment:
            treatment.diagnosis = diagnosis
            treatment.prescription = prescription
            treatment.notes = notes
            flash('Treatment record updated successfully!', 'success')
        else:
            treatment = Treatment(
                appointment_id=appointment_id,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes
            )
            db.session.add(treatment)
            flash('Treatment record created successfully!', 'success')
        
        # Mark appointment as completed if not already
        if appointment.status != 'Completed':
            appointment.status = 'Completed'
        
        db.session.commit()
        return redirect(url_for('doctor_dashboard'))
    
    return render_template('doctor_treatment.html', appointment=appointment, treatment=treatment)


@app.route('/add_treatment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def add_treatment(appointment_id):
    # Legacy route - redirect to new route
    return redirect(url_for('doctor_treatment', appointment_id=appointment_id))


@app.route('/view_patient_history/<int:patient_id>')
@login_required
def view_patient_history(patient_id):
    # Core Func Allow doctors to view full history of patients 
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    patient = Patient.query.get_or_404(patient_id)
    
    # Get all appointments with this doctor
    appointments = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == doctor.id,
        Appointment.status != 'Available'
    ).order_by(Appointment.date.desc()).all()
    
    # Also get appointments with other doctors (for complete medical history)
    all_appointments = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.status == 'Completed'
    ).order_by(Appointment.date.desc()).all()
    
    return render_template('view_patient_history.html', 
                         patient=patient, 
                         appointments=appointments,
                         all_appointments=all_appointments,
                         doctor=doctor)


@app.route('/write_prescription/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def write_prescription(appointment_id):
    # Allow doctors to write/edit prescriptions for their appointments
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify the appointment belongs to this doctor
    if appointment.doctor_id != doctor.id:
        abort(403)
    
    # Verify appointment is completed
    if appointment.status != 'Completed':
        flash('You can only write prescriptions for completed appointments.', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Get or create treatment record
    treatment = appointment.treatment
    if not treatment:
        treatment = Treatment(appointment_id=appointment_id)
        db.session.add(treatment)
        db.session.commit()
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis', '').strip()
        prescription = request.form.get('prescription', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not diagnosis and not prescription:
            flash('Please enter at least diagnosis or prescription.', 'error')
            return render_template('write_prescription.html', appointment=appointment, treatment=treatment)
        
        # Update treatment
        treatment.diagnosis = diagnosis if diagnosis else treatment.diagnosis
        treatment.prescription = prescription if prescription else treatment.prescription
        treatment.notes = notes if notes else treatment.notes
        
        db.session.commit()
        flash('Prescription and medical records saved successfully!', 'success')
        return redirect(url_for('view_patient_history', patient_id=appointment.patient_id))
    
    return render_template('write_prescription.html', appointment=appointment, treatment=treatment)


@app.route('/update_medical_notes/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def update_medical_notes(appointment_id):
    # Allow doctors to add/update medical notes and diagnosis
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    
    if appointment.doctor_id != doctor.id:
        abort(403)
    
    treatment = appointment.treatment
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis', '')
        prescription = request.form.get('prescription', '')
        notes = request.form.get('notes', '')
        
        if not treatment:
            # Create new treatment 
            treatment = Treatment(
                appointment_id=appointment_id,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes
            )
            db.session.add(treatment)
        else:
            # Update existing treatment
            if diagnosis:
                treatment.diagnosis = diagnosis
            if prescription:
                treatment.prescription = prescription
            treatment.notes = notes  # Update notes
        
        db.session.commit()
        flash('Medical notes saved successfully!', 'success')
        return redirect(url_for('view_patient_history', patient_id=appointment.patient_id))
    
    return render_template('update_medical_notes.html', appointment=appointment, treatment=treatment)


# add availability slot

@app.route('/add_availability', methods=['POST'])
@login_required
def add_availability():
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    if not doctor:
        abort(403)
    
    if request.method == 'POST':
        slot_date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        # Convert strings to date/time objects
        slot_date = datetime.strptime(slot_date, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()
        
        # Create new available time slot as an appointment
        new_slot = Appointment(
            doctor_id=doctor.id,
            name="Available",
            date=slot_date,
            st_time=start_time,
            en_time=end_time,
            status="Available"
        )
        
        db.session.add(new_slot)
        db.session.commit()
        flash('Availability added successfully!', 'success')
        
        return redirect(url_for('doctor_dashboard'))
    
#delete availability slot

@app.route('/delete_availability/<int:slot_id>')
@login_required
def delete_availability(slot_id):
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    slot = Appointment.query.get_or_404(slot_id)
    
    # Verify ownership and that it's an availability slot
    if slot.doctor_id != doctor.id or slot.status != 'Available':
        abort(403)
    
    db.session.delete(slot)
    db.session.commit()
    
    flash('Availability slot deleted!', 'success')
    return redirect(url_for('doctor_dashboard'))


@app.route('/doctor_view_appointment/<int:appointment_id>')
@login_required
def doctor_view_appointment(appointment_id):
    # View detailed appointment information
    if current_user.user_role != 1:
        abort(403)
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appointment.doctor_id != doctor.id:
        abort(403)
    
    return render_template('doctor_view_appointment.html', 
                         appointment=appointment,
                         doctor=doctor)


# PATIENT ROUTES
#patient registerrr 

@app.route('/patientregister', methods=['GET', 'POST'])
def patientreg():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        pwdp = request.form.get('pwdp')
        name1 = request.form.get('name1')
        DOB = request.form.get('DOB')
        gender1 = request.form.get('gender')
        blood_group1 = request.form.get('blood_group')
        contact = request.form.get('contact', '')
        
        if not (u_name and pwdp and name1 and DOB and gender1 and blood_group1):
            return render_template('patient_register.html', message="Fill the whole form")
        
        existing_user = User.query.filter_by(username=u_name).first()
        if existing_user:
            return render_template('patient_register.html', message='Username already exists. Please choose another.')
        
        date_of_birth = datetime.strptime(DOB, '%Y-%m-%d').date()
        
        # Create User 
        new_user = User(username=u_name, user_role=2)
        db.session.add(new_user)
        db.session.commit()
         
        # Create Patient 
        new_patient = Patient(
            username=u_name,
            passwordp=pwdp,
            name=name1,
            date_of_birth=date_of_birth,
            gender=gender1,
            blood_group=blood_group1,
            contact=contact,
            patient_id=new_user.id
        )
        db.session.add(new_patient)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('patientlogin'))
    
    return render_template('patient_register.html')

#  patient login

@app.route('/patientlogin', methods=['GET', 'POST'])
def patientlogin():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        pwd = request.form.get('pwd')
        
        this_patient = Patient.query.filter_by(username=u_name).first()
        if not this_patient:
            return render_template('patient_login.html', error="Patient does not exist")
        if this_patient.is_blacklisted:
            return render_template('patient_login.html', error="Account has been suspended")
        if this_patient.passwordp != pwd:
            return render_template('patient_login.html', error="Incorrect password")
        
        
        user = User.query.get(this_patient.patient_id)
        login_user(user)
        
        return redirect(url_for('patient_dashboard'))
    
    return render_template('patient_login.html')


@app.route('/patient_dashboard')
@login_required
def patient_dashboard():
    # Patient Core Func: Register and login
    if current_user.user_role != 2:
        abort(403)
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    if not patient or patient.is_blacklisted:
        logout_user()
        flash('Account suspended', 'error')
        return redirect(url_for('home'))
    
    # Core Func Display all available specialization/departments
    departments = Department.query.all()
    
    # Core Func Display availability of doctors for the coming 7 days
    today = date.today()
    next_week = [today + timedelta(days=i) for i in range(7)]
    doctors = Doctor.query.filter_by(is_blacklisted=False).all()
    
    # Core Func Display upcoming appointments and their status
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= today
    ).order_by(Appointment.date.asc()).all()
    
    # Core Func Show past appointment history with diagnosis and prescriptions
    # Core Func  Allow patients to view their own treatment history
    past_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date < today
    ).order_by(Appointment.date.desc()).all()
    
    return render_template(
        'patient_dashboard.html',
        patient=patient,
        departments=departments,
        doctors=doctors,
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments,
        next_week=next_week,
        today=today
    )


@app.route('/patient_view_treatment/<int:appointment_id>')
@login_required
def patient_view_treatment(appointment_id):
    # Core Func View diagnosis and prescriptions
    # Core Func  Allow patients to view their own treatment history
    if current_user.user_role != 2:
        abort(403)
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    
    if appointment.patient_id != patient.id:
        abort(403)
    
    return render_template('patient_view_treatment.html', appointment=appointment)


@app.route('/patient_view_doctor/<int:doctor_id>')
@login_required
def patient_view_doctor(doctor_id):
    # Core Functionality 3: Read doctor profiles
    if current_user.user_role != 2:
        abort(403)
    
    doctor = Doctor.query.get_or_404(doctor_id)
    if doctor.is_blacklisted:
        flash('Doctor not available', 'error')
        return redirect(url_for('patient_dashboard'))
    
    # Get doctor's availability for next 7 days
    today = date.today()
    next_week = [today + timedelta(days=i) for i in range(7)]
    
    availability = []
    for day in next_week:
        # Available slots for this day (created by doctor)
        available_slots = Appointment.query.filter_by(
            doctor_id=doctor.id,
            date=day,
            status='Available'
        ).order_by(Appointment.st_time.asc()).all()

        # Booked/completed appointments for this day
        booked_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date == day,
            Appointment.status.in_(['Booked', 'Completed'])
        ).order_by(Appointment.st_time.asc()).all()

        availability.append({
            'date': day,
            'day_name': day.strftime('%A'),
            'available_slots': available_slots,
            'booked_appointments': booked_appointments,
            'slots_available': len(available_slots) > 0
        })
    
    return render_template('patient_view_doctor.html', 
                         doctor=doctor, 
                         availability=availability)


@app.route('/create_appointment', methods=['GET', 'POST'])
@login_required
def create_appointment():
    # Core Func Book appointments with doctors
    if current_user.user_role != 2:
        abort(403)
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    doctors = Doctor.query.filter_by(is_blacklisted=False).all()
    departments = Department.query.all()
    
    if request.method == 'POST':
        doctor_id = request.form.get("doctor_id")
        date_str = request.form.get("date")
        stime_str = request.form.get("start_time")
        etime_str = request.form.get("end_time")
        
        
        if not all([doctor_id, date_str, stime_str, etime_str]):
            return render_template('create_appointment.html', 
                                 doctors=doctors,
                                 departments=departments,
                                 message="All fields are required")
        
        date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        stime_obj = datetime.strptime(stime_str.strip(), '%H:%M').time()
        etime_obj = datetime.strptime(etime_str.strip(), '%H:%M').time()
        # ensure doctor_id is int
        try:
            doctor_id_int = int(doctor_id)
        except Exception:
            return render_template('create_appointment.html', 
                                 doctors=doctors,
                                 departments=departments,
                                 message="Invalid doctor selection")
        
        # Check if date is in the past
        if date_obj < date.today():
            return render_template('create_appointment.html', 
                                 doctors=doctors,
                                 departments=departments,
                                 message="Cannot book appointments in the past")
        
        # Check time validity
        if etime_obj <= stime_obj:
            return render_template('create_appointment.html', 
                                 doctors=doctors,
                                 departments=departments,
                                 message="End time must be after start time")
        
        
        available_slot = Appointment.query.filter_by(
            doctor_id=doctor_id_int,
            date=date_obj,
            st_time=stime_obj,
            en_time=etime_obj,
            status='Available'
        ).first()

        if available_slot:
            # Book the available slot
            available_slot.patient_id = patient.id
            available_slot.name = patient.name
            available_slot.status = 'Booked'
            db.session.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('patient_dashboard'))
        else:
            # No available slot found - patient cannot create arbitrary appointments
            return render_template('create_appointment.html', 
                                 doctors=doctors,
                                 departments=departments,
                                 message="This slot is not available. Please check the doctor's available slots and select one of them.")
    
    return render_template('create_appointment.html', doctors=doctors, departments=departments)


@app.route('/cancel_appointment/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    # Core Func  Cancel appointments
    # Core Func  Update appointment status dynamically (Booked → Cancelled)
    if current_user.user_role != 2:
        abort(403)
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    
    if appointment.patient_id != patient.id:
        abort(403)
    
    if appointment.status == 'Completed':
        flash('Cannot cancel completed appointments', 'error')
        return redirect(url_for('patient_dashboard'))
    
    appointment.status = 'Cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('patient_dashboard'))


@app.route('/patient_search_doctors', methods=['GET', 'POST'])
@login_required
def patient_search_doctors():
    # Core Func Search by specialization or doctor's name
    if current_user.user_role != 2:
        abort(403)
    
    doctors = []
    departments = Department.query.all()
    search_query = ''
    search_type = 'name'
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        search_type = request.form.get('search_type', 'name')
        
        if search_query:
            if search_type == 'name':
                doctors = Doctor.query.filter(
                    Doctor.is_blacklisted == False,
                    Doctor.name.ilike(f'%{search_query}%')
                ).all()
            elif search_type == 'specialization':
                doctors = Doctor.query.filter(
                    Doctor.is_blacklisted == False,
                    Doctor.specialization.ilike(f'%{search_query}%')
                ).all()
    
    return render_template('patient_search_doctors.html', 
                         doctors=doctors, 
                         departments=departments,
                         search_query=search_query,
                         search_type=search_type)


@app.route('/patient_edit_profile', methods=['GET', 'POST'])
@login_required
def patient_edit_profile():
    # Core Func Patients can edit their profile
    if current_user.user_role != 2:
        abort(403)
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    
    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.contact = request.form.get('contact', '')
        DOB = request.form.get('DOB')
        if DOB:
            patient.date_of_birth = datetime.strptime(DOB, '%Y-%m-%d').date()
        
        # Allow password change
        new_password = request.form.get('new_password')
        if new_password:
            patient.passwordp = new_password
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient_dashboard'))
    
    return render_template('patient_edit_profile.html', patient=patient)


#ADDITIONAL / SHARED ROUTES 
@app.route('/view_department/<int:dept_id>')
@login_required
def view_department(dept_id):
    # View department details with all doctors
    department = Department.query.get_or_404(dept_id)
    doctors = Doctor.query.filter_by(department_id=dept_id, is_blacklisted=False).all()
    
    return render_template('view_department.html', 
                         department=department, 
                         doctors=doctors)


@app.route('/search_by_department/<int:dept_id>')
@login_required
def search_by_department(dept_id):
    # Search doctors by department
    if current_user.user_role != 2:
        abort(403)
    
    department = Department.query.get_or_404(dept_id)
    doctors = Doctor.query.filter_by(department_id=dept_id, is_blacklisted=False).all()
    
    return render_template('patient_search_doctors.html', 
                         doctors=doctors,
                         search_query=department.name,
                         search_type='department',
                         department=department)


#The route exists.

#The request is valid.

#But the user does not have permission to access that page

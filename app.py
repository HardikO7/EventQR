import os
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
import database
import otp_service
import export_service
import qr_service

app = Flask(__name__)
app.config.from_object(Config)

# Auto-initialize database on fresh cloud instances if database file is missing
if Config.DB_TYPE in ("sqlite", "auto"):
    if not Config.SQLITE_PATH.exists() or Config.SQLITE_PATH.stat().st_size == 0:
        try:
            import init_db
            init_db.setup_database()
            print("[CLOUD INIT] Database auto-initialized successfully.")
        except Exception as e:
            print(f"[CLOUD INIT WARNING] Could not auto-initialize DB: {e}")

# ==============================================================================
# Auth & Role Decorators
# ==============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for('login', next=request.url))
            user_role = session['user'].get('role', 'student')
            if user_role not in roles:
                role_names = " or ".join(r.capitalize() for r in roles)
                flash(f"Access restricted: This area is designated for {role_names} accounts only.", "danger")
                if user_role == 'student':
                    return redirect(url_for('student_dashboard'))
                elif user_role == 'organizer':
                    return redirect(url_for('organizer_dashboard'))
                elif user_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==============================================================================
# Public / Discovery Routes
# ==============================================================================

@app.route('/')
def index():
    """Main Page: Wikipedia-style portal with active events & quick stats"""
    events = database.get_all_approved_events()
    all_users = database.get_all_users()
    all_entries = database.fetch_one("SELECT COUNT(*) as cnt FROM entry_logs")
    stats = {
        "total_events": len(events),
        "total_users": len(all_users),
        "total_confirmed": sum(e.get("confirmed_count", 0) for e in events),
        "total_scans": all_entries["cnt"] if all_entries else 0
    }
    return render_template('index.html', events=events, stats=stats)

@app.route('/events')
def events_list():
    """Browse Events Directory with keyword search and department filter"""
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', 'All Departments').strip()
    events = database.get_all_approved_events(department=dept, search=search)
    return render_template('events_list.html', events=events, search_query=search, selected_dept=dept)

@app.route('/events/<int:event_id>')
def event_detail(event_id):
    """Wikipedia Article-style event view with Infobox, capacity & waitlist"""
    event = database.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('events_list'))

    capacity = database.get_event_capacity_stats(event_id)

    # Check current user registration status
    existing_reg = None
    is_eligible = True
    if 'user' in session:
        u_id = session['user']['id']
        existing_reg = database.fetch_one("SELECT * FROM registrations WHERE event_id = %s AND user_id = %s", (event_id, u_id))
        
        # Check department restriction
        dept_req = event.get('department_restriction', 'All Departments')
        user_dept = session['user'].get('department', '')
        if dept_req != 'All Departments' and dept_req.lower() not in user_dept.lower():
            is_eligible = False

    return render_template('event_detail.html', event=event, capacity=capacity, existing_registration=existing_reg, is_eligible=is_eligible)

# ==============================================================================
# Authentication & Email OTP Routes
# ==============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """Sign up with 6-digit Email OTP Verification"""
    if 'user' in session:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        roll_no = request.form.get('roll_no', '').strip().upper()
        department = request.form.get('department', 'Computer Science').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'student').strip()

        if not all([name, email, password]):
            flash("Name, email, and password are required.", "danger")
            return render_template('register_user.html', form_data=request.form)

        # Check existing user
        if database.get_user_by_email(email):
            flash(f"An account with email '{email}' already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        if roll_no and database.get_user_by_roll(roll_no):
            flash(f"Roll Number '{roll_no}' is already linked to another account.", "warning")
            return render_template('register_user.html', form_data=request.form)

        # Create unverified user
        pw_hash = generate_password_hash(password)
        user_id = database.create_user(name, email, pw_hash, roll_no, phone, department, role, is_verified=0)

        # Generate & send 6-digit OTP
        otp_service.create_and_send_otp(email, purpose="registration", user_name=name)
        session['pending_email'] = email

        flash(f"A 6-digit verification code has been dispatched to {email}. Please check your inbox and enter it to activate your account.", "info")
        return redirect(url_for('verify_otp_route', email=email, purpose="registration"))

    return render_template('register_user.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_route():
    """Verify 6-digit numeric OTP code"""
    email = request.args.get('email') or request.form.get('email', '')
    purpose = request.args.get('purpose') or request.form.get('purpose', 'registration')

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        success, msg = otp_service.verify_otp(email, otp_code, purpose=purpose)

        if success:
            if purpose == "registration":
                user = database.get_user_by_email(email)
                if user:
                    database.update_user_verification(user["id"], verified=True)
                    session['user'] = {
                        'id': user['id'],
                        'name': user['name'],
                        'email': user['email'],
                        'role': user['role'],
                        'department': user['department'],
                        'roll_no': user['roll_no']
                    }
                    flash("Account successfully verified! Welcome to EventQR.", "success")
                    return redirect(url_for('student_dashboard'))

            elif purpose == "password_reset":
                return redirect(url_for('reset_password_route', email=email, otp_code=otp_code))

        flash(msg, "danger")

    return render_template('verify_otp.html', email=email, purpose=purpose)

@app.route('/resend-otp')
def resend_otp():
    email = request.args.get('email', '').strip().lower()
    purpose = request.args.get('purpose', 'registration')
    if email:
        user = database.get_user_by_email(email)
        name = user['name'] if user else 'Student'
        otp_service.create_and_send_otp(email, purpose=purpose, user_name=name)
        flash(f"A new verification code has been dispatched to {email}. Please check your inbox.", "info")
        return redirect(url_for('verify_otp_route', email=email, purpose=purpose))
    flash("Email required.", "danger")
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login for Students, Organizers, and Admins"""
    if 'user' in session:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '').strip()

        # Match either email or roll number
        user = database.get_user_by_email(login_id) or database.get_user_by_roll(login_id)

        if user and check_password_hash(user['password_hash'], password):
            if not user.get('is_active', 1):
                flash("Your account has been suspended by administration. Please contact support.", "danger")
                return render_template('login.html')

            session['user'] = {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'department': user['department'],
                'roll_no': user['roll_no']
            }
            flash(f"Welcome back, {user['name']}!", "success")

            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)

            # Role-based dashboard redirect
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'organizer':
                return redirect(url_for('organizer_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))

        flash("Invalid credentials. Please verify your email/roll number and password.", "danger")

    return render_template('login.html')

@app.route('/login/otp', methods=['GET', 'POST'])
def login_otp_request():
    """Real-Time Passwordless Login: Step 1 (Request OTP via Email or Roll No)"""
    if 'user' in session:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        user = database.get_user_by_email(login_id) or database.get_user_by_roll(login_id)

        if not user:
            flash(f"No registered account found matching '{login_id}'.", "danger")
            return render_template('login_otp.html')

        if not user.get('is_active', 1):
            flash("Your account is currently suspended. Please contact administrator.", "danger")
            return render_template('login_otp.html')

        # Generate 6-digit real-time OTP with 5-minute TTL
        otp_service.create_and_send_otp(user["email"], purpose="login", user_name=user["name"])
        flash(f"A 6-digit login verification code has been dispatched to {user['email']}. Please check your inbox.", "info")
        return redirect(url_for('login_otp_verify', email=user['email']))

    return render_template('login_otp.html')

@app.route('/login/otp/verify', methods=['GET', 'POST'])
def login_otp_verify():
    """Real-Time Passwordless Login: Step 2 (Auto-Submitting OTP verification)"""
    email = request.args.get('email') or request.form.get('email', '')

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        success, msg = otp_service.verify_otp(email, otp_code, purpose="login")

        if success:
            user = database.get_user_by_email(email)
            if user:
                session['user'] = {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role'],
                    'department': user['department'],
                    'roll_no': user['roll_no']
                }
                flash(f"Verified! Welcome back, {user['name']}.", "success")

                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'organizer':
                    return redirect(url_for('organizer_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))

        flash(msg, "danger")

    return render_template('login_otp_verify.html', email=email)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been signed out.", "info")
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request Password Reset OTP"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = database.get_user_by_email(email)
        if user:
            otp_service.create_and_send_otp(email, purpose="password_reset", user_name=user["name"])
            flash(f"A password reset code has been sent to {email}. Please check your inbox.", "info")
            return redirect(url_for('reset_password_route', email=email))
        flash("If this email is registered in EventQR, a password reset code was dispatched.", "info")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_route():
    """Set New Password after OTP verification"""
    email = request.args.get('email') or request.form.get('email', '')

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        new_pw = request.form.get('new_password', '').strip()
        confirm_pw = request.form.get('confirm_password', '').strip()

        if new_pw != confirm_pw:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', email=email)

        success, msg = otp_service.verify_otp(email, otp_code, purpose="password_reset")
        if success:
            user = database.get_user_by_email(email)
            if user:
                database.update_user_password(user["id"], generate_password_hash(new_pw))
                flash("Password updated successfully! Please log in with your new password.", "success")
                return redirect(url_for('login'))
        flash(msg, "danger")

    return render_template('reset_password.html', email=email)

# ==============================================================================
# User Profile Management
# ==============================================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = database.get_user_by_id(session['user']['id'])
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        roll_no = request.form.get('roll_no', '').strip().upper()

        database.update_user_profile(user['id'], name, phone, department, roll_no)
        session['user']['name'] = name
        session['user']['department'] = department
        session['user']['roll_no'] = roll_no
        flash("Profile updated successfully.", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/profile/password', methods=['POST'])
@login_required
def change_password():
    user = database.get_user_by_id(session['user']['id'])
    curr_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')

    if check_password_hash(user['password_hash'], curr_pw):
        database.update_user_password(user['id'], generate_password_hash(new_pw))
        flash("Password changed successfully.", "success")
    else:
        flash("Current password is incorrect.", "danger")

    return redirect(url_for('profile'))

# ==============================================================================
# Student Dashboard & Registration Execution
# ==============================================================================

@app.route('/dashboard')
@login_required
def student_dashboard():
    """Student Desk: List of registered events, passes, and waitlists"""
    user_role = session['user'].get('role', 'student')
    if user_role == 'organizer':
        return redirect(url_for('organizer_dashboard'))
    elif user_role == 'admin':
        return redirect(url_for('admin_dashboard'))

    user_id = session['user']['id']
    regs = database.get_user_registrations(user_id)
    confirmed_count = sum(1 for r in regs if r.get('status') == 'confirmed')
    waitlist_count = sum(1 for r in regs if r.get('status') == 'waitlisted')
    present_count = sum(1 for r in regs if r.get('attendance_status') == 'Present')

    return render_template('student_dashboard.html', 
                           registrations=regs, 
                           confirmed_count=confirmed_count,
                           waitlist_count=waitlist_count,
                           present_count=present_count)

@app.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def event_register(event_id):
    """Execute event registration with capacity & waitlist handling"""
    user_id = session['user']['id']
    user_role = session['user'].get('role', 'student')
    event = database.get_event_by_id(event_id)
    if not event or event['status'] != 'approved':
        flash("Event not available for registration.", "danger")
        return redirect(url_for('events_list'))

    # Organizer restriction: cannot register for own event
    if event['organizer_id'] == user_id:
        flash("Organizers cannot register for their own event. Use the Organizer Desk to manage attendees.", "warning")
        return redirect(url_for('event_detail', event_id=event_id))

    # Role check: only student accounts register for admission passes
    if user_role == 'organizer':
        flash("Organizer accounts cannot register for student attendee passes. Use your Organizer Desk to manage events.", "warning")
        return redirect(url_for('event_detail', event_id=event_id))

    if user_role == 'admin':
        flash("Administrator accounts cannot register for attendee passes. Use the Administration Portal to oversee events.", "warning")
        return redirect(url_for('event_detail', event_id=event_id))

    # Department restriction check
    dept_req = event.get('department_restriction', 'All Departments')
    user_dept = session['user'].get('department', '')
    if dept_req != 'All Departments' and dept_req.lower() not in user_dept.lower():
        flash(f"Eligibility Error: This event is restricted to {dept_req} students.", "danger")
        return redirect(url_for('event_detail', event_id=event_id))

    success, msg, reg = database.register_for_event(event_id, user_id, registration_method="Profile")
    flash(msg, "success" if success else "warning")
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/registrations/<int:reg_id>/cancel', methods=['POST'])
@login_required
def cancel_reg(reg_id):
    """Cancel registration with automatic waitlist promotion"""
    user_id = session['user']['id']
    # Organizers & admins can also cancel registrations on behalf of users
    check_user_id = None if session['user']['role'] in ('organizer', 'admin') else user_id

    success, msg = database.cancel_registration(reg_id, user_id=check_user_id)
    flash(msg, "info" if success else "danger")
    return redirect(request.referrer or url_for('student_dashboard'))

@app.route('/ticket/<token>')
def ticket_view(token):
    """Admission Ticket Pass View"""
    reg = database.get_registration_by_token(token)
    if not reg:
        flash("Invalid or unrecognized ticket token.", "danger")
        return redirect(url_for('find_ticket'))

    return render_template('ticket.html', guest=reg)

def mask_email(email):
    """Mask email for privacy, e.g. ghardik880@gmail.com -> g*******0@gmail.com"""
    if not email or '@' not in email:
        return email
    parts = email.split('@')
    name = parts[0]
    domain = parts[1]
    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"

@app.route('/find-ticket', methods=['GET', 'POST'])
def find_ticket():
    if request.method == 'POST':
        q = request.form.get('query', '').strip()
        if not q:
            flash("Please enter your roll number or university email.", "warning")
            return render_template('find_ticket.html')

        # If user is already authenticated in session and searching for themselves or admin/organizer
        curr_user = session.get('user')
        if curr_user:
            if curr_user['role'] in ('admin', 'organizer') or curr_user['email'].lower() == q.lower() or curr_user.get('roll_no', '').lower() == q.lower():
                target_user = database.get_user_by_roll(q) or database.get_user_by_email(q) or curr_user
                regs = database.get_user_registrations(target_user['id'])
                confirmed = [r for r in regs if r.get('status') == 'confirmed' and r.get('qr_token')]
                if confirmed:
                    if len(confirmed) == 1:
                        return redirect(url_for('ticket_view', token=confirmed[0]['qr_token']))
                    return render_template('find_ticket_results.html', passes=confirmed, student=target_user)
                flash(f"No confirmed ticket pass found for '{q}'.", "warning")
                return render_template('find_ticket.html')

        # Check if direct 32-character token was pasted
        if len(q) == 32 and all(c in '0123456789abcdefABCDEF' for c in q):
            reg = database.get_registration_by_token(q)
            if reg and reg.get('status') == 'confirmed':
                return redirect(url_for('ticket_view', token=reg['qr_token']))

        # Look up user by roll or email
        user = database.get_user_by_roll(q) or database.get_user_by_email(q)
        if not user:
            flash(f"No registered attendee account found matching '{q}'. Please check the roll number or email.", "danger")
            return render_template('find_ticket.html')

        regs = database.get_user_registrations(user['id'])
        confirmed = [r for r in regs if r.get('status') == 'confirmed' and r.get('qr_token')]
        if not confirmed:
            flash(f"No confirmed event admission passes found for {user['name']}.", "warning")
            return render_template('find_ticket.html')

        # Privacy Enforcement: Dispatch 6-digit OTP to registered email
        otp_service.create_and_send_otp(user['email'], purpose="ticket_lookup", user_name=user['name'])
        session['ticket_lookup_user_id'] = user['id']
        session['ticket_lookup_email'] = user['email']

        masked = mask_email(user['email'])
        flash(f"Privacy Protection: A 6-digit verification code has been dispatched to {masked}. Please enter it below to access your pass.", "info")
        return redirect(url_for('find_ticket_verify'))

    return render_template('find_ticket.html')

@app.route('/find-ticket/verify', methods=['GET', 'POST'])
def find_ticket_verify():
    """Verify OTP before revealing ticket passes to maintain attendee privacy"""
    user_id = session.get('ticket_lookup_user_id')
    email = session.get('ticket_lookup_email')

    if not user_id or not email:
        flash("Please search for your admission pass first.", "warning")
        return redirect(url_for('find_ticket'))

    user = database.get_user_by_id(user_id)
    if not user:
        flash("Attendee record not found.", "danger")
        return redirect(url_for('find_ticket'))

    masked = mask_email(email)

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        success, msg = otp_service.verify_otp(email, otp_code, purpose="ticket_lookup")

        if success:
            session.pop('ticket_lookup_user_id', None)
            session.pop('ticket_lookup_email', None)
            session['ticket_access_authorized_for'] = user_id

            regs = database.get_user_registrations(user_id)
            confirmed = [r for r in regs if r.get('status') == 'confirmed' and r.get('qr_token')]
            if not confirmed:
                flash("No active confirmed passes found for this account.", "info")
                return redirect(url_for('find_ticket'))

            if len(confirmed) == 1:
                flash(f"Identity verified! Here is your official admission pass.", "success")
                return redirect(url_for('ticket_view', token=confirmed[0]['qr_token']))

            flash(f"Identity verified! You have {len(confirmed)} confirmed admission passes.", "success")
            return render_template('find_ticket_results.html', passes=confirmed, student=user)

        flash(msg, "danger")

    return render_template('find_ticket_verify.html', email=email, masked_email=masked, user=user)

@app.route('/find-ticket/resend')
def find_ticket_resend():
    """Resend pass lookup verification code"""
    user_id = session.get('ticket_lookup_user_id')
    email = session.get('ticket_lookup_email')
    if user_id and email:
        user = database.get_user_by_id(user_id)
        name = user['name'] if user else "Student"
        otp_service.create_and_send_otp(email, purpose="ticket_lookup", user_name=name)
        flash(f"A new verification code has been dispatched to {mask_email(email)}. Please check your inbox.", "info")
        return redirect(url_for('find_ticket_verify'))
    flash("Session expired. Please search again.", "warning")
    return redirect(url_for('find_ticket'))

# ==============================================================================
# Organizer Desk: Event Creation & Management
# ==============================================================================

@app.route('/organizer/dashboard')
@role_required('organizer', 'admin')
def organizer_dashboard():
    events = database.get_organizer_events(session['user']['id'])
    total_confirmed = sum(e.get('confirmed_count', 0) for e in events)
    total_waitlisted = sum(e.get('waitlist_count', 0) for e in events)
    total_present = sum(e.get('present_count', 0) for e in events)

    return render_template('organizer_dashboard.html', 
                           events=events,
                           total_confirmed=total_confirmed,
                           total_waitlisted=total_waitlisted,
                           total_present=total_present)

@app.route('/events/create', methods=['GET', 'POST'])
@role_required('organizer', 'admin')
def event_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        dept_restriction = request.form.get('department_restriction', 'All Departments').strip()
        event_date = request.form.get('event_date', '').strip()
        event_time = request.form.get('event_time', '').strip()
        venue = request.form.get('venue', '').strip()
        capacity = int(request.form.get('capacity', 50))

        # Admin created events are approved immediately; organizer events are pending
        status = "approved" if session['user']['role'] == 'admin' else "pending"

        event_id = database.create_event(
            title=title,
            description=description,
            department_restriction=dept_restriction,
            event_date=event_date,
            event_time=event_time,
            venue=venue,
            capacity=capacity,
            organizer_id=session['user']['id'],
            status=status
        )

        if status == "approved":
            flash("Event created and published successfully!", "success")
        else:
            flash("Event proposal submitted! It will appear in the directory once approved by administration.", "info")

        return redirect(url_for('organizer_dashboard'))

    return render_template('event_create.html')

@app.route('/events/<int:event_id>/manage')
@role_required('organizer', 'admin')
def event_manage(event_id):
    event = database.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('organizer_dashboard'))

    # Organizer access constraint: organizers can only manage events they created
    if session['user']['role'] == 'organizer' and event['organizer_id'] != session['user']['id']:
        flash("Access restricted: Organizers can only access attendee lists and registration details for their own events.", "danger")
        return redirect(url_for('organizer_dashboard'))

    tab = request.args.get('tab', 'confirmed')
    capacity_stats = database.get_event_capacity_stats(event_id)
    confirmed_attendees = database.get_event_attendees(event_id, status_filter='confirmed')
    waitlist_attendees = database.get_event_attendees(event_id, status_filter='waitlisted')
    present_list = database.get_event_present_list(event_id)
    absent_list = database.get_event_absent_list(event_id)

    return render_template('event_manage.html',
                           event=event,
                           capacity_stats=capacity_stats,
                           active_tab=tab,
                           confirmed_attendees=confirmed_attendees,
                           waitlist_attendees=waitlist_attendees,
                           present_list=present_list,
                           absent_list=absent_list)

@app.route('/events/<int:event_id>/capacity', methods=['POST'])
@role_required('organizer', 'admin')
def update_event_capacity(event_id):
    event = database.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('organizer_dashboard'))

    if session['user']['role'] == 'organizer' and event['organizer_id'] != session['user']['id']:
        flash("Access restricted: You can only adjust seat capacity for your own events.", "danger")
        return redirect(url_for('organizer_dashboard'))

    new_capacity = int(request.form.get('capacity', 50))
    database.update_event(
        event_id=event_id,
        title=event['title'],
        description=event['description'],
        department_restriction=event['department_restriction'],
        event_date=event['event_date'],
        event_time=event['event_time'],
        venue=event['venue'],
        capacity=new_capacity
    )

    # Check if waitlisted students can now be promoted
    stats = database.get_event_capacity_stats(event_id)
    promoted_count = 0
    while stats["remaining"] > 0 and stats["waitlisted"] > 0:
        next_w = database.fetch_one("""
            SELECT * FROM registrations 
            WHERE event_id = %s AND status = 'waitlisted' 
            ORDER BY waitlist_position ASC LIMIT 1
        """, (event_id,))
        if not next_w:
            break

        import qr_service
        import email_service

        promoted_u = database.get_user_by_id(next_w["user_id"])
        token = qr_service.generate_secure_token()
        pass_rel, qr_rel = qr_service.generate_qr_ticket(
            token=token,
            guest_name=promoted_u["name"],
            roll_no=promoted_u["roll_no"] or "Student",
            department=promoted_u["department"],
            event_title=event["title"]
        )
        database.execute_query("""
            UPDATE registrations 
            SET status = 'confirmed', waitlist_position = 0, qr_token = %s, qr_image_path = %s
            WHERE id = %s
        """, (token, pass_rel, next_w["id"]))

        database.execute_query("""
            UPDATE registrations 
            SET waitlist_position = waitlist_position - 1
            WHERE event_id = %s AND status = 'waitlisted' AND waitlist_position > 1
        """, (event_id,))

        email_service.send_ticket_email(
            guest_name=promoted_u["name"],
            to_email=promoted_u["email"],
            roll_no=promoted_u["roll_no"] or "Student",
            department=promoted_u["department"],
            token=token,
            qr_image_path=pass_rel,
            event_title=event["title"]
        )
        promoted_count += 1
        stats = database.get_event_capacity_stats(event_id)

    msg = f"Capacity updated to {new_capacity}."
    if promoted_count > 0:
        msg += f" Automatically promoted {promoted_count} student(s) from the waitlist to confirmed!"
    flash(msg, "success")

    return redirect(url_for('event_manage', event_id=event_id))

@app.route('/events/<int:event_id>/export/pdf')
@role_required('organizer', 'admin')
def export_event_pdf(event_id):
    event = database.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('organizer_dashboard'))

    if session['user']['role'] == 'organizer' and event['organizer_id'] != session['user']['id']:
        flash("Access restricted: You can only export attendee reports for your own events.", "danger")
        return redirect(url_for('organizer_dashboard'))

    report_type = request.args.get('report_type', 'present')
    buf = export_service.generate_pdf_report(report_type, event_id)
    filename = f"Event_{event_id}_{report_type}_attendance.pdf"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/events/<int:event_id>/export/excel')
@role_required('organizer', 'admin')
def export_event_excel(event_id):
    event = database.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('organizer_dashboard'))

    if session['user']['role'] == 'organizer' and event['organizer_id'] != session['user']['id']:
        flash("Access restricted: You can only export attendee rosters for your own events.", "danger")
        return redirect(url_for('organizer_dashboard'))

    report_type = request.args.get('report_type', 'full')
    buf = export_service.generate_excel_report(report_type, event_id)
    filename = f"Event_{event_id}_{report_type}_roster.xlsx"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ==============================================================================
# Gate Checkpoint Scanner
# ==============================================================================

@app.route('/scanner')
@role_required('organizer', 'admin')
def gate_scanner():
    events = database.get_all_approved_events()
    event_id = request.args.get('event_id')
    selected_event = database.get_event_by_id(int(event_id)) if event_id else None

    # Get sample token for quick testing
    sample_reg = database.fetch_one("SELECT r.qr_token, u.name FROM registrations r JOIN users u ON r.user_id = u.id WHERE r.status = 'confirmed' AND r.qr_token IS NOT NULL LIMIT 1")

    return render_template('scanner.html', 
                           events=events, 
                           selected_event=selected_event,
                           sample_token=sample_reg['qr_token'] if sample_reg else '',
                           sample_name=sample_reg['name'] if sample_reg else '')

@app.route('/api/validate-scan', methods=['POST'])
def api_validate_scan():
    """Real-time QR validation endpoint called by web and desktop scanners"""
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    gate = data.get('gate', 'Main Gate 1').strip()
    scanned_by = session.get('user', {}).get('name', 'Staff Scanner')

    if not token:
        return jsonify({"status": "ERROR", "message": "No token provided."}), 400

    reg = database.get_registration_by_token(token)
    if not reg:
        return jsonify({
            "status": "INVALID",
            "message": "Unrecognized or fraudulent QR code. Token not found in event records.",
            "guest": None
        }), 200

    if reg['status'] != 'confirmed':
        return jsonify({
            "status": "INVALID",
            "message": f"Admission Rejected: Attendee registration is '{reg['status']}'.",
            "guest": reg
        }), 200

    # Record entry (enforces single scan constraint)
    success, log_entry = database.record_gate_entry(reg['id'], gate_number=gate, scanned_by=scanned_by)
    if not success:
        return jsonify({
            "status": "ALREADY_USED",
            "message": f"ENTRY REJECTED: Pass was already scanned on {log_entry.get('scan_time')} at {log_entry.get('gate_number')}!",
            "guest": reg,
            "log": log_entry
        }), 200

    return jsonify({
        "status": "GRANTED",
        "message": f"ACCESS GRANTED: Welcome, {reg['student_name']}!",
        "guest": reg,
        "log": log_entry
    }), 200

# ==============================================================================
# Administration Desk: Moderation & User Management
# ==============================================================================

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    all_events = database.get_all_events_for_admin()
    all_users = database.get_all_users()
    pending_count = sum(1 for e in all_events if e.get('status') == 'pending')
    entries_count = database.fetch_one("SELECT COUNT(*) as cnt FROM entry_logs")['cnt']

    return render_template('admin_dashboard.html',
                           events=all_events,
                           total_users=len(all_users),
                           pending_events_count=pending_count,
                           total_entries=entries_count)

@app.route('/admin/approvals')
@role_required('admin')
def admin_approvals():
    pending_events = database.get_all_events_for_admin(status='pending')
    return render_template('admin_approvals.html', pending_events=pending_events)

@app.route('/admin/events/<int:event_id>/approve', methods=['POST'])
@role_required('admin')
def admin_event_approve(event_id):
    database.approve_event(event_id)
    flash("Event has been approved and published to the public directory.", "success")
    return redirect(url_for('admin_approvals'))

@app.route('/admin/events/<int:event_id>/reject', methods=['POST'])
@role_required('admin')
def admin_event_reject(event_id):
    reason = request.form.get('reason', '').strip()
    database.reject_event(event_id, reason=reason)
    flash("Event proposal has been rejected.", "info")
    return redirect(url_for('admin_approvals'))

@app.route('/admin/users')
@role_required('admin')
def admin_users():
    search = request.args.get('search', '').strip()
    role = request.args.get('role', 'all').strip()
    users = database.get_all_users(role=role, search=search)
    return render_template('admin_users.html', users=users, search_query=search, selected_role=role)

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@role_required('admin')
def admin_user_toggle(user_id):
    new_state = database.toggle_user_active(user_id)
    flash(f"User account status updated to {'Active' if new_state else 'Suspended'}.", "info")
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/role', methods=['POST'])
@role_required('admin')
def admin_user_role(user_id):
    new_role = request.form.get('role', 'student').strip()
    database.update_user_role(user_id, new_role)
    flash(f"User role updated to '{new_role.capitalize()}'.", "success")
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/eligibility', methods=['GET', 'POST'])
@role_required('admin')
def admin_eligibility():
    if request.method == 'POST':
        roll = request.form.get('roll_no', '').strip().upper()
        name = request.form.get('name', '').strip()
        dept = request.form.get('department', '').strip()
        course = request.form.get('course', 'MCA').strip()
        email = request.form.get('email', '').strip()
        if roll and name and dept:
            added = database.add_eligible_student(roll, name, dept, course, email)
            if added:
                flash(f"Added {name} ({roll}) to master eligibility reference table.", "success")
            else:
                flash(f"Student with roll number '{roll}' already exists in table.", "warning")

    students = database.get_all_eligible_students()
    return render_template('admin_eligibility.html', students=students)

# ==============================================================================
# Main Runner
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("=" * 65)
    print(" EventPass Campus Event Management Platform")
    print(" Real-Time QR Gate Scanning & Capacity Engine")
    print(f" Server Running at: http://127.0.0.1:{port}")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=False)

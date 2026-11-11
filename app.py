import io
import os
from functools import wraps
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
import init_db

app = Flask(__name__)
app.config.from_object(Config)

try:
    init_db.ensure_database()
except Exception as e:
    print(f"[DB INIT WARNING] Could not verify MySQL database on startup: {e}")


# ==============================================================================
# Session, Auth & Authorization Helpers
# ==============================================================================

def _set_user_session(user):
    session['user'] = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
        'department': user['department'],
        'roll_no': user['roll_no'],
    }


def _redirect_for_role(role):
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    if role == 'organizer':
        return redirect(url_for('organizer_dashboard'))
    return redirect(url_for('student_dashboard'))


def _mask_email(email):
    if not email or '@' not in email:
        return email
    name, domain = email.split('@', 1)
    masked_name = (name[0] + "*") if len(name) <= 2 else (name[0] + "*" * (len(name) - 2) + name[-1])
    return f"{masked_name}@{domain}"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for('login', next=request.url))
            user_role = session['user'].get('role', 'student')
            if user_role not in roles:
                role_names = " or ".join(r.capitalize() for r in roles)
                flash(f"Access restricted: This area is designated for {role_names} accounts only.", "danger")
                return _redirect_for_role(user_role)
            return f(*args, **kwargs)
        return decorated
    return decorator


def _get_authorized_organizer_event(event_id):
    """Fetch event and verify organizer ownership (admins can access all events)."""
    event = database.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return None
    if session['user']['role'] == 'organizer' and event['organizer_id'] != session['user']['id']:
        flash("Access restricted: Organizers can only manage their own events.", "danger")
        return None
    return event


# ==============================================================================
# Public / Discovery Routes
# ==============================================================================

@app.route('/')
def index():
    events = database.get_all_approved_events()
    all_users = database.get_all_users()
    all_entries = database.fetch_one("SELECT COUNT(*) as cnt FROM entry_logs")
    stats = {
        "total_events": len(events),
        "total_users": len(all_users),
        "total_confirmed": sum(e.get("confirmed_count", 0) for e in events),
        "total_scans": all_entries["cnt"] if all_entries else 0,
    }
    return render_template('index.html', events=events, stats=stats)


@app.route('/events')
def events_list():
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', 'All Departments').strip()
    events = database.get_all_approved_events(department=dept, search=search)
    return render_template('events_list.html', events=events, search_query=search, selected_dept=dept)


@app.route('/events/<int:event_id>')
def event_detail(event_id):
    event = database.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('events_list'))

    capacity = database.get_event_capacity_stats(event_id)
    existing_reg = None
    is_eligible = True
    if 'user' in session:
        existing_reg = database.fetch_one(
            "SELECT * FROM registrations WHERE event_id = %s AND user_id = %s",
            (event_id, session['user']['id']),
        )
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

        if database.get_user_by_email(email):
            flash(f"An account with email '{email}' already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        if roll_no and database.get_user_by_roll(roll_no):
            flash(f"Roll Number '{roll_no}' is already linked to another account.", "warning")
            return render_template('register_user.html', form_data=request.form)

        database.create_user(name, email, generate_password_hash(password), roll_no, phone, department, role, is_verified=0)
        otp_service.create_and_send_otp(email, purpose="registration", user_name=name)
        session['pending_email'] = email

        flash(f"A 6-digit verification code has been dispatched to {email}. Please check your inbox and enter it to activate your account.", "info")
        return redirect(url_for('verify_otp_route', email=email, purpose="registration"))

    return render_template('register_user.html')


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_route():
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
                    _set_user_session(user)
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
        otp_service.create_and_send_otp(email, purpose=purpose, user_name=user['name'] if user else 'Student')
        flash(f"A new verification code has been dispatched to {email}. Please check your inbox.", "info")
        return redirect(url_for('verify_otp_route', email=email, purpose=purpose))
    flash("Email required.", "danger")
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return _redirect_for_role(session['user'].get('role', 'student'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '').strip()
        user = database.get_user_by_email(login_id) or database.get_user_by_roll(login_id)

        if user and check_password_hash(user['password_hash'], password):
            if not user.get('is_active', 1):
                flash("Your account has been suspended by administration. Please contact support.", "danger")
                return render_template('login.html')

            _set_user_session(user)
            flash(f"Welcome back, {user['name']}!", "success")
            next_url = request.args.get('next')
            return redirect(next_url) if next_url else _redirect_for_role(user['role'])

        flash("Invalid credentials. Please verify your email/roll number and password.", "danger")

    return render_template('login.html')


@app.route('/login/otp', methods=['GET', 'POST'])
def login_otp_request():
    if 'user' in session:
        return _redirect_for_role(session['user'].get('role', 'student'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        user = database.get_user_by_email(login_id) or database.get_user_by_roll(login_id)

        if not user:
            flash(f"No registered account found matching '{login_id}'.", "danger")
            return render_template('login_otp.html')
        if not user.get('is_active', 1):
            flash("Your account is currently suspended. Please contact administrator.", "danger")
            return render_template('login_otp.html')

        otp_service.create_and_send_otp(user["email"], purpose="login", user_name=user["name"])
        flash(f"A 6-digit login verification code has been dispatched to {user['email']}. Please check your inbox.", "info")
        return redirect(url_for('login_otp_verify', email=user['email']))

    return render_template('login_otp.html')


@app.route('/login/otp/verify', methods=['GET', 'POST'])
def login_otp_verify():
    email = request.args.get('email') or request.form.get('email', '')

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        success, msg = otp_service.verify_otp(email, otp_code, purpose="login")
        if success:
            user = database.get_user_by_email(email)
            if user:
                _set_user_session(user)
                flash(f"Verified! Welcome back, {user['name']}.", "success")
                return _redirect_for_role(user['role'])
        flash(msg, "danger")

    return render_template('login_otp_verify.html', email=email)


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been signed out.", "info")
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
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
    if check_password_hash(user['password_hash'], request.form.get('current_password', '')):
        database.update_user_password(user['id'], generate_password_hash(request.form.get('new_password', '')))
        flash("Password changed successfully.", "success")
    else:
        flash("Current password is incorrect.", "danger")
    return redirect(url_for('profile'))


# ==============================================================================
# Student Dashboard, Registration & Ticket Lookup
# ==============================================================================

@app.route('/dashboard')
@login_required
def student_dashboard():
    user_role = session['user'].get('role', 'student')
    if user_role != 'student':
        return _redirect_for_role(user_role)

    regs = database.get_user_registrations(session['user']['id'])
    return render_template(
        'student_dashboard.html',
        registrations=regs,
        confirmed_count=sum(1 for r in regs if r.get('status') == 'confirmed'),
        waitlist_count=sum(1 for r in regs if r.get('status') == 'waitlisted'),
        present_count=sum(1 for r in regs if r.get('attendance_status') == 'Present'),
    )


@app.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def event_register(event_id):
    user_id = session['user']['id']
    user_role = session['user'].get('role', 'student')
    event = database.get_event_by_id(event_id)
    if not event or event['status'] != 'approved':
        flash("Event not available for registration.", "danger")
        return redirect(url_for('events_list'))

    if event['organizer_id'] == user_id or user_role != 'student':
        flash("Only student attendee accounts can register for event passes.", "warning")
        return redirect(url_for('event_detail', event_id=event_id))

    dept_req = event.get('department_restriction', 'All Departments')
    user_dept = session['user'].get('department', '')
    if dept_req != 'All Departments' and dept_req.lower() not in user_dept.lower():
        flash(f"Eligibility Error: This event is restricted to {dept_req} students.", "danger")
        return redirect(url_for('event_detail', event_id=event_id))

    success, msg, _ = database.register_for_event(event_id, user_id, registration_method="Profile")
    flash(msg, "success" if success else "warning")
    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/registrations/<int:reg_id>/cancel', methods=['POST'])
@login_required
def cancel_reg(reg_id):
    check_user_id = None if session['user']['role'] in ('organizer', 'admin') else session['user']['id']
    success, msg = database.cancel_registration(reg_id, user_id=check_user_id)
    flash(msg, "info" if success else "danger")
    return redirect(request.referrer or url_for('student_dashboard'))


@app.route('/ticket/<token>')
def ticket_view(token):
    reg = database.get_registration_by_token(token)
    if not reg:
        flash("Invalid or unrecognized ticket token.", "danger")
        return redirect(url_for('find_ticket'))
    return render_template('ticket.html', guest=reg)


@app.route('/ticket/<token>/image')
def ticket_image(token):
    """Serve admission pass PNG dynamically from memory (works on read-only serverless hosts)."""
    reg = database.get_registration_by_token(token)
    if not reg or reg.get('status') != 'confirmed':
        return "Ticket not found", 404

    png_bytes = qr_service.render_pass_badge_bytes(
        token=reg['qr_token'],
        guest_name=reg['student_name'],
        roll_no=reg.get('student_roll') or 'Student',
        department=reg.get('student_dept') or 'Computer Science',
        event_title=reg['event_title'],
    )
    as_download = request.args.get('download') == '1'
    return send_file(
        io.BytesIO(png_bytes),
        mimetype='image/png',
        as_attachment=as_download,
        download_name=f"eventpass_{reg['qr_token'][:8]}.png",
    )


def _render_confirmed_passes(user):
    regs = database.get_user_registrations(user['id'])
    confirmed = [r for r in regs if r.get('status') == 'confirmed' and r.get('qr_token')]
    if not confirmed:
        return None
    if len(confirmed) == 1:
        return redirect(url_for('ticket_view', token=confirmed[0]['qr_token']))
    return render_template('find_ticket_results.html', passes=confirmed, student=user)


@app.route('/find-ticket', methods=['GET', 'POST'])
def find_ticket():
    if request.method == 'POST':
        q = request.form.get('query', '').strip()
        if not q:
            flash("Please enter your roll number or university email.", "warning")
            return render_template('find_ticket.html')

        curr_user = session.get('user')
        if curr_user and (
            curr_user['role'] in ('admin', 'organizer')
            or curr_user['email'].lower() == q.lower()
            or (curr_user.get('roll_no') or '').lower() == q.lower()
        ):
            target_user = database.get_user_by_roll(q) or database.get_user_by_email(q) or curr_user
            resp = _render_confirmed_passes(target_user)
            if resp:
                return resp
            flash(f"No confirmed ticket pass found for '{q}'.", "warning")
            return render_template('find_ticket.html')

        if len(q) == 32 and all(c in '0123456789abcdefABCDEF' for c in q):
            reg = database.get_registration_by_token(q)
            if reg and reg.get('status') == 'confirmed':
                return redirect(url_for('ticket_view', token=reg['qr_token']))

        user = database.get_user_by_roll(q) or database.get_user_by_email(q)
        if not user:
            flash(f"No registered attendee account found matching '{q}'. Please check the roll number or email.", "danger")
            return render_template('find_ticket.html')

        regs = database.get_user_registrations(user['id'])
        if not any(r.get('status') == 'confirmed' and r.get('qr_token') for r in regs):
            flash(f"No confirmed event admission passes found for {user['name']}.", "warning")
            return render_template('find_ticket.html')

        otp_service.create_and_send_otp(user['email'], purpose="ticket_lookup", user_name=user['name'])
        session['ticket_lookup_user_id'] = user['id']
        session['ticket_lookup_email'] = user['email']
        flash(f"Privacy Protection: A 6-digit verification code has been dispatched to {_mask_email(user['email'])}.", "info")
        return redirect(url_for('find_ticket_verify'))

    return render_template('find_ticket.html')


@app.route('/find-ticket/verify', methods=['GET', 'POST'])
def find_ticket_verify():
    user_id = session.get('ticket_lookup_user_id')
    email = session.get('ticket_lookup_email')
    if not user_id or not email:
        flash("Please search for your admission pass first.", "warning")
        return redirect(url_for('find_ticket'))

    user = database.get_user_by_id(user_id)
    if not user:
        flash("Attendee record not found.", "danger")
        return redirect(url_for('find_ticket'))

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        success, msg = otp_service.verify_otp(email, otp_code, purpose="ticket_lookup")
        if success:
            session.pop('ticket_lookup_user_id', None)
            session.pop('ticket_lookup_email', None)
            session['ticket_access_authorized_for'] = user_id
            resp = _render_confirmed_passes(user)
            if resp:
                flash("Identity verified!", "success")
                return resp
            flash("No active confirmed passes found for this account.", "info")
            return redirect(url_for('find_ticket'))
        flash(msg, "danger")

    return render_template('find_ticket_verify.html', email=email, masked_email=_mask_email(email), user=user)


@app.route('/find-ticket/resend')
def find_ticket_resend():
    user_id = session.get('ticket_lookup_user_id')
    email = session.get('ticket_lookup_email')
    if user_id and email:
        user = database.get_user_by_id(user_id)
        otp_service.create_and_send_otp(email, purpose="ticket_lookup", user_name=user['name'] if user else "Student")
        flash(f"A new verification code has been dispatched to {_mask_email(email)}.", "info")
        return redirect(url_for('find_ticket_verify'))
    flash("Session expired. Please search again.", "warning")
    return redirect(url_for('find_ticket'))


# ==============================================================================
# Organizer Desk: Event Creation, Capacity & Exports
# ==============================================================================

@app.route('/organizer/dashboard')
@role_required('organizer', 'admin')
def organizer_dashboard():
    events = database.get_organizer_events(session['user']['id'])
    return render_template(
        'organizer_dashboard.html',
        events=events,
        total_confirmed=sum(e.get('confirmed_count', 0) for e in events),
        total_waitlisted=sum(e.get('waitlist_count', 0) for e in events),
        total_present=sum(e.get('present_count', 0) for e in events),
    )


@app.route('/events/create', methods=['GET', 'POST'])
@role_required('organizer', 'admin')
def event_create():
    if request.method == 'POST':
        status = "approved" if session['user']['role'] == 'admin' else "pending"
        database.create_event(
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip(),
            department_restriction=request.form.get('department_restriction', 'All Departments').strip(),
            event_date=request.form.get('event_date', '').strip(),
            event_time=request.form.get('event_time', '').strip(),
            venue=request.form.get('venue', '').strip(),
            capacity=int(request.form.get('capacity', 50)),
            organizer_id=session['user']['id'],
            status=status,
        )
        msg = "Event created and published successfully!" if status == "approved" else "Event proposal submitted for administrative approval."
        flash(msg, "success" if status == "approved" else "info")
        return redirect(url_for('organizer_dashboard'))

    return render_template('event_create.html')


@app.route('/events/<int:event_id>/manage')
@role_required('organizer', 'admin')
def event_manage(event_id):
    event = _get_authorized_organizer_event(event_id)
    if not event:
        return redirect(url_for('organizer_dashboard'))

    return render_template(
        'event_manage.html',
        event=event,
        capacity_stats=database.get_event_capacity_stats(event_id),
        active_tab=request.args.get('tab', 'confirmed'),
        confirmed_attendees=database.get_event_attendees(event_id, status_filter='confirmed'),
        waitlist_attendees=database.get_event_attendees(event_id, status_filter='waitlisted'),
        present_list=database.get_event_present_list(event_id),
        absent_list=database.get_event_absent_list(event_id),
    )


@app.route('/events/<int:event_id>/capacity', methods=['POST'])
@role_required('organizer', 'admin')
def update_event_capacity(event_id):
    event = _get_authorized_organizer_event(event_id)
    if not event:
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
        capacity=new_capacity,
    )

    promoted_count = 0
    stats = database.get_event_capacity_stats(event_id)
    while stats["remaining"] > 0 and stats["waitlisted"] > 0:
        if not database.promote_next_waitlisted(event_id):
            break
        promoted_count += 1
        stats = database.get_event_capacity_stats(event_id)

    msg = f"Capacity updated to {new_capacity}."
    if promoted_count:
        msg += f" Automatically promoted {promoted_count} student(s) from the waitlist!"
    flash(msg, "success")
    return redirect(url_for('event_manage', event_id=event_id))


@app.route('/events/<int:event_id>/export/pdf')
@role_required('organizer', 'admin')
def export_event_pdf(event_id):
    if not _get_authorized_organizer_event(event_id):
        return redirect(url_for('organizer_dashboard'))
    report_type = request.args.get('report_type', 'present')
    buf = export_service.generate_pdf_report(report_type, event_id)
    return send_file(buf, as_attachment=True, download_name=f"Event_{event_id}_{report_type}_attendance.pdf", mimetype='application/pdf')


@app.route('/events/<int:event_id>/export/excel')
@role_required('organizer', 'admin')
def export_event_excel(event_id):
    if not _get_authorized_organizer_event(event_id):
        return redirect(url_for('organizer_dashboard'))
    report_type = request.args.get('report_type', 'full')
    buf = export_service.generate_excel_report(report_type, event_id)
    return send_file(buf, as_attachment=True, download_name=f"Event_{event_id}_{report_type}_roster.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ==============================================================================
# Gate Checkpoint Scanner
# ==============================================================================

@app.route('/scanner')
@role_required('organizer', 'admin')
def gate_scanner():
    events = database.get_all_approved_events()
    event_id = request.args.get('event_id')
    selected_event = database.get_event_by_id(int(event_id)) if event_id else None
    sample_reg = database.fetch_one("SELECT r.qr_token, u.name FROM registrations r JOIN users u ON r.user_id = u.id WHERE r.status = 'confirmed' AND r.qr_token IS NOT NULL LIMIT 1")
    return render_template(
        'scanner.html',
        events=events,
        selected_event=selected_event,
        sample_token=sample_reg['qr_token'] if sample_reg else '',
        sample_name=sample_reg['name'] if sample_reg else '',
    )


@app.route('/api/validate-scan', methods=['POST'])
def api_validate_scan():
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    gate = data.get('gate', 'Main Gate 1').strip()
    scanned_by = session.get('user', {}).get('name', 'Staff Scanner')

    if not token:
        return jsonify({"status": "ERROR", "message": "No token provided."}), 400

    reg = database.get_registration_by_token(token)
    if not reg:
        return jsonify({"status": "INVALID", "message": "Unrecognized or fraudulent QR code. Token not found in event records.", "guest": None}), 200

    if reg['status'] != 'confirmed':
        return jsonify({"status": "INVALID", "message": f"Admission Rejected: Attendee registration is '{reg['status']}'.", "guest": reg}), 200

    success, log_entry = database.record_gate_entry(reg['id'], gate_number=gate, scanned_by=scanned_by)
    if not success:
        return jsonify({
            "status": "ALREADY_USED",
            "message": f"ENTRY REJECTED: Pass was already scanned on {log_entry.get('scan_time')} at {log_entry.get('gate_number')}!",
            "guest": reg,
            "log": log_entry,
        }), 200

    return jsonify({
        "status": "GRANTED",
        "message": f"ACCESS GRANTED: Welcome, {reg['student_name']}!",
        "guest": reg,
        "log": log_entry,
    }), 200


# ==============================================================================
# Administration Console
# ==============================================================================

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    all_events = database.get_all_events_for_admin()
    all_users = database.get_all_users()
    entries_count = database.fetch_one("SELECT COUNT(*) as cnt FROM entry_logs")['cnt']
    return render_template(
        'admin_dashboard.html',
        events=all_events,
        total_users=len(all_users),
        pending_events_count=sum(1 for e in all_events if e.get('status') == 'pending'),
        total_entries=entries_count,
    )


@app.route('/admin/approvals')
@role_required('admin')
def admin_approvals():
    return render_template('admin_approvals.html', pending_events=database.get_all_events_for_admin(status='pending'))


@app.route('/admin/events/<int:event_id>/approve', methods=['POST'])
@role_required('admin')
def admin_event_approve(event_id):
    database.approve_event(event_id)
    flash("Event has been approved and published to the public directory.", "success")
    return redirect(url_for('admin_approvals'))


@app.route('/admin/events/<int:event_id>/reject', methods=['POST'])
@role_required('admin')
def admin_event_reject(event_id):
    database.reject_event(event_id, reason=request.form.get('reason', '').strip())
    flash("Event proposal has been rejected.", "info")
    return redirect(url_for('admin_approvals'))


@app.route('/admin/users')
@role_required('admin')
def admin_users():
    search = request.args.get('search', '').strip()
    role = request.args.get('role', 'all').strip()
    return render_template('admin_users.html', users=database.get_all_users(role=role, search=search), search_query=search, selected_role=role)


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
            if database.add_eligible_student(roll, name, dept, course, email):
                flash(f"Added {name} ({roll}) to master eligibility reference table.", "success")
            else:
                flash(f"Student with roll number '{roll}' already exists in table.", "warning")

    return render_template('admin_eligibility.html', students=database.get_all_eligible_students())


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("=" * 65)
    print(" EventPass Campus Event Management Platform (MySQL)")
    print(f" Server Running at: http://127.0.0.1:{port}")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=False)

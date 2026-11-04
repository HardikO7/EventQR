import sqlite3
import os
from datetime import datetime
from config import Config

CURRENT_ENGINE = "sqlite"

def get_mysql_connection():
    import mysql.connector
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

def test_mysql_available():
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            connection_timeout=2
        )
        conn.close()
        return True
    except Exception:
        return False

def get_db_connection():
    global CURRENT_ENGINE
    if Config.DB_TYPE in ("mysql", "auto") and test_mysql_available():
        try:
            conn = get_mysql_connection()
            CURRENT_ENGINE = "mysql"
            return conn
        except Exception:
            pass

    conn = sqlite3.connect(Config.SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    CURRENT_ENGINE = "sqlite"
    return conn

def adapt_sql(sql):
    if CURRENT_ENGINE == "sqlite":
        return sql.replace("%s", "?")
    return sql

def execute_query(sql, params=(), commit=True, return_id=False):
    conn = get_db_connection()
    sql = adapt_sql(sql)
    last_id = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        if commit:
            conn.commit()
        if return_id:
            last_id = cursor.lastrowid
        cursor.close()
    finally:
        conn.close()
    return last_id

def fetch_one(sql, params=()):
    conn = get_db_connection()
    sql = adapt_sql(sql)
    try:
        if CURRENT_ENGINE == "mysql":
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            row = cursor.fetchone()
            cursor.close()
            return row
        else:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            cursor.close()
            return dict(row) if row else None
    finally:
        conn.close()

def fetch_all(sql, params=()):
    conn = get_db_connection()
    sql = adapt_sql(sql)
    try:
        if CURRENT_ENGINE == "mysql":
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        else:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]
    finally:
        conn.close()

# ==============================================================================
# User Authentication & Profile Queries
# ==============================================================================

def create_user(name, email, password_hash, roll_no="", phone="", department="Computer Science", role="student", is_verified=0):
    sql = """
        INSERT INTO users (name, email, password_hash, roll_no, phone, department, role, is_verified, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
    """
    return execute_query(sql, (
        name.strip(),
        email.strip().lower(),
        password_hash,
        roll_no.strip().upper() if roll_no else None,
        phone.strip(),
        department.strip(),
        role,
        1 if is_verified else 0
    ), return_id=True)

def get_user_by_id(user_id):
    return fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))

def get_user_by_email(email):
    return fetch_one("SELECT * FROM users WHERE LOWER(email) = %s", (email.strip().lower(),))

def get_user_by_roll(roll_no):
    if not roll_no:
        return None
    return fetch_one("SELECT * FROM users WHERE UPPER(roll_no) = %s", (roll_no.strip().upper(),))

def update_user_verification(user_id, verified=True):
    execute_query("UPDATE users SET is_verified = %s WHERE id = %s", (1 if verified else 0, user_id))

def update_user_password(user_id, password_hash):
    execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))

def update_user_profile(user_id, name, phone, department, roll_no=""):
    execute_query("""
        UPDATE users SET name = %s, phone = %s, department = %s, roll_no = %s
        WHERE id = %s
    """, (name.strip(), phone.strip(), department.strip(), roll_no.strip().upper() if roll_no else None, user_id))

def get_all_users(role=None, search=None):
    sql = "SELECT id, name, email, roll_no, phone, department, role, is_verified, is_active, created_at FROM users WHERE 1=1"
    params = []
    if role and role != "all":
        sql += " AND role = %s"
        params.append(role)
    if search:
        s = f"%{search.strip().lower()}%"
        sql += " AND (LOWER(name) LIKE %s OR LOWER(email) LIKE %s OR LOWER(roll_no) LIKE %s OR LOWER(department) LIKE %s)"
        params.extend([s, s, s, s])
    sql += " ORDER BY created_at DESC"
    return fetch_all(sql, params)

def toggle_user_active(user_id):
    u = get_user_by_id(user_id)
    if u:
        new_val = 0 if u.get("is_active") else 1
        execute_query("UPDATE users SET is_active = %s WHERE id = %s", (new_val, user_id))
        return new_val
    return None

def update_user_role(user_id, new_role):
    if new_role in ("student", "organizer", "admin"):
        execute_query("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))

# ==============================================================================
# Event Queries (Multiple Customizable Events)
# ==============================================================================

def create_event(title, description, department_restriction, event_date, event_time, venue, capacity, organizer_id, status="pending"):
    sql = """
        INSERT INTO events (title, description, department_restriction, event_date, event_time, venue, capacity, organizer_id, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_query(sql, (
        title.strip(),
        description.strip(),
        department_restriction.strip(),
        event_date,
        event_time.strip(),
        venue.strip(),
        int(capacity),
        organizer_id,
        status
    ), return_id=True)

def update_event(event_id, title, description, department_restriction, event_date, event_time, venue, capacity):
    execute_query("""
        UPDATE events 
        SET title = %s, description = %s, department_restriction = %s, 
            event_date = %s, event_time = %s, venue = %s, capacity = %s
        WHERE id = %s
    """, (title.strip(), description.strip(), department_restriction.strip(), event_date, event_time.strip(), venue.strip(), int(capacity), event_id))

def get_event_by_id(event_id):
    sql = """
        SELECT e.*, u.name as organizer_name, u.email as organizer_email, u.department as organizer_dept
        FROM events e
        JOIN users u ON e.organizer_id = u.id
        WHERE e.id = %s
    """
    return fetch_one(sql, (event_id,))

def get_all_approved_events(department=None, search=None):
    sql = """
        SELECT e.*, u.name as organizer_name,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id AND r.status = 'confirmed') as confirmed_count,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id AND r.status = 'waitlisted') as waitlist_count
        FROM events e
        JOIN users u ON e.organizer_id = u.id
        WHERE e.status = 'approved'
    """
    params = []
    if department and department != "All Departments":
        sql += " AND (e.department_restriction = %s OR e.department_restriction = 'All Departments')"
        params.append(department)
    if search:
        s = f"%{search.strip().lower()}%"
        sql += " AND (LOWER(e.title) LIKE %s OR LOWER(e.description) LIKE %s OR LOWER(e.venue) LIKE %s)"
        params.extend([s, s, s])
    sql += " ORDER BY e.event_date ASC, e.event_time ASC"
    return fetch_all(sql, params)

def get_organizer_events(organizer_id):
    sql = """
        SELECT e.*,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id AND r.status = 'confirmed') as confirmed_count,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id AND r.status = 'waitlisted') as waitlist_count,
               (SELECT COUNT(*) FROM entry_logs el WHERE el.event_id = e.id) as present_count
        FROM events e
        WHERE e.organizer_id = %s
        ORDER BY e.created_at DESC
    """
    return fetch_all(sql, (organizer_id,))

def get_all_events_for_admin(status=None):
    sql = """
        SELECT e.*, u.name as organizer_name, u.email as organizer_email,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id AND r.status = 'confirmed') as confirmed_count,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id AND r.status = 'waitlisted') as waitlist_count
        FROM events e
        JOIN users u ON e.organizer_id = u.id
    """
    params = []
    if status and status != "all":
        sql += " WHERE e.status = %s"
        params.append(status)
    sql += " ORDER BY e.created_at DESC"
    return fetch_all(sql, params)

def approve_event(event_id):
    execute_query("UPDATE events SET status = 'approved', rejection_reason = '' WHERE id = %s", (event_id,))

def reject_event(event_id, reason=""):
    execute_query("UPDATE events SET status = 'rejected', rejection_reason = %s WHERE id = %s", (reason.strip(), event_id))

def get_event_capacity_stats(event_id):
    e = get_event_by_id(event_id)
    if not e:
        return None
    capacity = e["capacity"]
    confirmed = fetch_one("SELECT COUNT(*) as cnt FROM registrations WHERE event_id = %s AND status = 'confirmed'", (event_id,))["cnt"]
    waitlisted = fetch_one("SELECT COUNT(*) as cnt FROM registrations WHERE event_id = %s AND status = 'waitlisted'", (event_id,))["cnt"]
    remaining = max(0, capacity - confirmed)
    return {
        "capacity": capacity,
        "confirmed": confirmed,
        "waitlisted": waitlisted,
        "remaining": remaining,
        "is_full": confirmed >= capacity
    }

# ==============================================================================
# Registration, Capacity & Waitlist System
# ==============================================================================

def register_for_event(event_id, user_id, registration_method="Profile"):
    """
    Register a user for an event:
    1. Prevents duplicate registration.
    2. Checks capacity:
       - If seats available: status = 'confirmed', generate cryptographic QR token & event pass.
       - If capacity full: status = 'waitlisted', assigns waitlist position.
    """
    # Duplicate check
    existing = fetch_one("SELECT * FROM registrations WHERE event_id = %s AND user_id = %s", (event_id, user_id))
    if existing:
        if existing["status"] in ("confirmed", "waitlisted"):
            return False, f"You are already registered for this event ({existing['status'].capitalize()}).", existing
        elif existing["status"] == "cancelled":
            # Re-activate registration
            execute_query("DELETE FROM registrations WHERE id = %s", (existing["id"],))

    event = get_event_by_id(event_id)
    user = get_user_by_id(user_id)
    if not event or not user:
        return False, "Event or user not found.", None

    stats = get_event_capacity_stats(event_id)

    if not stats["is_full"]:
        # Direct Confirmation
        import qr_service
        import email_service

        token = qr_service.generate_secure_token()
        pass_rel, qr_rel = qr_service.generate_qr_ticket(
            token=token,
            guest_name=user["name"],
            roll_no=user["roll_no"] or "Student",
            department=user["department"],
            event_title=event["title"]
        )

        reg_id = execute_query("""
            INSERT INTO registrations (event_id, user_id, status, waitlist_position, qr_token, qr_image_path, registration_method)
            VALUES (%s, %s, 'confirmed', 0, %s, %s, %s)
        """, (event_id, user_id, token, pass_rel, registration_method), return_id=True)

        reg = fetch_one("SELECT * FROM registrations WHERE id = %s", (reg_id,))
        email_service.send_ticket_email(
            guest_name=user["name"],
            to_email=user["email"],
            roll_no=user["roll_no"] or "Student",
            department=user["department"],
            token=token,
            qr_image_path=pass_rel,
            event_title=event["title"]
        )

        return True, "Registration Confirmed! Your QR admission ticket has been generated.", reg

    else:
        # Event is Full -> Queue on Waitlist
        import email_service

        next_waitlist_pos = stats["waitlisted"] + 1
        reg_id = execute_query("""
            INSERT INTO registrations (event_id, user_id, status, waitlist_position, qr_token, qr_image_path, registration_method)
            VALUES (%s, %s, 'waitlisted', %s, NULL, NULL, %s)
        """, (event_id, user_id, next_waitlist_pos, registration_method), return_id=True)

        reg = fetch_one("SELECT * FROM registrations WHERE id = %s", (reg_id,))
        email_service.send_waitlist_email(
            guest_name=user["name"],
            to_email=user["email"],
            event_title=event["title"],
            waitlist_pos=next_waitlist_pos
        )

        return True, f"Event capacity is full! You have been placed on the official waitlist at position #{next_waitlist_pos}.", reg

def cancel_registration(registration_id, user_id=None):
    """
    Cancel an existing registration.
    If the cancelled registration was 'confirmed', automatically promotes
    the first waitlisted student (waitlist_position = 1) to 'confirmed'!
    """
    sql = "SELECT * FROM registrations WHERE id = %s"
    params = [registration_id]
    if user_id:
        sql += " AND user_id = %s"
        params.append(user_id)

    reg = fetch_one(sql, params)
    if not reg or reg["status"] == "cancelled":
        return False, "Registration not found or already cancelled."

    prev_status = reg["status"]
    event_id = reg["event_id"]

    # Mark as cancelled
    execute_query("UPDATE registrations SET status = 'cancelled', waitlist_position = 0 WHERE id = %s", (registration_id,))

    promoted_user = None
    if prev_status == "confirmed":
        # Find next waitlisted student
        next_waitlist = fetch_one("""
            SELECT * FROM registrations 
            WHERE event_id = %s AND status = 'waitlisted' 
            ORDER BY waitlist_position ASC LIMIT 1
        """, (event_id,))

        if next_waitlist:
            import qr_service
            import email_service

            event = get_event_by_id(event_id)
            promoted_u = get_user_by_id(next_waitlist["user_id"])

            token = qr_service.generate_secure_token()
            pass_rel, qr_rel = qr_service.generate_qr_ticket(
                token=token,
                guest_name=promoted_u["name"],
                roll_no=promoted_u["roll_no"] or "Student",
                department=promoted_u["department"],
                event_title=event["title"]
            )

            execute_query("""
                UPDATE registrations 
                SET status = 'confirmed', waitlist_position = 0, qr_token = %s, qr_image_path = %s
                WHERE id = %s
            """, (token, pass_rel, next_waitlist["id"]))

            # Shift remaining waitlisted positions down by 1
            execute_query("""
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
            promoted_user = promoted_u

    return True, "Registration cancelled successfully." + (f" Waitlist #1 ({promoted_user['name']}) has been automatically promoted to confirmed!" if promoted_user else "")

def get_user_registrations(user_id):
    sql = """
        SELECT r.*, e.title as event_title, e.event_date, e.event_time, e.venue, e.department_restriction,
               u.name as organizer_name,
               el.id as entry_id, el.scan_time, el.gate_number,
               CASE WHEN el.id IS NOT NULL THEN 'Present' ELSE 'Absent' END as attendance_status
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        JOIN users u ON e.organizer_id = u.id
        LEFT JOIN entry_logs el ON r.id = el.registration_id
        WHERE r.user_id = %s
        ORDER BY r.created_at DESC
    """
    return fetch_all(sql, (user_id,))

def get_registration_by_id(reg_id):
    sql = """
        SELECT r.*, e.title as event_title, e.event_date, e.event_time, e.venue,
               u.name as student_name, u.email as student_email, u.roll_no as student_roll, u.department as student_dept,
               el.scan_time, el.gate_number
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        JOIN users u ON r.user_id = u.id
        LEFT JOIN entry_logs el ON r.id = el.registration_id
        WHERE r.id = %s
    """
    return fetch_one(sql, (reg_id,))

def get_registration_by_token(token):
    sql = """
        SELECT r.*, e.title as event_title, e.event_date, e.event_time, e.venue, e.capacity,
               u.name as student_name, u.email as student_email, u.roll_no as student_roll, u.department as student_dept,
               el.id as entry_id, el.scan_time, el.gate_number, el.scanned_by,
               CASE WHEN el.id IS NOT NULL THEN 'Present' ELSE 'Absent' END as attendance_status
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        JOIN users u ON r.user_id = u.id
        LEFT JOIN entry_logs el ON r.id = el.registration_id
        WHERE r.qr_token = %s
    """
    return fetch_one(sql, (token.strip(),))

def get_event_attendees(event_id, status_filter=None):
    sql = """
        SELECT r.*, u.name as student_name, u.email as student_email, u.roll_no as student_roll, u.phone as student_phone, u.department as student_dept,
               el.id as entry_id, el.scan_time, el.gate_number, el.scanned_by,
               CASE WHEN el.id IS NOT NULL THEN 'Present' ELSE 'Absent' END as attendance_status
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN entry_logs el ON r.id = el.registration_id
        WHERE r.event_id = %s
    """
    params = [event_id]
    if status_filter and status_filter != "all":
        sql += " AND r.status = %s"
        params.append(status_filter)
    sql += " ORDER BY r.status ASC, r.waitlist_position ASC, r.created_at ASC"
    return fetch_all(sql, params)

# ==============================================================================
# Gate Attendance Queries (Single Scan Validation & SQL Joins)
# ==============================================================================

def record_gate_entry(registration_id, gate_number="Main Gate 1", scanned_by="Staff Scanner"):
    # Check if already scanned
    existing = fetch_one("SELECT * FROM entry_logs WHERE registration_id = %s", (registration_id,))
    if existing:
        return False, existing

    reg = fetch_one("SELECT * FROM registrations WHERE id = %s", (registration_id,))
    if not reg:
        return False, None

    entry_id = execute_query("""
        INSERT INTO entry_logs (registration_id, event_id, gate_number, scanned_by, status)
        VALUES (%s, %s, %s, %s, 'ALLOWED')
    """, (registration_id, reg["event_id"], gate_number, scanned_by), return_id=True)

    new_log = fetch_one("SELECT * FROM entry_logs WHERE id = %s", (entry_id,))
    return True, new_log

def get_event_present_list(event_id):
    sql = """
        SELECT r.id as reg_id, r.qr_token, r.registration_method,
               u.name as student_name, u.roll_no as student_roll, u.department as student_dept, u.email as student_email,
               el.scan_time, el.gate_number, el.scanned_by
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        INNER JOIN entry_logs el ON r.id = el.registration_id
        WHERE r.event_id = %s AND r.status = 'confirmed'
        ORDER BY el.scan_time DESC
    """
    return fetch_all(sql, (event_id,))

def get_event_absent_list(event_id):
    sql = """
        SELECT r.id as reg_id, r.qr_token, r.registration_method, r.created_at,
               u.name as student_name, u.roll_no as student_roll, u.department as student_dept, u.email as student_email
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN entry_logs el ON r.id = el.registration_id
        WHERE r.event_id = %s AND r.status = 'confirmed' AND el.id IS NULL
        ORDER BY u.name ASC
    """
    return fetch_all(sql, (event_id,))

# ==============================================================================
# Eligible Students Reference Master Table
# ==============================================================================

def get_eligible_student(roll_no):
    if not roll_no:
        return None
    return fetch_one("SELECT * FROM eligible_students WHERE LOWER(roll_no) = LOWER(%s)", (roll_no.strip(),))

def get_all_eligible_students():
    return fetch_all("SELECT * FROM eligible_students ORDER BY department, roll_no")

def add_eligible_student(roll_no, name, department, course="MCA", email=""):
    existing = get_eligible_student(roll_no)
    if existing:
        return False
    execute_query("""
        INSERT INTO eligible_students (roll_no, name, department, course, email, is_eligible)
        VALUES (%s, %s, %s, %s, %s, 1)
    """, (roll_no.strip().upper(), name.strip(), department.strip(), course.strip(), email.strip()))
    return True

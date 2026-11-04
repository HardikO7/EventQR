"""
EventQR - Campus Events Platform Database Seeder
Real-world University Datasets: Freshers at CCC Complex, Onam at SET Courtyard, Build with AI Hackathon, etc.
"""

import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from PIL import Image, ImageDraw, ImageFont

from config import Config
import database
import qr_service

def setup_database():
    print(f"[*] Initializing EventQR database schema (Active Engine: {database.CURRENT_ENGINE.upper()})...")

    conn = database.get_db_connection()
    cursor = conn.cursor()
    is_sqlite = (database.CURRENT_ENGINE == "sqlite")
    auto_inc = "AUTOINCREMENT" if is_sqlite else "AUTO_INCREMENT"
    ts_now = "CURRENT_TIMESTAMP"

    tables = ["entry_logs", "registrations", "events", "email_otps", "users", "eligible_students", "guests", "admin_users"]
    for t in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {t}")
        except Exception:
            pass

    # 1. Users
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY {auto_inc},
            name VARCHAR(150) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            roll_no VARCHAR(50) UNIQUE,
            phone VARCHAR(25) DEFAULT '',
            department VARCHAR(100) DEFAULT 'Computer Science',
            role VARCHAR(20) DEFAULT 'student',
            is_verified BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT {ts_now}
        )
    """)

    # 2. Email OTPs
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS email_otps (
            id INTEGER PRIMARY KEY {auto_inc},
            email VARCHAR(150) NOT NULL,
            otp_code VARCHAR(10) NOT NULL,
            purpose VARCHAR(30) NOT NULL,
            expires_at DATETIME NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT {ts_now}
        )
    """)

    # 3. Events
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY {auto_inc},
            title VARCHAR(255) NOT NULL,
            description TEXT,
            department_restriction VARCHAR(100) DEFAULT 'All Departments',
            event_date DATE NOT NULL,
            event_time VARCHAR(50) DEFAULT '10:00 AM',
            venue VARCHAR(255) NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 50,
            organizer_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            rejection_reason TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT {ts_now}
        )
    """)

    # 4. Registrations
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY {auto_inc},
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'confirmed',
            waitlist_position INTEGER DEFAULT 0,
            qr_token VARCHAR(64) UNIQUE,
            qr_image_path VARCHAR(255),
            registration_method VARCHAR(30) DEFAULT 'Profile',
            created_at TIMESTAMP DEFAULT {ts_now},
            UNIQUE (event_id, user_id)
        )
    """)

    # 5. Entry Logs
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS entry_logs (
            id INTEGER PRIMARY KEY {auto_inc},
            registration_id INTEGER NOT NULL UNIQUE,
            event_id INTEGER NOT NULL,
            scan_time TIMESTAMP DEFAULT {ts_now},
            gate_number VARCHAR(50) DEFAULT 'Main Gate 1',
            scanned_by VARCHAR(100) DEFAULT 'Gate Scanner',
            status VARCHAR(50) DEFAULT 'ALLOWED',
            notes VARCHAR(255) DEFAULT 'Checked in'
        )
    """)

    # 6. Eligible Students Reference Pool
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS eligible_students (
            id INTEGER PRIMARY KEY {auto_inc},
            roll_no VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(150) NOT NULL,
            department VARCHAR(100) NOT NULL,
            course VARCHAR(50) DEFAULT 'MCA',
            semester VARCHAR(20) DEFAULT '3rd Semester',
            email VARCHAR(150),
            is_eligible BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT {ts_now}
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("[+] Database schema successfully created.")

def seed_users():
    print("[*] Seeding university user accounts...")
    users = [
        # Admin Account (Imaginary professional name)
        ("Dr. Arvind Swaminathan", "admin@campus.edu", generate_password_hash("admin123"), "FACULTY-ADM-01", "+91 98765 00001", "Computer Science", "admin", 1),
        # Organizer Account
        ("Prof. Neha Deshmukh", "organizer@campus.edu", generate_password_hash("organizer123"), "FACULTY-CS-04", "+91 98765 00002", "Computer Science", "organizer", 1),
        # Real-world Student Accounts
        ("Rohan Sen", "rohan.sen@campus.edu", generate_password_hash("student123"), "25CS101", "+91 98765 11001", "Computer Science", "student", 1),
        ("Kavya Nair", "kavya.nair@campus.edu", generate_password_hash("student123"), "25CS102", "+91 98765 11002", "Computer Science", "student", 1),
        ("Aditya Sharma", "aditya.s@campus.edu", generate_password_hash("student123"), "25CS103", "+91 98765 11003", "Computer Science", "student", 1),
        ("Meera Krishnan", "meera.k@campus.edu", generate_password_hash("student123"), "25CS104", "+91 98765 11004", "Computer Science", "student", 1),
        ("Tanmay Joshi", "tanmay.j@campus.edu", generate_password_hash("student123"), "25CS105", "+91 98765 11005", "Computer Science", "student", 1),
        ("Aarav Mehta", "aarav.m@campus.edu", generate_password_hash("student123"), "25CS106", "+91 98765 11006", "Computer Science", "student", 1),
        ("Varun Pillai", "varun.p@campus.edu", generate_password_hash("student123"), "25ME201", "+91 98765 11007", "Mechanical Engineering", "student", 1),
    ]

    for name, email, pw, roll, phone, dept, role, verif in users:
        database.create_user(name, email, pw, roll, phone, dept, role, verif)
    print(f"[+] Created {len(users)} users across Admin, Faculty, and Students.")

def seed_events():
    print("[*] Seeding real-world campus events...")
    admin = database.get_user_by_email("admin@campus.edu")
    organizer = database.get_user_by_email("organizer@campus.edu")

    events = [
        # Event 1: CS Freshers at CCC Complex
        ("CS Department Freshers' Welcome 2026",
         "Annual welcome celebration for the incoming Computer Science batch. Faculty orientation, interactive senior sessions, cultural performances, and evening refreshments.",
         "Computer Science", "2026-11-14", "03:00 PM", "CCC Complex (Central Computing Center)",
         5, organizer["id"], "approved"),

        # Event 2: Onam at School of Engineering & Technology
        ("Annual Onam Cultural Celebration & Feast",
         "Traditional university cultural festival featuring Pookkalam floral carpet competition, Thiruvathira folk dance, traditional music, and authentic grand Onasadhya feast for all campus departments.",
         "All Departments", "2026-11-18", "11:30 AM", "School of Engineering and Technology (SET Courtyard)",
         150, organizer["id"], "approved"),

        # Event 3: Build with AI Hackathon at CCC Innovation Lab
        ("Build with AI: 24-Hour Campus Hackathon",
         "Intensive 24-hour campus prototyping challenge. Teams design and deploy practical AI agents, computer vision pipelines, and automated developer tools. High-speed compute and mentoring provided.",
         "Computer Science", "2026-11-22", "09:00 AM", "CCC Innovation Lab & Seminar Hall",
         40, organizer["id"], "approved"),

        # Event 4: Career & Placement Conclave at Auditorium
        ("Campus Placement & Career Conclave 2026",
         "Annual career summit featuring industry recruiters, alumni technology panels, resume clinics, and pre-placement sessions for graduating students across engineering and science streams.",
         "All Departments", "2026-12-02", "10:00 AM", "Main University Auditorium",
         200, admin["id"], "approved"),

        # Event 5: Sports Championship (Pending review for admin approval queue)
        ("Inter-Department Badminton & Futsal Championship",
         "Annual inter-department athletic championship spanning men's and women's badminton doubles and 5-a-side futsal tournament.",
         "All Departments", "2026-12-08", "08:30 AM", "University Sports Complex & Indoor Stadium",
         60, organizer["id"], "pending")
    ]

    for title, desc, dept, date, time, venue, cap, org_id, st in events:
        database.create_event(title, desc, dept, date, time, venue, cap, org_id, st)
    print(f"[+] Created {len(events)} real-world campus events.")

def seed_registrations_and_waitlist():
    print("[*] Seeding registrations, capacity checks, and waitlist queues...")
    event1 = database.get_event_by_id(1) # CS Freshers (Capacity: 5)

    # Register 5 students to fill capacity
    confirmed_students = [
        "rohan.sen@campus.edu",
        "kavya.nair@campus.edu",
        "aditya.s@campus.edu",
        "meera.k@campus.edu",
        "tanmay.j@campus.edu"
    ]

    for email in confirmed_students:
        user = database.get_user_by_email(email)
        success, msg, reg = database.register_for_event(event1["id"], user["id"], "Profile")
        print(f"    - {user['name']}: {msg}")

    # Register 6th student -> automatically queued as Waitlist #1!
    user6 = database.get_user_by_email("aarav.m@campus.edu")
    success, msg, reg6 = database.register_for_event(event1["id"], user6["id"], "Profile")
    print(f"    - {user6['name']} (Waitlist test): {msg}")

    # Gate check-ins: Rohan Sen and Kavya Nair checked in as Present
    reg_rohan = database.fetch_one("SELECT * FROM registrations WHERE event_id = 1 AND user_id = (SELECT id FROM users WHERE email = 'rohan.sen@campus.edu')")
    reg_kavya = database.fetch_one("SELECT * FROM registrations WHERE event_id = 1 AND user_id = (SELECT id FROM users WHERE email = 'kavya.nair@campus.edu')")

    if reg_rohan:
        database.record_gate_entry(reg_rohan["id"], "CCC Main Gate", "Staff Desk A")
        print("[+] Check-in recorded for Rohan Sen (Present at CCC Main Gate)")
    if reg_kavya:
        database.record_gate_entry(reg_kavya["id"], "CCC Main Gate", "Staff Desk A")
        print("[+] Check-in recorded for Kavya Nair (Present at CCC Main Gate)")

def seed_eligibility_pool():
    students = [
        ("25CS101", "Rohan Sen", "Computer Science", "MCA", "rohan.sen@campus.edu"),
        ("25CS102", "Kavya Nair", "Computer Science", "MCA", "kavya.nair@campus.edu"),
        ("25CS103", "Aditya Sharma", "Computer Science", "MCA", "aditya.s@campus.edu"),
        ("25CS104", "Meera Krishnan", "Computer Science", "M.Sc Computer Science", "meera.k@campus.edu"),
        ("25CS105", "Tanmay Joshi", "Computer Science", "MCA", "tanmay.j@campus.edu"),
        ("25CS106", "Aarav Mehta", "Computer Science", "MCA", "aarav.m@campus.edu"),
        ("25ME201", "Varun Pillai", "Mechanical Engineering", "M.Tech Mechanical", "varun.p@campus.edu"),
    ]
    for roll, name, dept, crs, email in students:
        database.add_eligible_student(roll, name, dept, crs, email)
    print(f"[+] Seeded {len(students)} students in eligibility reference pool.")

if __name__ == "__main__":
    setup_database()
    seed_users()
    seed_events()
    seed_registrations_and_waitlist()
    seed_eligibility_pool()
    print("\n[SUCCESS] EventPass Campus Platform Setup Complete!")

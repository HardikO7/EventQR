"""
EventQR - MySQL / TiDB Schema Initializer & Sample Data Seeder
Reads schema.sql and connects via mysql-connector-python.
"""

from pathlib import Path
from werkzeug.security import generate_password_hash
from config import Config
import database

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _run_schema_statements(drop_existing=False):
    """Create database (if needed) and execute table definitions from schema.sql."""
    if not drop_existing:
        try:
            conn = database.get_db_connection(use_database=True)
            cursor = conn.cursor()
        except Exception:
            conn = database.get_db_connection(use_database=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE `{Config.MYSQL_DB}`")
    else:
        conn = database.get_db_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{Config.MYSQL_DB}`")
        for table in ("entry_logs", "registrations", "events", "email_otps", "users", "eligible_students"):
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    for stmt in schema_sql.split(";"):
        clean = "\n".join(line for line in stmt.splitlines() if not line.strip().startswith("--")).strip()
        if clean and not clean.upper().startswith(("CREATE DATABASE", "USE ")):
            cursor.execute(clean)

    conn.commit()
    cursor.close()
    conn.close()


def seed_sample_data():
    """Populate initial campus accounts, events, passes, check-ins, and eligible students."""
    users = [
        ("Dr. Suresh Joseph", "admin@campus.edu", "admin123", "FACULTY-ADM-01", "+91 98765 00001", "Computer Science", "admin"),
        ("Prof. Neha Deshmukh", "organizer@campus.edu", "organizer123", "FACULTY-CS-04", "+91 98765 00002", "Computer Science", "organizer"),
        ("Rohan Sen", "rohan.sen@campus.edu", "student123", "25CS101", "+91 98765 11001", "Computer Science", "student"),
        ("Kavya Nair", "kavya.nair@campus.edu", "student123", "25CS102", "+91 98765 11002", "Computer Science", "student"),
        ("Aditya Sharma", "aditya.s@campus.edu", "student123", "25CS103", "+91 98765 11003", "Computer Science", "student"),
        ("Meera Krishnan", "meera.k@campus.edu", "student123", "25CS104", "+91 98765 11004", "Computer Science", "student"),
        ("Tanmay Joshi", "tanmay.j@campus.edu", "student123", "25CS105", "+91 98765 11005", "Computer Science", "student"),
        ("Aarav Mehta", "aarav.m@campus.edu", "student123", "25CS106", "+91 98765 11006", "Computer Science", "student"),
        ("Varun Pillai", "varun.p@campus.edu", "student123", "25ME201", "+91 98765 11007", "Mechanical Engineering", "student"),
    ]
    for name, email, pwd, roll, phone, dept, role in users:
        database.create_user(name, email, generate_password_hash(pwd), roll, phone, dept, role, is_verified=1)

    admin = database.get_user_by_email("admin@campus.edu")
    organizer = database.get_user_by_email("organizer@campus.edu")

    events = [
        ("CS Department Freshers' Welcome 2026",
         "Annual welcome celebration for the incoming Computer Science batch.",
         "Computer Science", "2026-11-14", "03:00 PM", "CCC Complex (Central Computing Center)", 350, organizer["id"], "approved"),
        ("Annual Onam Cultural Celebration & Feast",
         "Traditional university cultural festival featuring Pookkalam, Thiruvathira dance, and Onasadhya feast.",
         "All Departments", "2026-11-18", "11:30 AM", "School of Engineering and Technology (SET Courtyard)", 150, organizer["id"], "approved"),
        ("Build with AI: 24-Hour Campus Hackathon",
         "Intensive 24-hour campus prototyping challenge for AI and computer vision pipelines.",
         "Computer Science", "2026-11-22", "09:00 AM", "CCC Innovation Lab & Seminar Hall", 40, organizer["id"], "approved"),
        ("Campus Placement & Career Conclave 2026",
         "Annual career summit featuring industry recruiters, alumni panels, and resume clinics.",
         "All Departments", "2026-12-02", "10:00 AM", "Main University Auditorium", 200, admin["id"], "approved"),
        ("Inter-Department Badminton & Futsal Championship",
         "Annual inter-department athletic championship.",
         "All Departments", "2026-12-08", "08:30 AM", "University Sports Complex & Indoor Stadium", 60, organizer["id"], "pending"),
    ]
    for title, desc, dept, ev_date, ev_time, venue, cap, org_id, status in events:
        database.create_event(title, desc, dept, ev_date, ev_time, venue, cap, org_id, status)

    event1 = database.get_event_by_id(1)
    if event1:
        for email in ("rohan.sen@campus.edu", "kavya.nair@campus.edu", "aditya.s@campus.edu", "meera.k@campus.edu", "tanmay.j@campus.edu"):
            u = database.get_user_by_email(email)
            database.register_for_event(event1["id"], u["id"], "Profile", send_email=False)

        for email in ("rohan.sen@campus.edu", "kavya.nair@campus.edu"):
            reg = database.fetch_one(
                "SELECT r.id FROM registrations r JOIN users u ON r.user_id = u.id WHERE r.event_id = %s AND u.email = %s",
                (event1["id"], email),
            )
            if reg:
                database.record_gate_entry(reg["id"], "CCC Main Gate", "Staff Desk A")

    eligible = [
        ("25CS101", "Rohan Sen", "Computer Science", "MCA", "rohan.sen@campus.edu"),
        ("25CS102", "Kavya Nair", "Computer Science", "MCA", "kavya.nair@campus.edu"),
        ("25CS103", "Aditya Sharma", "Computer Science", "MCA", "aditya.s@campus.edu"),
        ("25CS104", "Meera Krishnan", "Computer Science", "M.Sc Computer Science", "meera.k@campus.edu"),
        ("25CS105", "Tanmay Joshi", "Computer Science", "MCA", "tanmay.j@campus.edu"),
        ("25CS106", "Aarav Mehta", "Computer Science", "MCA", "aarav.m@campus.edu"),
        ("25ME201", "Varun Pillai", "Mechanical Engineering", "M.Tech Mechanical", "varun.p@campus.edu"),
    ]
    for roll, name, dept, crs, email in eligible:
        database.add_eligible_student(roll, name, dept, crs, email)


def ensure_database():
    """Ensure tables exist and auto-seed sample data only when the users table is empty."""
    _run_schema_statements(drop_existing=False)
    row = database.fetch_one("SELECT COUNT(*) as c FROM users")
    if row and row["c"] == 0:
        seed_sample_data()


def setup_database():
    """Reset MySQL schema and seed sample campus data."""
    print(f"[*] Initializing MySQL database '{Config.MYSQL_DB}' at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}...")
    _run_schema_statements(drop_existing=True)
    seed_sample_data()
    print("[SUCCESS] MySQL EventQR database initialized and seeded.")


if __name__ == "__main__":
    setup_database()

"""
EventQR MySQL Database Inspector Utility
Usage:
    python view_db.py               (Overview of all tables)
    python view_db.py users         (Show all registered users)
    python view_db.py events        (Show all campus events)
    python view_db.py passes        (Show all issued admission tickets)
    python view_db.py otps          (Show recent email verification OTPs)
    python view_db.py logs          (Show live gate check-in admissions)
"""

import sys
import database
from config import Config


def show_overview():
    print("\n" + "=" * 65)
    print(f" EVENTQR MYSQL DATABASE OVERVIEW ({Config.MYSQL_DB})")
    print("=" * 65)
    tables = [
        ("users", "User accounts (Students, Organizers, Admins)"),
        ("events", "Published & proposed campus events"),
        ("registrations", "Issued admission passes, tokens & waitlists"),
        ("email_otps", "Real-time OTP verification codes & TTLs"),
        ("entry_logs", "Live gate check-in logs & entry timestamps"),
        ("eligible_students", "Master student eligibility verification table"),
    ]
    for table, desc in tables:
        count = database.fetch_one(f"SELECT COUNT(*) as c FROM {table}")["c"]
        print(f" * {table:<18} | {count:>4} rows | {desc}")
    print("=" * 65 + "\n")


def show_users():
    users = database.fetch_all("SELECT id, name, email, roll_no, role, is_verified FROM users ORDER BY id")
    print(f"\nUSERS ({len(users)} Total)")
    print("-" * 80)
    for u in users:
        ver = "Yes" if u.get('is_verified') else "No"
        print(f"{u['id']:<4} {u['name']:<20} {u['email']:<28} {u.get('roll_no') or '-':<14} {u['role']:<10} {ver}")


def show_events():
    events = database.fetch_all("SELECT id, title, event_date, event_time, capacity, status FROM events ORDER BY id")
    print(f"\nEVENTS ({len(events)} Total)")
    print("-" * 85)
    for e in events:
        print(f"{e['id']:<4} {e['title'][:28]:<30} {e.get('event_date',''):<12} {e.get('event_time',''):<10} {e.get('capacity',0):<8} {e['status']}")


def show_passes():
    regs = database.fetch_all("""
        SELECT r.id, u.name, u.roll_no, e.title, r.status, r.qr_token, r.waitlist_position
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        JOIN events e ON r.event_id = e.id
        ORDER BY r.id DESC
    """)
    print(f"\nREGISTRATIONS & PASSES ({len(regs)} Total)")
    print("-" * 90)
    for r in regs:
        tok = (r['qr_token'][:12] + "...") if r['qr_token'] else "N/A (Waitlist)"
        st = f"WAIT #{r.get('waitlist_position', 1)}" if r['status'] == 'waitlisted' else r['status'].upper()
        print(f"{r['id']:<4} {r['name']:<18} {r.get('roll_no') or '-':<14} {r['title'][:26]:<28} {st:<12} {tok}")


def show_otps():
    otps = database.fetch_all("SELECT id, email, otp_code, purpose, expires_at, is_used FROM email_otps ORDER BY created_at DESC LIMIT 15")
    print("\nRECENT EMAIL OTPS (Latest 15)")
    print("-" * 85)
    for o in otps:
        print(f"{o['id']:<4} {o['email']:<28} {o['otp_code']:<8} {o['purpose']:<15} {o['expires_at']} | {'Used' if o.get('is_used') else 'Active'}")


def show_logs():
    logs = database.fetch_all("""
        SELECT l.id, u.name, u.roll_no, e.title, l.gate_number, l.scan_time
        FROM entry_logs l
        JOIN registrations r ON l.registration_id = r.id
        JOIN users u ON r.user_id = u.id
        JOIN events e ON r.event_id = e.id
        ORDER BY l.scan_time DESC
    """)
    print(f"\nGATE ENTRY LOGS ({len(logs)} Total)")
    print("-" * 85)
    for l in logs:
        print(f"{l['id']:<4} {l['name']:<18} {l.get('roll_no') or '-':<14} {l['title'][:22]:<24} {l['gate_number']:<14} {str(l['scan_time'])[:16]}")


if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    commands = {
        "users": show_users, "user": show_users,
        "events": show_events, "event": show_events,
        "passes": show_passes, "tickets": show_passes, "registrations": show_passes,
        "otps": show_otps, "otp": show_otps,
        "logs": show_logs, "gates": show_logs, "entry": show_logs,
    }
    commands.get(arg, show_overview)()

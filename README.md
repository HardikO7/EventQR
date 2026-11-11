# EventQR (EventPass) - Campus Event & QR Gate Entry System

**MCA Mini Project — Pondicherry University**
- **Student:** Hardik Gupta (`25MCA00PY0031`)
- **Project Guide & HOD:** Dr. Suresh Joseph, Professor and Head, Department of Computer Science

---

## Core Architecture
- **Web Application (`app.py`):** Flask 3+ multi-role portal (`student`, `organizer`, `admin`) with password + 6-digit Email OTP login and Two-Factor pass retrieval.
- **Database (`database.py`, `schema.sql`):** MySQL / TiDB Cloud Serverless via `mysql-connector-python` (`certifi` TLS auto-enabled for cloud hosts).
- **QR Ticketing (`qr_service.py`):** Cryptographic 32-char hex tokens (`secrets.token_hex(16)`) rendered into branded pass PNGs (served dynamically via `/ticket/<token>/image`).
- **Email Service (`email_service.py`, `otp_service.py`):** Gmail SMTP OTP & pass delivery (async background thread locally; synchronous in Vercel serverless mode).
- **Gate Validation (`scanner.py` & `/scanner`):** Web browser camera scanner (`jsQR`) + optional standalone OpenCV/`pyzbar` desktop scanner (`pip install opencv-python-headless pyzbar`).
- **Roster Exports (`export_service.py`):** ReportLab PDF & OpenPyXL Excel attendance reports.

---

## Local Setup (MySQL)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env` with your MySQL and Gmail SMTP settings (see `.env.example`).
3. Start the web server (auto-initializes tables & sample data if DB is empty):
   ```bash
   python app.py
   ```
4. Inspect database tables via CLI:
   ```bash
   python view_db.py
   ```

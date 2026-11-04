# EventQR: AI-Powered Student Verification & QR-Based Event Entry Management System

**MCA Mini Project — Pondicherry University**  
- **Student Name:** Hardik Gupta  
- **Enrollment Number:** 25MCA00PY0031  
- **Course & Semester:** MCA — 2nd Year, 3rd Semester  
- **Project Supervisor & HOD:** Dr. Suresh Joseph, Professor and Head  
- **Department:** Department of Computer Science, School of Engineering & Technology, Pondicherry University  

---

## 1. Project Overview

**EventQR** is an end-to-end event access management and attendance analytics web system engineered to digitize guest registration, automate student eligibility verification, eliminate ticket forgery, and streamline entry gate validation for university symposiums, fests, and conferences.

### Key Value Propositions
- **Eliminates Manual Paperwork:** Automated form filling powered by Computer Vision and Optical Character Recognition (OCR).
- **Prevents Fake Registrations:** Live cross-referencing against the university's pre-loaded student database ensures only eligible students (e.g. Department of Computer Science) are admitted.
- **Anti-Forgery Security:** Tickets encode cryptographically random, unpredictable 32-character tokens generated via Python's `secrets` module rather than sequential IDs.
- **Single-Use Gate Validation:** Real-time OpenCV / pyzbar gate scanning permits entry exactly once per guest and rejects all duplicate/forged scans.
- **Live SQL-Join Attendance:** Present and Absent lists are dynamically derived through relational SQL joins between `guests` and `entry_logs` ensuring zero status drift.
- **Executive Reporting & Analytics:** Pandas-powered dashboard showing no-show rates, peak entry-time histograms, and one-click PDF (ReportLab) & Excel (openpyxl) downloads.

---

## 2. System Architecture

The system is organized into four distinct architectural tiers:

```
+--------------------------------------------------------------------------+
|                             USER TIER                                    |
|      Student / Attendee                    Organizer / Gate Staff        |
|  (Registers, Uploads ID, Downloads Pass)     (Scans QR, Views Analytics) |
+--------------------------------------------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
|                        PRESENTATION TIER (Web UI)                        |
|  - Landing & Event Showcase               - Web Gate Scanner             |
|  - AI OCR Registration Desk               - Live Present/Absent Lists    |
|  - E-Pass Badge & Ticket Confirmation     - Analytics Dashboard          |
|  - Ticket Retrieval Lookup                - PDF / Excel Export Center    |
+--------------------------------------------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
|                        APPLICATION TIER (Flask)                          |
|  - app.py                : Route handlers, Session auth, REST APIs       |
|  - ocr_service.py        : OpenCV image preprocessing & ID OCR engine    |
|  - qr_service.py         : Cryptographic token & event pass generation   |
|  - email_service.py      : Automated smtplib delivery with attachments   |
|  - scanner.py            : Standalone OpenCV + pyzbar live webcam script |
|  - analytics_service.py  : Pandas aggregation & no-show metrics         |
|  - export_service.py     : ReportLab PDF and openpyxl Excel exports      |
+--------------------------------------------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
|                        DATABASE TIER (MySQL / SQLite)                    |
|  - events                : Symposium metadata & venues                   |
|  - eligible_students     : Master eligibility reference records          |
|  - guests                : Registered attendees & cryptographic tokens   |
|  - entry_logs            : One row per gate scan (unique guest_id)       |
|  - admin_users           : Hashed organizer credentials                  |
+--------------------------------------------------------------------------+
```

---

## 3. Technology Stack

| Category | Technology | Purpose |
|---|---|---|
| **Programming Language** | Python 3.10+ / 3.14 | Core backend logic & computer vision |
| **Web Framework** | Flask 3.1 | REST routing, Jinja2 templating, sessions |
| **Frontend** | HTML5, CSS3, Bootstrap 5, FontAwesome 6 | Responsive, glassmorphic UI |
| **Relational Database** | MySQL (with SQLite seamless fallback) | Storage of events, students, tokens, entry logs |
| **Computer Vision** | OpenCV (`cv2`) & `pyzbar` | Real-time webcam capture & QR code decoding |
| **AI / OCR** | OpenCV + `pytesseract` / OCR Engine | ID card text extraction & regex parsing |
| **Cryptographic Security**| Python `secrets` module | Unguessable 32-character security tokens |
| **QR Code Generation** | `qrcode[pil]` & Pillow (PIL) | High-resolution branded event badge passes |
| **Email Dispatch** | Python `smtplib` & `email.mime` | Automated email delivery with QR attachment |
| **Data Analytics** | Pandas | Groupby aggregation, hourly histograms, no-show rate |
| **PDF Export** | ReportLab 5.0 | Official university attendance documents |
| **Excel Export** | `openpyxl` & Pandas | Multi-sheet attendance spreadsheets |

---

## 4. Database Design & SQL Joins

As emphasized in Review Report 2 (Section 3.2), attendance status is computed dynamically through SQL joins rather than a static status column:

### Present List (Checked In)
```sql
SELECT g.id, g.name, g.roll_no, g.department, g.email, g.phone, 
       e.scan_time, e.gate_number, e.scanned_by
FROM guests g
INNER JOIN entry_logs e ON g.id = e.guest_id
WHERE g.event_id = 1
ORDER BY e.scan_time DESC;
```

### Absent List (Unchecked Registrations)
```sql
SELECT g.id, g.name, g.roll_no, g.department, g.email, g.phone, g.created_at
FROM guests g
LEFT JOIN entry_logs e ON g.id = e.guest_id
WHERE g.event_id = 1 AND e.id IS NULL
ORDER BY g.name ASC;
```

---

## 5. Quick Start Guide

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database & Seed Sample Assets
```bash
python init_db.py
```
This automatically creates the database schema, seeds the default symposium details, sets up 10 eligible students, registers sample attendees, and generates sample Pondicherry University ID cards for OCR testing!

### Step 3: Run the Web Application
```bash
python app.py
```
Open your browser and navigate to: **http://127.0.0.1:5000**

---

## 6. How to Run the Live Entry Scanner

You have **two** ways to scan passes:

### Option A: Web Browser Scanner
1. Sign in as Organizer at `http://127.0.0.1:5000/admin/login` (Username: `admin`, Password: `admin123`).
2. Go to **Gate Scanner** in the navbar.
3. Click **Start Camera** to use your webcam, or use the interactive **Token Validator** to test scans with 1 click.

### Option B: Standalone OpenCV Desktop Scanner (cv2 + pyzbar)
Run the desktop computer vision script:
```bash
# Live webcam scanner
python scanner.py

# Or test against a generated QR ticket image without a camera:
python scanner.py --image static/qr_codes/qr_12abb6e7c1d70822f1b5366e65435d08.png
```

---

## 7. Viva Demonstration Walkthrough

1. **AI ID Card Auto-Verification:**
   - Go to `/register`.
   - Click one of the demo ID card buttons (e.g. *Hardik Gupta* or *Ananya Roy*).
   - Observe the OpenCV OCR pipeline extracting Roll Number, Name, and confirming Department of Computer Science eligibility.
   - Click the *Karthik N (Mechanical Engineering)* button to demonstrate automatic rejection of ineligible students.

2. **Automated QR Pass & Email Delivery:**
   - Submit registration.
   - Observe the generated digital event badge with security token.
   - Check the **Sent Email Logs** tab under Admin to review the dispatched email receipt.

3. **Single-Use Gate Validation & Anti-Forgery:**
   - Scan the QR code at the Gate Scanner.
   - First scan gives a **GREEN "ACCESS GRANTED"** banner.
   - Scanning the same QR code a second time triggers a **RED "ENTRY REJECTED: ALREADY SCANNED"** warning with the previous scan timestamp.

4. **Pandas Analytics & One-Click Reports:**
   - Visit `/admin/dashboard` to view the live Turnout Rate, No-Show Rate, and Hourly check-in histogram.
   - Click **Export PDF** or **Export Excel** to download the formatted Present and Absent attendance lists.

---

## 8. Default Credentials for Viva Review
- **Admin Username:** `admin`
- **Admin Password:** `admin123`

# EventQR — Viva Voce Preparation & Technical Defense Guide

**Candidate:** Hardik Gupta (25MCA00PY0031)  
**Degree:** MCA — 2nd Year, 3rd Semester  
**Guide & HOD:** Dr. Suresh Joseph, Professor and Head  
**Institution:** Department of Computer Science, School of Engineering & Technology, Pondicherry University  

---

## Part 1: Architecture & Technical Questions

### Q1: Why did you use Python's `secrets` module instead of a sequential ID or simple random number for the QR code?
> **Answer:**  
> A sequential guest ID (e.g. `guest_id=101`) or standard `random.randint()` is predictable. If we encoded sequential IDs into the QR code, an attacker could forge tickets by guessing other attendees' IDs.  
> Python's `secrets` module generates cryptographically secure, pseudo-random numbers using the operating system's CSPRNG (Cryptographically Secure Pseudo-Random Number Generator). We generate 32-character hexadecimal tokens ($2^{128}$ possible combinations), making brute-force forging mathematically impossible.

---

### Q2: Why are the Present and Absent lists computed through SQL Joins rather than a static `status` column in the guests table?
> **Answer:**  
> Storing a static `status='Present'` column creates data anomalies, race conditions, and lack of auditability.  
> By separating registrations into `guests` and gate scans into `entry_logs`, we adhere to **database normalization**:
> 1. **Present List:** An `INNER JOIN` between `guests` and `entry_logs` guarantees that an attendee is only marked present if a physical gate entry event was recorded with timestamp, gate number, and scanner identity.
> 2. **Absent List:** A `LEFT JOIN ... WHERE entry_logs.id IS NULL` gives the true list of registered attendees who have not crossed any gate.
> 3. **Single Source of Truth:** Duplicate entries are prevented at the database schema level via a `UNIQUE` constraint on `entry_logs.guest_id`.

---

### Q3: How does your AI ID Card OCR verification pipeline work?
> **Answer:**  
> The OCR pipeline consists of three stages:
> 1. **Image Preprocessing with OpenCV:** The raw uploaded ID card photo is converted to grayscale, denoised with a Gaussian blur, and enhanced using adaptive contrast adjustment and Otsu thresholding to maximize character contrast against varying backgrounds.
> 2. **Optical Character Recognition & Pattern Extraction:** OCR extracts raw text lines, and a regular expression parser isolates the Roll Number pattern (e.g., `25MCA00PY0031`), Name, and Department.
> 3. **Eligibility Cross-Referencing:** The extracted Roll Number and Department are cross-referenced in real-time against the `eligible_students` master reference table. If the student does not belong to the Computer Science department or is marked ineligible, the system automatically rejects registration before any ticket can be issued.

---

### Q4: How is duplicate ticket entry prevented during high-traffic gate entry?
> **Answer:**  
> Double gate scanning is prevented in two tiers:
> 1. **Application Level:** When a token is decoded by `scanner.py` or the web scanner, `database.record_entry()` first executes a query to check if an entry log exists for that `guest_id`. If found, it immediately responds with `ALREADY_USED` and the exact prior check-in timestamp.
> 2. **Database Engine Level:** The `entry_logs` table enforces a `UNIQUE` constraint on `guest_id`. Even if two scanners scanned the exact same QR code simultaneously, the database transaction enforces that only one record can ever be committed, while the second throws an integrity constraint violation.

---

### Q5: How did you implement automated email delivery without exposing private passwords?
> **Answer:**  
> Direct password login is blocked by modern SMTP providers like Google. We used Python's `smtplib` and `email.mime` modules configured with TLS over port 587 using an **App-Specific Password** stored in environment variables (`.env`).  
> The system builds a multipart MIME email with inline HTML formatting and attaches the rendered PNG event pass. If SMTP credentials are not configured, the system gracefully operates in Simulation Mode, logging the message and saving a rendered digital receipt in `static/email_receipts/` so examiners can review the exact email output directly.

---

### Q6: How is Pandas utilized in your Analytics Dashboard?
> **Answer:**  
> Rather than simple database counters, Pandas handles advanced analytics:
> 1. **Hourly Check-in Distribution:** Pandas converts the `scan_time` timestamps into datetime objects, buckets them into hourly time slots using `.dt.strftime("%I:00 %p")`, and performs `.groupby().size()` to compute the peak arrival curve.
> 2. **Department Turnout Breakdown:** Pandas un-stacks registration and attendance cross-tabulations to plot comparative stacked bar charts.
> 3. **No-Show Rate Computation:** $\text{No-Show Rate} = \left(\frac{\text{Absent Count}}{\text{Total Registered}}\right) \times 100$.

---

### Q7: How are the PDF and Excel reports generated?
> **Answer:**  
> - **PDF Generation:** Built using **ReportLab** (`SimpleDocTemplate`, `Table`, `TableStyle`). It dynamically builds formatted university-branded attendance documents with auto-wrapping table cells, custom headers, and summary counts without saving temporary files to disk (using an in-memory `io.BytesIO` buffer).  
> - **Excel Generation:** Built using **Pandas** and **openpyxl**. It generates multi-sheet workbooks with separate tabs for "All Guests", "Present List", and "Absent List" with automated column sizing.

---

## Part 2: Live Viva Demo Script

When Dr. Joseph or the review committee asks for a demonstration, follow this smooth 4-step sequence:

| Step | Action | What to Explain to Examiners |
|---|---|---|
| **1** | Open `http://127.0.0.1:5000/register` | *"First, let's demonstrate the AI OCR verification. I'll click Karthik N (Mechanical Engineering). The system runs OpenCV preprocessing, extracts the roll number, checks the eligibility master table, and immediately flags that Mechanical students are ineligible."* |
| **2** | Select an eligible CS student & submit | *"Now selecting an eligible CS student, the details are auto-filled. When we submit, Python's `secrets` module generates an unguessable 32-character token, produces the digital badge pass, and dispatches the email."* |
| **3** | Open Gate Scanner at `/admin/scanner` | *"Now at the gate, we scan the QR pass. First attempt turns GREEN with ACCESS GRANTED. If someone tries to re-enter or passes the same QR code to a friend, the scanner immediately turns RED: ENTRY REJECTED: ALREADY USED at [timestamp]."* |
| **4** | Open `/admin/dashboard` & download PDF | *"Finally, in the Organizer Dashboard, Pandas aggregates live turnout, no-show rate, and hourly arrival trends. With one click, we can export the official university Present Attendance List as a clean PDF report."* |

-- =====================================================================
-- EventQR - Multi-Event & Multi-Role Database Schema
-- Student: Hardik Gupta (25MCA00PY0031) | Guide: Dr. S. Joseph
-- Pondicherry University - Department of Computer Science
-- =====================================================================

CREATE DATABASE IF NOT EXISTS eventqr_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eventqr_db;

-- 1. Users Table (Students, Organizers, Admins)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    roll_no VARCHAR(50) UNIQUE,
    phone VARCHAR(25) DEFAULT '',
    department VARCHAR(100) DEFAULT 'Computer Science',
    role VARCHAR(20) DEFAULT 'student', -- 'student', 'organizer', 'admin'
    is_verified BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_roll (roll_no)
) ENGINE=InnoDB;

-- 2. Email OTP Table (Registration & Password Reset Verification)
CREATE TABLE IF NOT EXISTS email_otps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    purpose VARCHAR(30) NOT NULL, -- 'registration', 'password_reset'
    expires_at DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_otp_lookup (email, otp_code, purpose)
) ENGINE=InnoDB;

-- 3. Events Table (Customizable & Multiple Events)
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department_restriction VARCHAR(100) DEFAULT 'All Departments',
    event_date DATE NOT NULL,
    event_time VARCHAR(50) DEFAULT '10:00 AM',
    venue VARCHAR(255) NOT NULL,
    capacity INT NOT NULL DEFAULT 50,
    organizer_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_event_status (status)
) ENGINE=InnoDB;

-- 4. Registrations Table (Capacity, Waitlist & Cryptographic QR Token)
CREATE TABLE IF NOT EXISTS registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    user_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed', -- 'confirmed', 'waitlisted', 'cancelled'
    waitlist_position INT DEFAULT 0,
    qr_token VARCHAR(64) UNIQUE,
    qr_image_path VARCHAR(255),
    registration_method VARCHAR(30) DEFAULT 'Profile', -- 'Profile', 'Manual', 'OCR Verified'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_event_user (event_id, user_id),
    INDEX idx_reg_token (qr_token)
) ENGINE=InnoDB;

-- 5. Entry Logs Table (Gate Attendance & Single-Scan Verification)
CREATE TABLE IF NOT EXISTS entry_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registration_id INT NOT NULL UNIQUE, -- Prevents duplicate scans at DB level
    event_id INT NOT NULL,
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gate_number VARCHAR(50) DEFAULT 'Main Gate 1',
    scanned_by VARCHAR(100) DEFAULT 'Gate Scanner',
    status VARCHAR(50) DEFAULT 'ALLOWED',
    notes VARCHAR(255) DEFAULT 'Checked in',
    FOREIGN KEY (registration_id) REFERENCES registrations(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Eligible Students Table (Department Eligibility Reference Table)
CREATE TABLE IF NOT EXISTS eligible_students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    course VARCHAR(50) DEFAULT 'MCA',
    semester VARCHAR(20) DEFAULT '3rd Semester',
    email VARCHAR(150),
    is_eligible BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

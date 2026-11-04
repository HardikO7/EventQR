import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration parameters"""
    SECRET_KEY = os.getenv("SECRET_KEY", "eventpass-campus-production-secure-key-2026")
    
    # Database Configuration (MySQL default with automatic SQLite fallback)
    DB_TYPE = os.getenv("DB_TYPE", "auto") # 'mysql', 'sqlite', or 'auto'
    MYSQL_HOST = os.getenv("DB_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("DB_PORT", 3306))
    MYSQL_USER = os.getenv("DB_USER", "root")
    MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "")
    MYSQL_DB = os.getenv("DB_NAME", "eventqr_db")
    
    SQLITE_PATH = BASE_DIR / "eventqr.db"

    # Static Folders
    STATIC_DIR = BASE_DIR / "static"
    QR_DIR = STATIC_DIR / "qr_codes"
    UPLOAD_DIR = STATIC_DIR / "uploads"
    SAMPLE_ID_DIR = STATIC_DIR / "sample_id_cards"
    RECEIPT_DIR = STATIC_DIR / "email_receipts"
    
    # Mail Service Configuration (Gmail SMTP or Simulation Mode)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "") # Gmail App Password
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "eventqr.pu@gmail.com")
    MAIL_SIMULATION_MODE = os.getenv("MAIL_SIMULATION_MODE", "true").lower() in ("true", "1")

    # OCR Settings
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    
    # Eligible Department filter (can be configured)
    ELIGIBLE_DEPARTMENT = os.getenv("ELIGIBLE_DEPARTMENT", "Computer Science")

    # Event details default
    EVENT_TITLE = "PU TechFest 2026: National Tech Symposium"
    EVENT_DATE = "2026-11-15"
    EVENT_VENUE = "JN Auditorium, Pondicherry University"

# Ensure all needed static folders exist
for d in [Config.QR_DIR, Config.UPLOAD_DIR, Config.SAMPLE_ID_DIR, Config.RECEIPT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

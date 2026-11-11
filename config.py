import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration parameters."""
    IS_VERCEL = bool(os.getenv("VERCEL"))
    SECRET_KEY = os.getenv("SECRET_KEY", "eventpass-campus-production-secure-key-2026")

    # MySQL Database Configuration (Local MySQL or Cloud TiDB Serverless)
    MYSQL_HOST = os.getenv("DB_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("DB_PORT", 3306))
    MYSQL_USER = os.getenv("DB_USER", "root")
    MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "")
    MYSQL_DB = os.getenv("DB_NAME", "eventqr_db")
    MYSQL_SSL = os.getenv("DB_SSL", "auto").lower()  # 'auto', 'true', or 'false'

    # Static Folders (writable locally; Vercel deployment filesystem is read-only)
    STATIC_DIR = BASE_DIR / "static"
    QR_DIR = STATIC_DIR / "qr_codes"
    RECEIPT_DIR = STATIC_DIR / "email_receipts"

    # Mail Service Configuration (Gmail SMTP or Simulation Mode)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "eventqr.pu@gmail.com")
    MAIL_SIMULATION_MODE = os.getenv("MAIL_SIMULATION_MODE", "true").lower() in ("true", "1")


if not Config.IS_VERCEL:
    for folder in (Config.QR_DIR, Config.RECEIPT_DIR):
        folder.mkdir(parents=True, exist_ok=True)

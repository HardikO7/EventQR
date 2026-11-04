import secrets
from datetime import datetime, timedelta
from config import Config
import database

def generate_numeric_otp(length=6):
    """Generate cryptographically secure 6-digit numeric OTP"""
    return "".join(secrets.choice("0123456789") for _ in range(length))

def create_and_send_otp(email, purpose="registration", user_name="Student"):
    """
    Generate 6-digit OTP, store in database with 5-minute expiration for login (15 min for reg),
    and dispatch via email service.
    """
    # Invalidate previous unused OTPs for this email and purpose
    database.execute_query("""
        UPDATE email_otps SET is_used = 1 
        WHERE email = %s AND purpose = %s AND is_used = 0
    """, (email.strip().lower(), purpose))

    otp_code = generate_numeric_otp(6)
    
    # 5 minute TTL for real-time login and pass lookup OTP, 15 minutes for registration/reset
    ttl_minutes = 5 if purpose in ("login", "ticket_lookup") else 15
    expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
    expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")

    database.execute_query("""
        INSERT INTO email_otps (email, otp_code, purpose, expires_at, is_used)
        VALUES (%s, %s, %s, %s, 0)
    """, (email.strip().lower(), otp_code, purpose, expires_str))

    # Send OTP email
    if purpose == "login":
        subject = f"🔐 Your Login Verification Code: {otp_code} — EventQR"
        action_msg = "Your one-time login verification code is:"
        banner_title = "EventQR Instant Login"
    elif purpose == "ticket_lookup":
        subject = f"🎟️ Admission Pass Verification Code: {otp_code} — EventQR"
        action_msg = "A request was made to retrieve your event admission pass. To protect your ticket privacy, enter the verification code below:"
        banner_title = "EventQR Pass Privacy Verification"
    else:
        subject = f"🔐 Your Verification Code: {otp_code} — EventQR"
        action_msg = "Your one-time verification code is:"
        banner_title = "EventQR Authentication"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #202122; background: #f8f9fa; padding: 25px;">
        <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #c8ccd1; border-radius: 4px; padding: 25px;">
            <div style="border-bottom: 1px solid #a2a9b1; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin: 0; font-family: Georgia, serif; font-weight: normal; color: #000000;">{banner_title}</h2>
                <div style="font-size: 12px; color: #54595d;">Pondicherry University Event Entry Management</div>
            </div>
            
            <p>Hello <strong>{user_name}</strong>,</p>
            <p>{action_msg}</p>
            
            <div style="text-align: center; margin: 25px 0;">
                <div style="display: inline-block; font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #202122; background: #eaecf0; border: 1px solid #a2a9b1; padding: 10px 24px; border-radius: 4px; font-family: monospace;">
                    {otp_code}
                </div>
            </div>
            
            <p style="font-size: 13px; color: #54595d;">This single-use code is valid for <strong>{ttl_minutes} minutes</strong>. If you did not make this request, someone may be attempting to access your ticket details.</p>
            <hr style="border: 0; border-top: 1px solid #eaecf0; margin: 20px 0;">
            <p style="font-size: 11px; color: #72777d; margin: 0;">Department of Computer Science &bull; Pondicherry University</p>
        </div>
    </body>
    </html>
    """

    # Dispatch via email service
    import email_service
    email_service.send_raw_email(email.strip().lower(), subject, html_content)

    return otp_code

def verify_otp(email, otp_code, purpose="registration"):
    """
    Validate OTP against database with timing-safe comparison and replay protection.
    """
    import hmac
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = database.fetch_one("""
        SELECT * FROM email_otps 
        WHERE email = %s AND purpose = %s AND is_used = 0 AND expires_at >= %s
        ORDER BY created_at DESC LIMIT 1
    """, (email.strip().lower(), purpose, now_str))

    if not record:
        return False, "Verification code has expired or was already used. Please request a new code."

    # Timing-attack safe comparison
    if not hmac.compare_digest(record["otp_code"].strip(), otp_code.strip()):
        return False, "Invalid verification code. Please check your email and try again."

    # Mark OTP as used (single use guarantee)
    database.execute_query("UPDATE email_otps SET is_used = 1 WHERE id = %s", (record["id"],))
    return True, "Verification successful."

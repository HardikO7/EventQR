import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from datetime import datetime
from pathlib import Path
from config import Config

def send_raw_email(to_email, subject, html_content, attachments=None):
    """
    Generic email dispatcher using smtplib or development simulation mode.
    Saves an HTML receipt in static/email_receipts for offline review and testing.
    """
    can_send_smtp = bool(Config.MAIL_USERNAME and Config.MAIL_PASSWORD and not Config.MAIL_SIMULATION_MODE)
    sent_successfully = False
    error_message = None

    if can_send_smtp:
        try:
            msg = MIMEMultipart("related")
            msg["Subject"] = Header(subject, "utf-8")
            from_addr = (Config.MAIL_DEFAULT_SENDER or Config.MAIL_USERNAME).strip()
            sender_label = Header("EventPass Pondicherry University", "utf-8").encode()
            msg["From"] = f"{sender_label} <{from_addr}>"
            msg["To"] = to_email

            part = MIMEText(html_content, "html", "utf-8")
            msg.attach(part)

            if attachments:
                for att_path in attachments:
                    att_path = Path(att_path)
                    if att_path.exists():
                        with open(att_path, "rb") as f:
                            img_part = MIMEImage(f.read(), name=att_path.name)
                            img_part.add_header("Content-Disposition", "attachment", filename=att_path.name)
                            # Also add Content-ID for inline referencing
                            cid_name = att_path.stem
                            img_part.add_header("Content-ID", f"<{cid_name}>")
                            msg.attach(img_part)

            clean_pwd = Config.MAIL_PASSWORD.replace(" ", "").strip()
            server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=15)
            if Config.MAIL_USE_TLS:
                server.starttls()
            server.login(Config.MAIL_USERNAME.strip(), clean_pwd)
            server.send_message(msg)
            server.quit()
            sent_successfully = True
            try:
                safe_subj = subject.encode("ascii", "replace").decode("ascii")
                print(f"[SMTP SUCCESS] Dispatched live email to {to_email} | Subject: {safe_subj}")
            except Exception:
                pass
        except Exception as e:
            error_message = str(e)
            sent_successfully = False
            try:
                print(f"[SMTP ERROR] Could not dispatch to {to_email}: {error_message}")
            except Exception:
                pass

    # Save receipt in static/email_receipts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    receipt_filename = f"email_{timestamp}.html"
    receipt_file = Config.RECEIPT_DIR / receipt_filename
    with open(receipt_file, "w", encoding="utf-8") as f:
        meta_header = f"""
        <!--
        SENT_AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        TO: {to_email}
        SUBJECT: {subject}
        STATUS: {'Delivered via Gmail SMTP' if sent_successfully else 'Delivered via Simulation Engine'}
        -->
        """
        f.write(meta_header + html_content)

    return {
        "success": sent_successfully or Config.MAIL_SIMULATION_MODE,
        "mode": "Live SMTP" if sent_successfully else "Simulated SMTP",
        "receipt": receipt_filename,
        "error": error_message
    }

def send_ticket_email(guest_name, to_email, roll_no, department, token, qr_image_path, event_title):
    """Deliver confirmed admission ticket pass with attached QR badge"""
    subject = f"🎟️ Event Pass Confirmed: {event_title}"
    ticket_file_path = Config.STATIC_DIR / qr_image_path

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #202122; background: #f8f9fa; padding: 25px;">
        <div style="max-width: 550px; margin: 0 auto; background: #ffffff; border: 1px solid #c8ccd1; border-radius: 4px; padding: 25px;">
            <div style="border-bottom: 1px solid #a2a9b1; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin: 0; font-family: Georgia, serif; font-weight: normal; color: #000000;">Event Admission Confirmed</h2>
                <div style="font-size: 12px; color: #54595d;">Pondicherry University &bull; EventQR System</div>
            </div>

            <p>Dear <strong>{guest_name}</strong>,</p>
            <p>Your registration for <strong>{event_title}</strong> has been successfully confirmed!</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px;">
                <tr style="border-bottom: 1px solid #eaecf0;">
                    <td style="padding: 8px 0; color: #54595d;">Student Name:</td>
                    <td style="padding: 8px 0; font-weight: bold;">{guest_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eaecf0;">
                    <td style="padding: 8px 0; color: #54595d;">Roll Number:</td>
                    <td style="padding: 8px 0; font-family: monospace;">{roll_no}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eaecf0;">
                    <td style="padding: 8px 0; color: #54595d;">Department:</td>
                    <td style="padding: 8px 0;">{department}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #54595d;">Status:</td>
                    <td style="padding: 8px 0; color: #16a34a; font-weight: bold;">Confirmed (Single Gate Entry)</td>
                </tr>
            </table>

            <div style="background: #f8f9fa; border: 1px dashed #a2a9b1; padding: 15px; text-align: center; border-radius: 4px; margin: 20px 0;">
                <div style="font-weight: bold; margin-bottom: 5px;">Your Entry Pass is Attached</div>
                <div style="font-size: 12px; color: #54595d;">Show the QR pass on your phone screen at the venue gate for check-in.</div>
                <div style="font-family: monospace; font-size: 11px; margin-top: 8px; color: #72777d;">Token: {token}</div>
            </div>

            <p style="font-size: 12px; color: #54595d;">Important: This ticket pass is strictly personal and single-use. Duplicate scan attempts at the gate will be automatically rejected.</p>
        </div>
    </body>
    </html>
    """

    attachments = [ticket_file_path] if ticket_file_path.exists() else []
    return send_raw_email(to_email, subject, html_content, attachments=attachments)

def send_waitlist_email(guest_name, to_email, event_title, waitlist_pos):
    """Notify student that they are queued on the event waitlist"""
    subject = f"⏳ Waitlist Notice (Position #{waitlist_pos}): {event_title}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #202122; background: #f8f9fa; padding: 25px;">
        <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #c8ccd1; border-radius: 4px; padding: 25px;">
            <div style="border-bottom: 1px solid #a2a9b1; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin: 0; font-family: Georgia, serif; font-weight: normal; color: #000000;">Event Capacity Filled — Waitlist</h2>
                <div style="font-size: 12px; color: #54595d;">Pondicherry University Event Entry Management</div>
            </div>

            <p>Dear <strong>{guest_name}</strong>,</p>
            <p>You have registered for <strong>{event_title}</strong>. Because the maximum capacity for this event has currently been reached, you have been placed on the official waitlist at:</p>

            <div style="text-align: center; margin: 25px 0;">
                <div style="display: inline-block; font-size: 28px; font-weight: bold; color: #b25900; background: #fef6ed; border: 1px solid #f6d199; padding: 10px 24px; border-radius: 4px;">
                    Waitlist Queue #{waitlist_pos}
                </div>
            </div>

            <p style="font-size: 13px; color: #54595d;">If a confirmed attendee cancels their registration or the event organizer expands seat capacity, you will be automatically promoted to Confirmed status and your QR ticket will be issued immediately.</p>
        </div>
    </body>
    </html>
    """
    return send_raw_email(to_email, subject, html_content)

def send_waitlist_promotion_email(guest_name, to_email, event_title, token, qr_image_path):
    """Notify student that they have been promoted from the waitlist to confirmed!"""
    subject = f"🎉 Seat Confirmed! Promoted from Waitlist: {event_title}"
    return send_ticket_email(guest_name, to_email, "Student", "University", token, qr_image_path, event_title)

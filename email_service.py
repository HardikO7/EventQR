import smtplib
import threading
from datetime import datetime
from pathlib import Path
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config


def _wrap_email_html(heading, subtitle, body_html, width=540):
    """Wrap email body content in consistent Pondicherry University styling."""
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #202122; background: #f8f9fa; padding: 25px;">
        <div style="max-width: {width}px; margin: 0 auto; background: #ffffff; border: 1px solid #c8ccd1; border-radius: 4px; padding: 25px;">
            <div style="border-bottom: 1px solid #a2a9b1; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin: 0; font-family: Georgia, serif; font-weight: normal; color: #000000;">{heading}</h2>
                <div style="font-size: 12px; color: #54595d;">{subtitle}</div>
            </div>
            {body_html}
        </div>
    </body>
    </html>
    """


def send_email_async(to_email, subject, html_content, attachments=None, attachment_bytes=None):
    """
    Dispatch email via background thread locally, or synchronously on Vercel serverless
    so OTP delivery completes before the serverless execution environment freezes.
    """
    if Config.IS_VERCEL:
        send_raw_email(to_email, subject, html_content, attachments=attachments, attachment_bytes=attachment_bytes)
        return
    thread = threading.Thread(
        target=send_raw_email,
        args=(to_email, subject, html_content, attachments, attachment_bytes),
        daemon=True,
    )
    thread.start()


def send_raw_email(to_email, subject, html_content, attachments=None, attachment_bytes=None):
    """Send email over SMTP and save receipt locally when writable."""
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
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            for att in (attachments or []):
                att_path = Path(att)
                if att_path.exists():
                    _attach_png(msg, att_path.read_bytes(), att_path.name)

            for fname, raw_bytes in (attachment_bytes or []):
                if raw_bytes:
                    _attach_png(msg, raw_bytes, fname)

            clean_pwd = Config.MAIL_PASSWORD.replace(" ", "").strip()
            if Config.MAIL_PORT == 465:
                server = smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=15)
            else:
                server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=15)
                if Config.MAIL_USE_TLS:
                    server.starttls()

            server.login(Config.MAIL_USERNAME.strip(), clean_pwd)
            server.send_message(msg)
            server.quit()
            sent_successfully = True
        except Exception as e:
            error_message = str(e)
            print(f"[SMTP ERROR] Could not dispatch to {to_email}: {error_message}")

    receipt_filename = None
    if not Config.IS_VERCEL:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        receipt_filename = f"email_{timestamp}.html"
        receipt_file = Config.RECEIPT_DIR / receipt_filename
        meta_header = (
            f"<!-- SENT_AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"TO: {to_email} | STATUS: {'SMTP' if sent_successfully else 'Simulated'} -->\n"
        )
        receipt_file.write_text(meta_header + html_content, encoding="utf-8")

    return {
        "success": sent_successfully or Config.MAIL_SIMULATION_MODE,
        "mode": "Live SMTP" if sent_successfully else "Simulated SMTP",
        "receipt": receipt_filename,
        "error": error_message,
    }


def _attach_png(msg, raw_bytes, filename):
    img_part = MIMEImage(raw_bytes, name=filename)
    img_part.add_header("Content-Disposition", "attachment", filename=filename)
    img_part.add_header("Content-ID", f"<{Path(filename).stem}>")
    msg.attach(img_part)


def send_ticket_email(guest_name, to_email, roll_no, department, token, qr_image_path, event_title, badge_bytes=None):
    """Send confirmed admission pass with attached QR badge."""
    subject = f"Event Pass Confirmed: {event_title}"
    body = f"""
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
    """
    html_content = _wrap_email_html("Event Admission Confirmed", "Pondicherry University &bull; EventQR System", body)

    att_bytes = [(f"pass_{token}.png", badge_bytes)] if badge_bytes else None
    attachments = None
    if not att_bytes and qr_image_path:
        ticket_file_path = Config.STATIC_DIR / qr_image_path
        if ticket_file_path.exists():
            attachments = [ticket_file_path]

    send_email_async(to_email, subject, html_content, attachments=attachments, attachment_bytes=att_bytes)
    return {"success": True, "mode": "Sync on Vercel" if Config.IS_VERCEL else "Async Queued", "error": None}


def send_waitlist_email(guest_name, to_email, event_title, waitlist_pos):
    """Notify attendee that they were queued on the event waitlist."""
    subject = f"Waitlist Notice (Position #{waitlist_pos}): {event_title}"
    body = f"""
        <p>Dear <strong>{guest_name}</strong>,</p>
        <p>You have registered for <strong>{event_title}</strong>. Because current seat capacity is full, you have been placed on the waitlist at:</p>
        <div style="text-align: center; margin: 25px 0;">
            <div style="display: inline-block; font-size: 28px; font-weight: bold; color: #b25900; background: #fef6ed; border: 1px solid #f6d199; padding: 10px 24px; border-radius: 4px;">
                Waitlist Queue #{waitlist_pos}
            </div>
        </div>
        <p style="font-size: 13px; color: #54595d;">If a confirmed attendee cancels or capacity increases, you will be automatically promoted and emailed your QR ticket.</p>
    """
    html_content = _wrap_email_html("Event Capacity Filled - Waitlist", "Pondicherry University Event Entry Management", body, width=520)
    send_email_async(to_email, subject, html_content)
    return {"success": True, "mode": "Sync on Vercel" if Config.IS_VERCEL else "Async Queued", "error": None}

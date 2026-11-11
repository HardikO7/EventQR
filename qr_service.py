import io
import secrets
import qrcode
from PIL import Image, ImageDraw, ImageFont
from config import Config


def generate_secure_token():
    """Generate a cryptographically random 32-character hex token."""
    return secrets.token_hex(16)


def render_pass_badge_bytes(token, guest_name, roll_no, department, event_title="PU TechFest 2026"):
    """Render branded QR admission pass PNG cleanly in memory and return raw PNG bytes."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(token)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGBA")

    width, height = 700, 360
    badge = Image.new("RGBA", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(badge)

    draw.rectangle([(0, 0), (width, 85)], fill="#1E3A8A")
    draw.rectangle([(0, 85), (width, 90)], fill="#3B82F6")
    draw.rectangle([(0, 90), (12, height)], fill="#1E3A8A")

    try:
        font_header = ImageFont.truetype("arial.ttf", 26)
        font_sub = ImageFont.truetype("arial.ttf", 14)
        font_label = ImageFont.truetype("arial.ttf", 12)
        font_value = ImageFont.truetype("arialbd.ttf", 16)
        font_token = ImageFont.truetype("consola.ttf", 11)
    except Exception:
        font_header = font_sub = font_label = font_value = font_token = ImageFont.load_default()

    draw.text((25, 18), "PONDICHERRY UNIVERSITY", fill="#E0E7FF", font=font_sub)
    draw.text((25, 42), event_title, fill="#FFFFFF", font=font_header)

    details = [
        ("ATTENDEE NAME", guest_name.upper()),
        ("ROLL NUMBER", (roll_no or "STUDENT").upper()),
        ("DEPARTMENT", department or "Computer Science"),
        ("ENTRY STATUS", "VALID TICKET (SINGLE ENTRY)"),
    ]

    y_offset = 110
    for label, val in details:
        draw.text((35, y_offset), label, fill="#64748B", font=font_label)
        draw.text((35, y_offset + 16), val, fill="#0F172A", font=font_value)
        y_offset += 48

    qr_resized = qr_img.resize((190, 190), Image.Resampling.LANCZOS)
    qr_x, qr_y = 475, 110
    draw.rounded_rectangle([(qr_x - 10, qr_y - 10), (qr_x + 200, qr_y + 200)], radius=8, outline="#CBD5E1", width=2)
    badge.paste(qr_resized, (qr_x, qr_y), qr_resized)

    short_token = f"SECURITY TOKEN: {token[:8]}...{token[-8:]}"
    draw.text((qr_x - 8, qr_y + 206), short_token, fill="#475569", font=font_token)

    draw.rectangle([(0, height - 25), (width, height)], fill="#F1F5F9")
    draw.text((25, height - 20), "Present this QR code at the entrance scanner for automatic gate validation.", fill="#64748B", font=font_token)

    buf = io.BytesIO()
    badge.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_ticket(token, guest_name, roll_no, department, event_title="PU TechFest 2026"):
    """Build pass PNG bytes (saving to static/qr_codes locally; pure in-memory on Vercel)."""
    badge_bytes = render_pass_badge_bytes(token, guest_name, roll_no, department, event_title)
    pass_filename = f"pass_{token}.png"
    if not Config.IS_VERCEL:
        pass_file_path = Config.QR_DIR / pass_filename
        pass_file_path.write_bytes(badge_bytes)
    return f"qr_codes/{pass_filename}", badge_bytes

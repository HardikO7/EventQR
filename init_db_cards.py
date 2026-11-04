from PIL import Image, ImageDraw, ImageFont
from config import Config

def create_sample_cards():
    samples = [
        ("Rohan Sen", "25CS101", "Computer Science", "MCA 3rd Semester", "sample_rohan_id.png"),
        ("Kavya Nair", "25CS102", "Computer Science", "MCA 3rd Semester", "sample_kavya_id.png"),
        ("Aditya Sharma", "25CS103", "Computer Science", "MCA 3rd Semester", "sample_aditya_id.png"),
        ("Meera Krishnan", "25CS104", "Computer Science", "M.Sc Computer Science", "sample_meera_id.png"),
        ("Varun Pillai", "25ME201", "Mechanical Engineering", "M.Tech Mechanical", "sample_varun_mech_id.png"),
    ]

    for name, roll, dept, crs, fname in samples:
        path = Config.SAMPLE_ID_DIR / fname
        create_card(path, name, roll, dept, crs)

def create_card(output_path, name, roll_no, department, course):
    w, h = 650, 400
    card = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(card)

    is_cs = "computer" in department.lower()
    header_color = "#1E3A8A" if is_cs else "#881337"
    draw.rectangle([(0, 0), (w, 80)], fill=header_color)
    draw.rectangle([(0, 80), (w, 86)], fill="#F59E0B")

    try:
        f_uni = ImageFont.truetype("arialbd.ttf", 20)
        f_dept = ImageFont.truetype("arial.ttf", 13)
        f_lbl = ImageFont.truetype("arial.ttf", 12)
        f_val = ImageFont.truetype("arialbd.ttf", 15)
        f_roll = ImageFont.truetype("consola.ttf", 16)
    except Exception:
        f_uni = ImageFont.load_default()
        f_dept = ImageFont.load_default()
        f_lbl = ImageFont.load_default()
        f_val = ImageFont.load_default()
        f_roll = ImageFont.load_default()

    draw.text((25, 16), "CENTRAL UNIVERSITY", fill="#FFFFFF", font=f_uni)
    draw.text((25, 45), f"DEPARTMENT OF {department.upper()}", fill="#E2E8F0", font=f_dept)

    photo_x, photo_y = 35, 115
    photo_w, photo_h = 135, 175
    draw.rectangle([(photo_x, photo_y), (photo_x + photo_w, photo_y + photo_h)], fill="#E2E8F0", outline="#94A3B8", width=2)
    draw.text((photo_x + 20, photo_y + 70), "STUDENT", fill="#64748B", font=f_lbl)
    draw.text((photo_x + 25, photo_y + 90), "PHOTO", fill="#64748B", font=f_lbl)

    info_x = 200
    fields = [
        ("STUDENT NAME", name),
        ("ROLL / REG NUMBER", roll_no),
        ("DEPARTMENT", department),
        ("COURSE & SEMESTER", course),
        ("VALIDITY", "2024 - 2026")
    ]

    curr_y = 108
    for lbl, val in fields:
        draw.text((info_x, curr_y), lbl, fill="#64748B", font=f_lbl)
        if "ROLL" in lbl:
            draw.text((info_x, curr_y + 15), val, fill="#1E3A8A", font=f_roll)
        else:
            draw.text((info_x, curr_y + 15), val, fill="#0F172A", font=f_val)
        curr_y += 48

    bar_x = 35
    bar_y = 330
    draw.rectangle([(0, 315), (w, h)], fill="#F8FAFC")
    draw.line([(0, 315), (w, 315)], fill="#E2E8F0", width=1)
    for i in range(0, 320, 5):
        line_w = 2 if (i % 3 == 0) else 1
        draw.line([(bar_x + i, bar_y), (bar_x + i, bar_y + 35)], fill="#1E293B", width=line_w)

    draw.text((390, bar_y + 8), f"ID: {roll_no}", fill="#475569", font=f_roll)
    draw.text((390, bar_y + 26), "OFFICIAL STUDENT IDENTITY CARD", fill="#94A3B8", font=f_lbl)
    draw.rectangle([(0, 0), (w - 1, h - 1)], outline="#CBD5E1", width=2)
    card.save(output_path, "PNG")

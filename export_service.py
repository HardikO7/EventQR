import io
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import database

def generate_pdf_report(report_type, event_id):
    """Generate official PDF attendance report using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#202122"),
        alignment=1
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#54595d"),
        alignment=1
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#54595d")
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#202122")
    )
    cell_head_style = ParagraphStyle(
        'CellHeadText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    event = database.get_event_by_id(event_id) or {"title": "University Event", "venue": "Campus"}

    if report_type == "present":
        report_title = "OFFICIAL PRESENT ATTENDANCE REPORT"
        records = database.get_event_present_list(event_id)
    elif report_type == "absent":
        report_title = "ABSENT REGISTERED STUDENTS REPORT"
        records = database.get_event_absent_list(event_id)
    else:
        report_title = "COMPLETE EVENT ATTENDEE ROSTER"
        records = database.get_event_attendees(event_id)

    # University Header
    elements.append(Paragraph("PONDICHERRY UNIVERSITY", sub_style))
    elements.append(Paragraph("EVENT ACCESS & ATTENDANCE MANAGEMENT SYSTEM", sub_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(event.get("title", ""), title_style))
    elements.append(Paragraph(f"{report_title} &bull; {event.get('event_date', '')} at {event.get('venue', '')}", sub_style))
    elements.append(Spacer(1, 10))

    # Meta
    gen_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    capacity_stats = database.get_event_capacity_stats(event_id) or {}
    meta_text = f"<b>Generated:</b> {gen_time} &nbsp;|&nbsp; <b>Capacity:</b> {capacity_stats.get('capacity', 0)} &nbsp;|&nbsp; <b>Confirmed:</b> {capacity_stats.get('confirmed', 0)} &nbsp;|&nbsp; <b>Waitlisted:</b> {capacity_stats.get('waitlisted', 0)}"
    elements.append(Paragraph(meta_text, meta_style))
    elements.append(Spacer(1, 12))

    # Build Table
    table_data = []

    if report_type == "present":
        headers = ["#", "Roll Number", "Student Name", "Department", "Gate Check-in Time", "Gate / Staff"]
        table_data.append([Paragraph(h, cell_head_style) for h in headers])
        for idx, r in enumerate(records, start=1):
            scan_time_str = str(r.get("scan_time", "-"))[:19]
            table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(r.get("student_roll", "-")), cell_style),
                Paragraph(str(r.get("student_name", "")), cell_style),
                Paragraph(str(r.get("student_dept", "")), cell_style),
                Paragraph(scan_time_str, cell_style),
                Paragraph(str(r.get("gate_number", "Gate 1")), cell_style),
            ])
        col_widths = [25, 95, 130, 110, 100, 70]

    elif report_type == "absent":
        headers = ["#", "Roll Number", "Student Name", "Department", "Email ID", "Status"]
        table_data.append([Paragraph(h, cell_head_style) for h in headers])
        for idx, r in enumerate(records, start=1):
            table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(r.get("student_roll", "-")), cell_style),
                Paragraph(str(r.get("student_name", "")), cell_style),
                Paragraph(str(r.get("student_dept", "")), cell_style),
                Paragraph(str(r.get("student_email", "")), cell_style),
                Paragraph("ABSENT", cell_style),
            ])
        col_widths = [25, 95, 135, 115, 110, 50]

    else:
        headers = ["#", "Roll Number", "Student Name", "Department", "Status", "Gate Scan Time"]
        table_data.append([Paragraph(h, cell_head_style) for h in headers])
        for idx, r in enumerate(records, start=1):
            scan_str = str(r.get("scan_time", "-"))[:19] if r.get("attendance_status") == "Present" else (r.get("status", "").capitalize())
            table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(r.get("student_roll", "-")), cell_style),
                Paragraph(str(r.get("student_name", "")), cell_style),
                Paragraph(str(r.get("student_dept", "")), cell_style),
                Paragraph(str(r.get("attendance_status", r.get("status", "").capitalize())), cell_style),
                Paragraph(scan_str, cell_style),
            ])
        col_widths = [25, 95, 135, 115, 65, 95]

    if len(table_data) == 1:
        table_data.append([Paragraph("No records found.", cell_style)] + [Paragraph("", cell_style)] * (len(headers) - 1))

    report_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#202122")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#C8CCD1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
    ]))

    elements.append(report_table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_excel_report(report_type, event_id):
    """Generate Excel spreadsheet for an event using Pandas and openpyxl"""
    buffer = io.BytesIO()
    
    if report_type == "full":
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            all_roster = database.get_event_attendees(event_id)
            present = database.get_event_present_list(event_id)
            absent = database.get_event_absent_list(event_id)

            df_all = pd.DataFrame(all_roster)
            df_present = pd.DataFrame(present)
            df_absent = pd.DataFrame(absent)

            for df, sheet in [(df_all, 'All Attendees'), (df_present, 'Present List'), (df_absent, 'Absent List')]:
                if not df.empty:
                    df_clean = df.drop(columns=[c for c in ['qr_image_path', 'notes'] if c in df.columns], errors='ignore')
                    df_clean.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    pd.DataFrame({"Status": ["No records"]}).to_excel(writer, sheet_name=sheet, index=False)
    else:
        records = database.get_event_present_list(event_id) if report_type == "present" else database.get_event_absent_list(event_id)
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.drop(columns=[c for c in ['qr_image_path', 'notes'] if c in df.columns], errors='ignore')
        else:
            df = pd.DataFrame({"Status": ["No records found"]})

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=report_type.capitalize(), index=False)

    buffer.seek(0)
    return buffer

import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import database


def generate_pdf_report(report_type, event_id):
    """Generate official PDF attendance report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.HexColor("#202122"), alignment=1)
    sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=13, textColor=colors.HexColor("#54595d"), alignment=1)
    meta_style = ParagraphStyle('DocMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor("#54595d"))
    cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor("#202122"))
    cell_head_style = ParagraphStyle('CellHeadText', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)

    event = database.get_event_by_id(event_id) or {"title": "University Event", "venue": "Campus"}
    if report_type == "present":
        report_title, records = "OFFICIAL PRESENT ATTENDANCE REPORT", database.get_event_present_list(event_id)
    elif report_type == "absent":
        report_title, records = "ABSENT REGISTERED STUDENTS REPORT", database.get_event_absent_list(event_id)
    else:
        report_title, records = "COMPLETE EVENT ATTENDEE ROSTER", database.get_event_attendees(event_id)

    capacity_stats = database.get_event_capacity_stats(event_id) or {}
    gen_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")

    elements = [
        Paragraph("PONDICHERRY UNIVERSITY", sub_style),
        Paragraph("EVENT ACCESS & ATTENDANCE MANAGEMENT SYSTEM", sub_style),
        Spacer(1, 4),
        Paragraph(event.get("title", ""), title_style),
        Paragraph(f"{report_title} &bull; {event.get('event_date', '')} at {event.get('venue', '')}", sub_style),
        Spacer(1, 10),
        Paragraph(
            f"<b>Generated:</b> {gen_time} &nbsp;|&nbsp; <b>Capacity:</b> {capacity_stats.get('capacity', 0)} "
            f"&nbsp;|&nbsp; <b>Confirmed:</b> {capacity_stats.get('confirmed', 0)} "
            f"&nbsp;|&nbsp; <b>Waitlisted:</b> {capacity_stats.get('waitlisted', 0)}",
            meta_style,
        ),
        Spacer(1, 12),
    ]

    table_data = []
    if report_type == "present":
        headers = ["#", "Roll Number", "Student Name", "Department", "Gate Check-in Time", "Gate / Staff"]
        table_data.append([Paragraph(h, cell_head_style) for h in headers])
        for idx, r in enumerate(records, start=1):
            table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(r.get("student_roll") or "-"), cell_style),
                Paragraph(str(r.get("student_name", "")), cell_style),
                Paragraph(str(r.get("student_dept", "")), cell_style),
                Paragraph(str(r.get("scan_time", "-"))[:19], cell_style),
                Paragraph(str(r.get("gate_number", "Gate 1")), cell_style),
            ])
        col_widths = [25, 95, 130, 110, 100, 70]
    elif report_type == "absent":
        headers = ["#", "Roll Number", "Student Name", "Department", "Email ID", "Status"]
        table_data.append([Paragraph(h, cell_head_style) for h in headers])
        for idx, r in enumerate(records, start=1):
            table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(r.get("student_roll") or "-"), cell_style),
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
            scan_str = str(r.get("scan_time", "-"))[:19] if r.get("attendance_status") == "Present" else r.get("status", "").capitalize()
            table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(r.get("student_roll") or "-"), cell_style),
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


def _write_sheet(ws, records):
    """Write a list of record dictionaries into an openpyxl worksheet."""
    if not records:
        ws.append(["Status"])
        ws.append(["No records found"])
        return

    skip_cols = {"qr_image_path", "notes"}
    cols = [c for c in records[0].keys() if c not in skip_cols]
    ws.append(cols)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in records:
        ws.append([row.get(c, "") for c in cols])


def generate_excel_report(report_type, event_id):
    """Generate Excel spreadsheet using lightweight native openpyxl."""
    wb = Workbook()
    if report_type == "full":
        ws = wb.active
        ws.title = "All Attendees"
        _write_sheet(ws, database.get_event_attendees(event_id))
        _write_sheet(wb.create_sheet("Present List"), database.get_event_present_list(event_id))
        _write_sheet(wb.create_sheet("Absent List"), database.get_event_absent_list(event_id))
    else:
        ws = wb.active
        ws.title = report_type.capitalize()
        records = database.get_event_present_list(event_id) if report_type == "present" else database.get_event_absent_list(event_id)
        _write_sheet(ws, records)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
